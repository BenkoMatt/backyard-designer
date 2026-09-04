"""Contour OFF-vs-ON pixel diff at 2 viewports, then restore state. Ribbon colors = real."""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
def dig(pg):
    pg.evaluate("""() => {
      const T = window._test;
      T.ensureTerrainArray();
      for (let iz = 60; iz <= 100; iz++) for (let ix = 70; ix <= 110; ix++) {
        const dx = (ix-85)/25, dz = (iz-80)/20;
        const d = Math.sqrt(dx*dx+dz*dz);
        if (d < 1) T.state.terrain[iz*201+ix] = -15*(1-d)*(1-d);
      }
      T.applyTerrainToMesh();
      T._debouncedApplyTerrainFull();
    }""")
    pg.wait_for_timeout(3000)
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    for W,H,tag in [(1280,800,"c1280f"),(1024,768,"c1024f")]:
        pg = b.new_context(viewport={"width":W,"height":H}).new_page()
        pg.set_default_timeout(20000)
        pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
        pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(900)
        pg.evaluate("() => document.getElementById('wp-scratch')?.click()"); pg.wait_for_timeout(900)
        pg.evaluate("() => window.setMode('advanced')"); pg.wait_for_timeout(500)
        dig(pg)
        # open dock, toggle OFF state first
        pg.evaluate("() => { const t = document.querySelector(\".td-tab[data-dock='analyze']\"); if (t) t.click(); }")
        pg.wait_for_timeout(600)
        pg.evaluate("() => document.getElementById('toast')?.classList.remove('visible')")
        pg.evaluate("() => document.querySelector(\".td-tab[data-dock='analyze']\")?.click()")  # close dock first
        pg.wait_for_timeout(500)
        pg.evaluate("() => window.Atmosphere.update(12.0, 45)")
        pg.wait_for_timeout(800)
        pg.screenshot(path=f"{OUT}/{tag}_off.png")
        # reopen dock, toggle ON, close dock
        pg.evaluate("() => document.querySelector(\".td-tab[data-dock='analyze']\")?.click()")
        pg.wait_for_timeout(500)
        pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()")
        pg.wait_for_timeout(1200)
        pg.evaluate("() => document.getElementById('toast')?.classList.remove('visible')")
        pg.evaluate("() => document.querySelector(\".td-tab[data-dock='analyze']\")?.click()")  # close dock
        pg.wait_for_timeout(500)
        pg.evaluate("() => window.Atmosphere.update(12.0, 45)")
        pg.wait_for_timeout(900)
        pg.screenshot(path=OUT + f"/{tag}_on.png")
        from PIL import Image
        a = Image.open(OUT + f"/{tag}_off.png").convert('RGB')
        c = Image.open(OUT + f"/{tag}_on.png").convert('RGB')
        pa, pc = a.load(), c.load()
        locs = [(x,y) for y in range(52,H) for x in range(280,W) if pa[x,y] != pc[x,y]]
        xs=[l[0] for l in locs]; ys=[l[1] for l in locs]
        print(f"{tag}: diff px {len(locs)}", f"bbox [{min(xs)},{max(xs)},{min(ys)},{max(ys)}]" if locs else "none")
        pg.close()
    b.close()
print("DONE")
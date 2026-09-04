"""Final contour verification: dig, toggle contours, CLOSE dock, screenshot, count ribbon pixels."""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    pg = b.new_context(viewport={"width":1280,"height":800}).new_page()
    pg.set_default_timeout(20000)
    pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
    pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(900)
    pg.evaluate("() => document.getElementById('wp-scratch')?.click()"); pg.wait_for_timeout(900)
    pg.evaluate("() => window.setMode('advanced')"); pg.wait_for_timeout(500)
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
    pg.wait_for_timeout(3500)
    pg.evaluate("() => { const t = document.querySelector(\".td-tab[data-dock='analyze']\"); if (t) t.click(); }")
    pg.wait_for_timeout(700)
    toast = pg.evaluate("() => { document.getElementById('ta-contour-toggle')?.click(); return document.getElementById('toast').textContent; }")
    pg.wait_for_timeout(1200)
    # CLOSE the dock so the pit is visible
    pg.evaluate("() => { const t = document.querySelector(\".td-tab[data-dock='analyze']\"); if (t) t.click(); }")
    pg.wait_for_timeout(700)
    pg.evaluate("() => document.getElementById('toast')?.classList.remove('visible')")
    pg.evaluate("() => window.Atmosphere.update(12.0, 45)")
    pg.wait_for_timeout(1000)
    pg.screenshot(path=OUT + "/final_on.png")
    from PIL import Image
    img = Image.open(OUT + "/final_on.png").convert('RGB')
    px = img.load()
    red = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>200 and px[x,y][1]<80 and px[x,y][2]<80)
    print("toast:", toast, "| red px:", red)
    if red > 150:
        locs=[(x,y) for y in range(52,800) for x in range(280,1280) if px[x,y][0]>200 and px[x,y][1]<80 and px[x,y][2]<80]
        xs=[l[0] for l in locs]; ys=[l[1] for l in locs]
        print("red bbox x", min(xs), max(xs), "y", min(ys), max(ys))
    b.close()
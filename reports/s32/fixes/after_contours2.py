"""Contour ribbon AFTER-verify: pixel-diff OFF vs ON at 2 viewports + vision."""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    for (w,h,tag) in [(1280,800,"c1280b"),(1024,768,"c1024b")]:
        pg = b.new_context(viewport={"width":w,"height":h}).new_page()
        pg.set_default_timeout(15000)
        pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
        pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(700)
        pg.evaluate("() => document.getElementById('wp-scratch')?.click()"); pg.wait_for_timeout(600)
        pg.evaluate("() => window.setMode('advanced')"); pg.wait_for_timeout(400)
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
        pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(400)
        pg.evaluate("() => { document.getElementById('ta-contour-interval').value='0.5'; document.getElementById('ta-contour-interval').dispatchEvent(new Event('change')); }")
        pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(400)
        pg.evaluate("() => document.getElementById('toast').classList.remove('visible')")
        pg.evaluate("() => window.Atmosphere.update(12.01, 45)")
        pg.wait_for_timeout(600)
        pg.screenshot(path=f"{OUT}/{tag}_off.png")
        pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(300)
        toast = pg.evaluate("() => { document.getElementById('ta-contour-toggle')?.click(); return document.getElementById('toast').textContent; }")
        pg.wait_for_timeout(1200)
        pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(400)
        pg.evaluate("() => document.getElementById('toast').classList.remove('visible')")
        pg.evaluate("() => window.Atmosphere.update(12.015, 44.9)")
        pg.wait_for_timeout(700)
        pg.screenshot(path=f"{OUT}/{tag}_on.png")
        from PIL import Image
        a = Image.open(f"{OUT}/{tag}_off.png").convert('RGB')
        c = Image.open(f"{OUT}/{tag}_on.png").convert('RGB')
        pa, pc = a.load(), c.load()
        # count only terrain-area diffs (skip toast band y<80)
        diff = 0; locs=[]
        for y in range(85, h):
            for x in range(280, w):
                if pa[x,y] != pc[x,y]:
                    diff += 1; locs.append((x,y))
        box = [0,0,0,0]
        if locs:
            xs=[l[0] for l in locs]; ys=[l[1] for l in locs]
            box=[min(xs),max(xs),min(ys),max(ys)]
        print(tag, 'toast:', toast[:40], 'terrain diff px:', diff, 'bbox:', box)
        json.dump({"toast": toast, "diff": diff, "bbox": box}, open(f"{OUT}/{tag}_diff.json","w"))
        if diff > 100:
            pad=25
            c.crop((max(280,box[0]-pad), max(85,box[2]-pad), min(w,box[1]+pad), min(h,box[3]+pad))).save(f"{OUT}/{tag}_crop.png")
    b.close()
print('DONE')

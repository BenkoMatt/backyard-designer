"""S32-P0 contour definitive check: same-session pixel-diff contour OFF vs ON (no other changes)."""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    for (w,h,tag) in [(1280,800,"c1280"),(1024,768,"c1024")]:
        pg = b.new_context(viewport={"width":w,"height":h}).new_page()
        pg.set_default_timeout(15000)
        pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
        pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(500)
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
        }""")
        pg.wait_for_timeout(2200)
        pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(400)
        pg.evaluate("() => { document.getElementById('ta-contour-interval').value='0.5'; document.getElementById('ta-contour-interval').dispatchEvent(new Event('change')); }")
        pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(400)
        pg.screenshot(path=f"{OUT}/{tag}_off.png")
        pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(300)
        pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()"); pg.wait_for_timeout(1200)
        pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(500)
        pg.screenshot(path=f"{OUT}/{tag}_on.png")
        from PIL import Image
        a = Image.open(f"{OUT}/{tag}_off.png").convert('RGB')
        c = Image.open(f"{OUT}/{tag}_on.png").convert('RGB')
        pa, pc = a.load(), c.load()
        diff = 0
        locs = []
        for y in range(52, h):
            for x in range(280, w):
                if pa[x,y] != pc[x,y]:
                    diff += 1
                    locs.append((x,y))
        dbox = [0,0,0,0]
        if locs:
            xs=[l[0] for l in locs]; ys=[l[1] for l in locs]
            dbox = [min(xs),max(xs),min(ys),max(ys)]
        print(tag, 'diff px:', diff, 'bbox:', dbox)
        json.dump({"diff": diff, "bbox": dbox}, open(f"{OUT}/{tag}_contourdiff.json","w"))
        if diff > 50:
            pad = 20
            c.crop((max(280,dbox[0]-pad), max(52,dbox[2]-pad), min(w,dbox[1]+pad), min(h,dbox[3]+pad))).save(f"{OUT}/{tag}_contourcrop.png")
    b.close()
print('DONE')
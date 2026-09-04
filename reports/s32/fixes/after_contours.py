"""S32-P0 contour AFTER-verify: contour lines must now rasterize on dug terrain (panel closed + open), 2 viewports."""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
res = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    for (w,h,tag) in [(1280,800,"after_contours_1280"),(1024,768,"after_contours_1024")]:
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
        pg.wait_for_timeout(2000)
        pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(400)
        pg.evaluate("() => { document.getElementById('ta-contour-interval').value='0.5'; document.getElementById('ta-contour-interval').dispatchEvent(new Event('change')); }")
        pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()"); pg.wait_for_timeout(1200)
        toast = pg.evaluate("() => document.getElementById('toast')?.textContent || ''")
        obj = pg.evaluate("""() => {
          let n = 0, verts = 0;
          window.scene.traverse(o => { if (o.userData && o.userData.isContourOverlay) { n++; verts += o.geometry.attributes.position.count; } });
          return { overlays: n, verts };
        }""")
        pg.screenshot(path=f"{OUT}/{tag}.png")
        # close panel for clean shot of terrain
        pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(500)
        pg.screenshot(path=f"{OUT}/{tag}_panelclosed.png")
        from PIL import Image
        img = Image.open(f"{OUT}/{tag}_panelclosed.png").convert('RGB')
        px = img.load()
        h1 = sum(1 for y in range(52,800) for x in range(280,w) if abs(px[x,y][0]-64)<9 and abs(px[x,y][1]-52)<9 and abs(px[x,y][2]-20)<10)
        h2 = sum(1 for y in range(52,800) for x in range(280,w) if abs(px[x,y][0]-38)<9 and abs(px[x,y][1]-26)<9 and abs(px[x,y][2]-13)<9)
        res[tag] = {"toast": toast, "objects": obj, "px_normal_0x403414": h1, "px_index_0x261a0d": h2}
        print(tag, json.dumps(res[tag]))
        # flat-terrain honest toast check on fresh page
        pg2 = b.new_context(viewport={"width":w,"height":h}).new_page()
        pg2.set_default_timeout(15000)
        pg2.goto(BASE, wait_until="load", timeout=60000); pg2.wait_for_timeout(2000)
        pg2.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg2.wait_for_timeout(400)
        pg2.evaluate("() => window.setMode('advanced')"); pg2.wait_for_timeout(300)
        pg2.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg2.wait_for_timeout(300)
        pg2.evaluate("() => document.getElementById('ta-contour-toggle')?.click()"); pg2.wait_for_timeout(900)
        toast2 = pg2.evaluate("() => document.getElementById('toast')?.textContent || ''")
        res[tag]["flat_toast"] = toast2
        print('flat terrain toast:', toast2)
    json.dump(res, open(f"{OUT}/after_contours.json","w"), indent=1)
    b.close()
print('DONE')
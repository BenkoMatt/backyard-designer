"""Test-only: recolor contour overlays to pure red at runtime — does the geometry rasterize at all?"""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    pg = b.new_context(viewport={"width":1280,"height":800}).new_page()
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
    }""")
    pg.wait_for_timeout(2200)
    pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(400)
    pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()"); pg.wait_for_timeout(1200)
    pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(400)
    n = pg.evaluate("""() => {
      let n = 0;
      window.scene.traverse(o => { if (o.userData && o.userData.isContourOverlay) { o.material.color.setHex(0xff0000); o.material.depthTest = false; n++; } });
      return n;
    }""")
    pg.wait_for_timeout(600)
    pg.screenshot(path=f"{OUT}/diag_contour_red.png")
    from PIL import Image
    img = Image.open(f"{OUT}/diag_contour_red.png").convert('RGB')
    px = img.load()
    red = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>180 and px[x,y][1]<90 and px[x,y][2]<90)
    print('overlays recolored:', n, 'RED px visible:', red)
    b.close()
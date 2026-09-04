"""Contour test with the analyze dock panel CLOSED (panels occlude yard center per audit C)."""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    pg = b.new_context(viewport={"width":1280,"height":800}).new_page()
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
    state = pg.evaluate("() => ({ contourEnabled: window._test.contourEnabled })")
    pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(500)
    closed = pg.evaluate("() => ({ panelVisible: !!document.querySelector('.dock-panel-container.visible') })")
    pg.screenshot(path=f"{OUT}/before_contours_panelclosed.png")
    from PIL import Image
    img = Image.open(f"{OUT}/before_contours_panelclosed.png").convert('RGB')
    px = img.load()
    hits = 0; samples=[]
    for y in range(52, 800):
        for x in range(280, 1280):
            r,g,b2 = px[x,y]
            is_idx = abs(r-38)<20 and abs(g-26)<18 and abs(b2-13)<16
            is_norm = abs(r-64)<20 and abs(g-46)<18 and abs(b2-20)<16
            if is_idx or is_norm:
                hits += 1
                if len(samples)<10: samples.append((x,y,(r,g,b2)))
    print('state:', state, 'panelClosed:', closed)
    print('contour-color px:', hits, 'samples:', samples)
    b.close()
"""Combined debug: after_contours2 sequence verbatim; inspect scene before ON shot."""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
errs=[]
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    pg = b.new_context(viewport={"width":1280,"height":800}).new_page()
    pg.set_default_timeout(15000)
    pg.on("pageerror", lambda e: errs.append("PAGEERR: "+str(e)))
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
    pg.evaluate("() => document.querySelector(\".td-tab[data-dock='analyze']\")?.click()"); pg.wait_for_timeout(400)
    pg.evaluate("() => { document.getElementById('ta-contour-interval').value='0.5'; document.getElementById('ta-contour-interval').dispatchEvent(new Event('change')); }")
    pg.evaluate("() => document.querySelector(\".td-tab[data-dock='analyze']\")?.click()"); pg.wait_for_timeout(400)
    pg.evaluate("() => document.getElementById('toast').classList.remove('visible')")
    pg.evaluate("() => window.Atmosphere.update(12.01, 45)")
    pg.wait_for_timeout(600)
    pg.evaluate("() => document.querySelector(\".td-tab[data-dock='analyze']\")?.click()"); pg.wait_for_timeout(300)
    toast = pg.evaluate("() => { document.getElementById('ta-contour-toggle')?.click(); return document.getElementById('toast').textContent; }")
    pg.wait_for_timeout(1200)
    st1 = pg.evaluate("""() => {
      const n = [];
      window.scene.traverse(o => { if (o.userData && o.userData.isContourOverlay) n.push({type:o.type, verts:o.geometry.attributes.position.count}); });
      return { overlays: n, enabled: window._test.contourEnabled, dockVisible: !!document.querySelector('.dock-panel-container.visible') };
    }""")
    pg.evaluate("() => document.querySelector(\".td-tab[data-dock='analyze']\")?.click()"); pg.wait_for_timeout(400)
    pg.evaluate("() => document.getElementById('toast').classList.remove('visible')")
    pg.evaluate("() => window.Atmosphere.update(12.015, 44.9)")
    pg.wait_for_timeout(700)
    st2 = pg.evaluate("""() => {
      const n = [];
      window.scene.traverse(o => { if (o.userData && o.userData.isContourOverlay) n.push({type:o.type, verts:o.geometry.attributes.position.count}); });
      return { overlays: n, enabled: window._test.contourEnabled, dockVisible: !!document.querySelector('.dock-panel-container.visible') };
    }""")
    print("toast:", toast)
    print("before close-dock:", json.dumps(st1))
    print("after close-dock (ON shot state):", json.dumps(st2))
    print("errors:", errs[:3])
    b.close()

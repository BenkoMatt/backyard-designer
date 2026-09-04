"""Live audit of contour overlay objects AFTER all settles."""
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
      T._debouncedApplyTerrainFull();
    }""")
    pg.wait_for_timeout(3500)
    pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(400)
    pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()"); pg.wait_for_timeout(1500)
    audit = pg.evaluate("""() => {
      const T = window._test;
      const out = [];
      window.scene.traverse(o => {
        if (o.userData && o.userData.isContourOverlay) {
          const p = o.geometry.attributes.position;
          out.push({ verts: p.count, visible: o.visible, color: o.material.color.getHexString(),
                     depthTest: o.material.depthTest, renderOrder: o.renderOrder });
        }
      });
      return { count: out.length, objs: out, contourEnabled: T.contourEnabled,
               rendererLines: T.renderer.info.render.lines, frame: T.renderer.info.render.frame };
    }""")
    print(json.dumps(audit, indent=1))
    json.dump(audit, open(OUT + "/diag_contour_livaudit.json", "w"), indent=1)
    b.close()

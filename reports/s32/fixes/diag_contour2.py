"""Enumerate ALL line objects in the scene after contour enable."""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
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
    pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(500)
    pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()")
    pg.wait_for_timeout(1500)
    lines = pg.evaluate("""() => {
      const out = [];
      window.scene.traverse(o => {
        if (o.isLineSegments || o.isLine) {
          const p = o.geometry.attributes.position;
          const arr = p.array;
          let yMin = Infinity, yMax = -Infinity, xMin = Infinity, xMax = -Infinity, zMin = Infinity, zMax = -Infinity;
          for (let i = 0; i < p.count; i++) {
            const x = arr[i*3], y = arr[i*3+1], z = arr[i*3+2];
            if (y < yMin) yMin = y; if (y > yMax) yMax = y;
            if (x < xMin) xMin = x; if (x > xMax) xMax = x;
            if (z < zMin) zMin = z; if (z > zMax) zMax = z;
          }
          out.push({ kind: o.isLineSegments ? 'LineSegments' : 'Line', verts: p.count,
                     visible: o.visible, name: o.name || null, renderOrder: o.renderOrder,
                     yMin: +yMin.toFixed(2), yMax: +yMax.toFixed(2),
                     xMin: +xMin.toFixed(1), xMax: +xMax.toFixed(1),
                     zMin: +zMin.toFixed(1), zMax: +zMax.toFixed(1),
                     parentType: o.parent ? o.parent.type : null,
                     vertexColors: !!o.material.vertexColors,
                     color: o.material.color ? o.material.color.getHexString() : null });
        }
      });
      return out;
    }""")
    print(json.dumps(lines, indent=1))
    b.close()
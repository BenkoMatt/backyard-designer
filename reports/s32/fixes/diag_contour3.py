"""Project contour vertices to screen coords and inspect the exact pixels there."""
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
    pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(400)
    pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()"); pg.wait_for_timeout(1500)
    out = pg.evaluate("""() => {
      const T = window._test;
      let c = null;
      window.scene.traverse(o => { if (o.isLineSegments && o.geometry.attributes.position.count === 1936) c = o; });
      if (!c) return { err: 'contour object not found' };
      const cam = T.activeCamera;
      const w = T.renderer.domElement.clientWidth, h = T.renderer.domElement.clientHeight;
      const p = c.geometry.attributes.position;
      const v = null;
      const V = null;
      // use camera math manually
      function project(x, y, z) {
        // vector from camera to point
        const m = c.matrixWorld;
        const wx = m.elements[0]*x + m.elements[4]*y + m.elements[8]*z + m.elements[12];
        const wy = m.elements[1]*x + m.elements[5]*y + m.elements[9]*z + m.elements[13];
        const wz = m.elements[2]*x + m.elements[6]*y + m.elements[10]*z + m.elements[14];
        // camera view matrix
        const e = cam.matrixWorldInverse.elements;
        const vx = e[0]*wx + e[4]*wy + e[8]*wz + e[12];
        const vy = e[1]*wx + e[5]*wy + e[9]*wz + e[13];
        const vz = e[2]*wx + e[6]*wy + e[10]*wz + e[14];
        const p44 = cam.projectionMatrix.elements;
        const cx = p44[0]*vx + p44[8]*vz;
        const cy = p44[5]*vy + p44[9]*vz;
        const cw = -vz; // perspective divide (for standard perspective camera)
        const px = (cx/cw*0.5 + 0.5) * w;
        const py = (-cy/cw*0.5 + 0.5) * h;
        return { x: Math.round(px), y: Math.round(py), vz: +vz.toFixed(2) };
      }
      const pts = [];
      for (let i = 0; i < Math.min(p.count, 3000); i += 97) {
        pts.push(project(p.array[i*3], p.array[i*3+1], p.array[i*3+2]));
      }
      return { count: p.count, camPos: cam.position.toArray(), pts: pts.slice(0, 30),
               renderInfo: T.renderer.info.render, domSize: { w, h },
               canvasRect: T.renderer.domElement.getBoundingClientRect().toJSON() };
    }""")
    print(json.dumps(out, indent=1))
    json.dump(out, open('/root/byd32-fix/reports/s32/fixes/diag_contour_project.json','w'), indent=1)
    b.close()
import base64
"""Read pixels back from the WebGL canvas itself (toDataURL) at projected contour coords."""
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
    pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()"); pg.wait_for_timeout(1400)
    res = pg.evaluate("""() => {
      const T = window._test;
      let c = null;
      window.scene.traverse(o => { if (o.isLineSegments && o.geometry.attributes.position.count === 1936) c = o; });
      const cam = T.activeCamera;
      const rect = T.renderer.domElement.getBoundingClientRect();
      const p = c.geometry.attributes.position;
      function project(x, y, z) {
        const m = c.matrixWorld;
        const wx = m.elements[0]*x + m.elements[4]*y + m.elements[8]*z + m.elements[12];
        const wy = m.elements[1]*x + m.elements[5]*y + m.elements[9]*z + m.elements[13];
        const e = cam.matrixWorldInverse.elements;
        const vx = e[0]*wx + e[4]*wy + e[12];
        const vy = e[1]*wx + e[5]*wy + e[13];
        const vz = e[2]*wx + e[6]*wy + e[14];
        const p44 = cam.projectionMatrix.elements;
        const cx = p44[0]*vx + p44[8]*vz;
        const cy = p44[5]*vy + p44[9]*vz;
        const cw = -vz;
        return { x: Math.round((cx/cw*0.5 + 0.5) * rect.width), y: Math.round((-cy/cw*0.5 + 0.5) * rect.height) };
      }
      const pts = [];
      for (let i = 0; i < p.count; i += 31) { const q = project(p.array[i*3], p.array[i*3+1], p.array[i*3+2]); if (q.x>=0&&q.y>=0) pts.push(q); }
      const url = T.renderer.domElement.toDataURL('image/png');
      return { pts: pts.slice(0, 20), dataLen: url.length, dataURL: url };
    }""")
    open('/tmp/canvas_readback.png','wb').write(base64.b64decode(res['dataURL'].split(',',1)[1])); print('saved canvas readback', res['dataLen'])
    print('pts sample:', res['pts'][:6])
    b.close()

"""Isolate SwiftShader line rasterization: inject a test LineSegments (red, plain + vertexColors)
at y=5 spanning the yard; screenshot; count red pixels."""
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
      let proto = null;
      window.scene.traverse(o => { if (o.isLineSegments && !proto) proto = o; });
      const LS = proto.constructor;
      const GEOM = proto.geometry.constructor;
      const MAT = proto.material.constructor;
      const ATTR = proto.geometry.attributes.position.constructor;
      // red plain-color lines at y=6 above yard center
      const g1 = new GEOM();
      g1.setAttribute('position', new ATTR(new Float32Array([-20,6,-20, 20,6,-20, 20,6,-20, 20,6,20, 20,6,20, -20,6,20, -20,6,20, -20,6,-20]), 3));
      const m1 = new MAT({ color: 0xff0000 });
      const o1 = new LS(g1, m1);
      o1.frustumCulled = false;
      window.__testLine1 = o1; window.scene.add(o1);
      // vertexColors line
      const g2 = new GEOM();
      const cols = new Float32Array(24);
      for (let i = 0; i < 8; i++) { cols[i*3+1] = 1; }
      g2.setAttribute('position', new ATTR(new Float32Array([-20,3,-20, 20,3,-20, 20,3,-20, 20,3,20, 20,3,20, -20,3,20, -20,3,20, -20,3,-20]), 3));
      g2.setAttribute('color', new ATTR(cols, 3));
      const m2 = new MAT({ vertexColors: true, linewidth: 2 });
      const o2 = new LS(g2, m2);
      o2.frustumCulled = false;
      window.__testLine2 = o2; window.scene.add(o2);
    }""")
    pg.wait_for_timeout(900)
    pg.screenshot(path=f"{OUT}/diag_line_raster.png")
    from PIL import Image
    img = Image.open(f"{OUT}/diag_line_raster.png").convert('RGB')
    px = img.load()
    red = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>200 and px[x,y][1]<80 and px[x,y][2]<80)
    green = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][1]>200 and px[x,y][0]<80 and px[x,y][2]<80)
    print('red px (plain material):', red, 'green px (vertexColors material):', green)
    b.close()
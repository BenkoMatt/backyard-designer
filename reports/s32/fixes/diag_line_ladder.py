"""Isolate: clone contour geometry, shift +40x, red, no depth test — does THAT rasterize?"""
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
    results = {}
    for n in (8, 100, 400, 1000):
        info = pg.evaluate("""(n) => {
          let proto = null;
          window.scene.traverse(o => { if (o.isLineSegments && !proto) proto = o; });
          const LS = proto.constructor, GEOM = proto.geometry.constructor, MAT = proto.material.constructor, ATTR = proto.geometry.attributes.position.constructor;
          const segs = [];
          for (let i = 0; i < n; i++) {
            const x0 = -30 + (i % 40) * 1.5, z0 = -30 + Math.floor(i / 40) * 1.5;
            segs.push(x0, 4, z0, x0 + 1, 4, z0);
          }
          const g = new GEOM();
          g.setAttribute('position', new ATTR(new Float32Array(segs), 3));
          const m = new MAT({ color: 0x00ffff });
          const o = new LS(g, m);
          o.frustumCulled = false;
          window['__ladder' + n] = o;
          window.scene.add(o);
          return { added: n };
        }""", n)
    print(json.dumps(results) if results else "ladder added")
    print(json.dumps(info))
    pg.wait_for_timeout(800)
    pg.screenshot(path=OUT + "/diag_contour_clone.png")
    from PIL import Image
    img = Image.open(OUT + "/diag_contour_clone.png").convert('RGB')
    px = img.load()
    cyan = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]<110 and px[x,y][1]>170 and px[x,y][2]>170)
    print('CYAN px total (ladder 8+100+400+1000 segments):', cyan)
    b.close()

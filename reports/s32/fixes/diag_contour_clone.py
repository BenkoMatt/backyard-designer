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
    info = pg.evaluate("""() => {
      let proto = null; let verts = 0;
      window.scene.traverse(o => { if (o.userData && o.userData.isContourOverlay && !proto) { proto = o; verts = o.geometry.attributes.position.count; } });
      if (!proto) return { err: 'none' };
      const LS = proto.constructor, GEOM = proto.geometry.constructor, MAT = proto.material.constructor, ATTR = proto.geometry.attributes.position.constructor;
      const src = proto.geometry.attributes.position.array;
      const arr = new Float32Array(src.length);
      for (let i = 0; i < arr.length; i += 3) { arr[i] = src[i] + 40; arr[i+1] = 5; arr[i+2] = src[i+2]; }
      const g = new GEOM();
      g.setAttribute('position', new ATTR(arr, 3));
      const m = new MAT({ color: 0xff00ff });
      const o = new LS(g, m);
      o.frustumCulled = false;
      window.__clone = o;
      window.scene.add(o);
      return { cloned: true, verts };
    }""")
    print(json.dumps(info))
    pg.wait_for_timeout(800)
    pg.screenshot(path=OUT + "/diag_contour_clone.png")
    from PIL import Image
    img = Image.open(OUT + "/diag_contour_clone.png").convert('RGB')
    px = img.load()
    mag = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>170 and px[x,y][1]<110 and px[x,y][2]>170)
    print('magenta px from cloned contour at x+40, y=5:', mag)
    if mag:
        locs=[(x,y) for y in range(52,800) for x in range(280,1280) if px[x,y][0]>170 and px[x,y][1]<110 and px[x,y][2]>170]
        xs=[l[0] for l in locs]; ys=[l[1] for l in locs]
        print('bbox x', min(xs), max(xs), 'y', min(ys), max(ys))
    b.close()

"""Contours ON (dock open), sun 12 -> 18.5: does ANYTHING change on screen?"""
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
    pg.wait_for_timeout(3000)
    pg.evaluate("() => document.querySelector(\".td-tab[data-dock='analyze']\")?.click()"); pg.wait_for_timeout(400)
    pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()"); pg.wait_for_timeout(1500)
    pg.evaluate("() => document.getElementById('toast').classList.remove('visible')")
    pg.evaluate("() => window.Atmosphere.update(12.0, 45)")
    pg.wait_for_timeout(900)
    pg.screenshot(path=OUT + "/sun12.png")
    pg.screenshot(path=OUT + "/sun185_before.png")
    st = pg.evaluate("""() => {
      let proto = null;
      window.scene.traverse(o => { if (o.userData && o.userData.isContourOverlay && !proto) proto = o; });
      if (!proto) return { err: 'no overlay' };
      const LS = proto.constructor, GEOM = proto.geometry.constructor, MAT = proto.material.constructor, ATTR = proto.geometry.attributes.position.constructor;
      const src2 = proto.geometry.attributes.position.array;
      const arr = new Float32Array(src2.length);
      arr.set(src2);
      for (let i = 1; i < arr.length; i += 3) arr[i] += 0.5;
      const g = new GEOM();
      g.setAttribute('position', new ATTR(arr, 3));
      const m = new MAT({ color: 0x0000ff, depthTest: false, depthWrite: false, side: 2 });
      const o = new LS(g, m);
      o.renderOrder = 1000;
      o.frustumCulled = false;
      window.__copy = o;
      window.scene.add(o);
      return { clonedVerts: arr.length / 3, srcVerts: proto.geometry.attributes.position.count,
               srcType: proto.type, srcVisible: proto.visible,
               srcFlags: { depthTest: proto.material.depthTest, depthWrite: proto.material.depthWrite,
                            transparent: proto.material.transparent, opacity: proto.material.opacity,
                            polygonOffset: proto.material.polygonOffset, renderOrder: proto.renderOrder } };
    }""")
    print('clone:', json.dumps(st))
    pg.wait_for_timeout(1500)
    pg.screenshot(path=OUT + "/sun185.png")
    from PIL import Image
    a = Image.open(OUT + "/sun12.png").convert('RGB')
    c = Image.open(OUT + "/sun185.png").convert('RGB')
    pa, pc = a.load(), c.load()
    diff = sum(1 for y in range(0,800) for x in range(0,1280) if pa[x,y] != pc[x,y])
    print("sun12 vs sun18.5 diff:", diff)
    st = pg.evaluate("""() => ({ frame: window._test.renderer.info.render.frame,
                                  lines: window._test.renderer.info.render.lines,
                                  tris: window._test.renderer.info.render.triangles })""")
    print("renderer:", json.dumps(st))
    b.close()

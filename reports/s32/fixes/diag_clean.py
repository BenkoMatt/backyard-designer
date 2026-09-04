"""CLEAN: scratch + dig + toggle. Toast + red px. (temp-red colors live in app)"""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
errs=[]
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    pg = b.new_context(viewport={"width":1280,"height":800}).new_page()
    pg.set_default_timeout(20000)
    pg.on("pageerror", lambda e: errs.append(str(e)))
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
    pg.wait_for_timeout(1500)
    pg.evaluate("() => document.querySelector(\".td-tab[data-dock='analyze']\")?.click()"); pg.wait_for_timeout(500)
    toast = pg.evaluate("() => { document.getElementById('ta-contour-toggle')?.click(); return document.getElementById('toast').textContent; }")
    pg.wait_for_timeout(1500)
    pg.evaluate("() => document.getElementById('toast').classList.remove('visible')")
    pg.evaluate("() => window.Atmosphere.update(12.0, 45)")
    pg.wait_for_timeout(900)
    pg.screenshot(path=OUT + "/clean_on.png")
    from PIL import Image
    c = Image.open(OUT + "/clean_on.png").convert('RGB')
    px = c.load()
    red = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>170 and px[x,y][1]<100 and px[x,y][2]<100)
    compass = sum(1 for y in range(52,800) for x in range(1180,1280) if px[x,y][0]>170 and px[x,y][1]<100 and px[x,y][2]<100)
    st = pg.evaluate("""() => {
      const n = [];
      window.scene.traverse(o => { if (o.userData && o.userData.isContourOverlay) n.push({type:o.type, verts:o.geometry.attributes.position.count, visible:o.visible}); });
      return { overlays: n, enabled: window._test.contourEnabled };
    }""")
    pg.screenshot(path=OUT + "/clean_before.png")
    pg.evaluate("() => window.scene.traverse(o => { if (o.userData && o.userData.isContourOverlay) { o.material.polygonOffset = false; o.material.polygonOffsetFactor = 0; o.material.needsUpdate = true; } })")
    pg.wait_for_timeout(400)
    pg.screenshot(path=OUT + "/clean_after.png")
    from PIL import Image as I2
    a = I2.open(OUT + "/clean_before.png").convert('RGB')
    c2 = I2.open(OUT + "/clean_after.png").convert('RGB')
    p2a, p2c = a.load(), c2.load()
    d = sum(1 for y in range(52,800) for x in range(280,1280) if p2a[x,y]!=p2c[x,y])
    red2 = sum(1 for y in range(52,800) for x in range(280,1180) if p2c[x,y][0]>170 and p2c[x,y][1]<100 and p2c[x,y][2]<100)
    print("polygonOffset-off diff:", d, "red after:", red2)
    diag = pg.evaluate("""() => {
      let m = null;
      window.scene.traverse(o => { if (o.userData && o.userData.isContourOverlay && !m) m = o; });
      if (!m) return { err: 1 };
      const g = m.geometry, pos = g.attributes.position, col = g.attributes.color;
      let nan = 0, firstBad = -1;
      const pa = pos.array;
      for (let i = 0; i < pa.length; i++) if (Number.isNaN(pa[i])) { nan++; if (firstBad<0) firstBad=i; }
      const ca = col ? col.array : null;
      let colNan = 0;
      if (ca) for (let i = 0; i < ca.length; i++) if (Number.isNaN(ca[i])) colNan++;
      let allZero = true;
      if (ca) for (let i = 0; i < Math.min(30, ca.length); i++) if (ca[i] !== 0) { allZero = false; break; }
      return { posCount: pos.count, colCount: col ? col.count : null,
               posItemSize: pos.itemSize, colItemSize: col ? col.itemSize : null,
               posNan: nan, firstBadIdx: firstBad, colNan, colFirst30AllZero: allZero,
               indexLen: g.index ? g.index.count : null,
               drawRange: JSON.stringify(g.drawRange),
               boundingSphere: g.boundingSphere ? { r: g.boundingSphere.radius, c: g.boundingSphere.center } : null };
    }""")
    print("mesh diag:", json.dumps(diag))
    st2 = pg.evaluate("""() => { const i = window._test.renderer.info.render; return { tris: i.triangles, calls: i.calls, frame: i.frame }; }""")
    overlays = pg.evaluate("""() => {
      const arr = [];
      window.scene.traverse(o => { if (o.renderOrder >= 900 || (o.material && o.material.opacity !== undefined && o.material.transparent)) arr.push({ name: o.type, ro: o.renderOrder, verts: o.geometry.attributes.position ? o.geometry.attributes.position.count : 0, visible: o.visible, op: o.material.opacity, ud: Object.keys(o.userData||{}).join(',') }); });
      return arr;
    }""")
    print("transparent/high-ro objects:", json.dumps(overlays, indent=0))
    pg.evaluate("""() => {
      window.__hidden = [];
      window.scene.traverse(o => { if (o !== window.__contourRef && !o.userData.isContourOverlay) { if (!o.parent || o.parent === window.scene) { window.__hidden.push(o); } } });
      for (const o of window.__hidden) window.scene.remove(o);
    }""")
    pg.evaluate("() => { window.__contourRef = null; window.scene.traverse(o => { if (o.userData.isContourOverlay) window.__contourRef = o; }); }")
    pg.evaluate("""() => {
      window.__hidden2 = [];
      window.scene.traverse(o => { if (o !== window.__contourRef && (o.parent === window.scene)) window.__hidden2.push(o); });
      for (const o of window.__hidden2) window.scene.remove(o);
    }""")
    pg.wait_for_timeout(500)
    pg.screenshot(path=OUT + "/clean_solo.png")
    pg.evaluate("() => { for (const o of window.__hidden2) window.scene.add(o); }")
    pg.wait_for_timeout(300)
    solo2 = pg.evaluate("""() => {
      let n = 0; window.scene.traverse(o => { if (o.parent === window.scene) n++; });
      return { sceneChildren: n, contourPresent: (() => { let f=false; window.scene.traverse(o=>{if(o.userData.isContourOverlay)f=true;}); return f; })() };
    }""")
    print('after restore:', json.dumps(solo2))
    hm = pg.evaluate("""() => {
      let found = null;
      window.scene.traverse(o => { if (o.material && o.material.vertexColors && o.geometry && o.geometry.attributes.position && o.geometry.attributes.position.count > 4000 && !o.userData.isContourOverlay) found = found || { type: o.type, verts: o.geometry.attributes.position.count, ro: o.renderOrder, visible: o.visible, matType: o.material.type, tc: o.material.transparent, op: o.material.opacity }; });
      return found;
    }""")
    print('heatmap-like overlay:', json.dumps(hm))
    tmat = pg.evaluate("""() => { let t = null; window.scene.traverse(o => { if (o.isMesh && o.visible && o.geometry && o.geometry.attributes.position) t = t || { matType: o.material.type, vc: o.material.vertexColors, ro: o.renderOrder, verts: o.geometry.attributes.position.count }; }); return t; }""")
    print('terrain material:', json.dumps(tmat))
    pg.evaluate("() => { for (const o of window.__hidden2) if (o !== window.__contourRef) window.scene.remove(o); }")
    pg.evaluate("() => { const c = window.__contourRef; c.scale.set(10,10,10); c.position.y += 10; c.updateMatrixWorld(true); }")
    pg.wait_for_timeout(600)
    pg.screenshot(path=OUT + "/clean_giant.png")
    pg.evaluate("() => { const c = window.__contourRef; c.scale.set(1,1,1); c.position.y -= 10; }")
    pg.wait_for_timeout(300)
    pg.screenshot(path=OUT + "/clean_novc_before.png")
    pg.evaluate("() => { const c = window.__contourRef; c.material.vertexColors = false; c.material.color = new (c.material.color.constructor)(0xff0000); c.material.needsUpdate = true; }")
    pg.wait_for_timeout(600)
    pg.screenshot(path=OUT + "/clean_novc.png")
    pg.evaluate("() => { const c = window.__contourRef; const M = c.material.constructor; const old = c.material; c.material = new M({ vertexColors: true, side: 2, depthTest: false, transparent: true, opacity: 0.9 }); old.dispose(); }")
    pg.evaluate("() => { const c = window.__contourRef; c.material.vertexColors = true; c.material.needsUpdate = true; }")
    pg.wait_for_timeout(600)
    pg.screenshot(path=OUT + "/clean_clonemat.png")
    bis = pg.evaluate("""() => {
      const c = window.__contourRef;
      const M = c.material.constructor, G = c.geometry.constructor, A = c.geometry.attributes.position.constructor;
      const arr = new Float32Array(c.geometry.attributes.position.array);
      const g2 = new G(); g2.setAttribute('position', new A(arr, 3));
      g2.setAttribute('color', new A(new Float32Array(c.geometry.attributes.color.array), 3));
      const m2 = new M({ vertexColors: true, side: 2, depthTest: false, transparent: true, opacity: 0.9 });
      const mesh2 = new (c.constructor)(g2, m2);
      mesh2.renderOrder = 1001; mesh2.frustumCulled = false;
      window.__bis = mesh2;
      window.scene.add(mesh2);
      return { verts: arr.length / 3 };
    }""")
    print('bisect clone:', json.dumps(bis))
    pg.wait_for_timeout(800)
    pg.screenshot(path=OUT + "/clean_bisect.png")
    pg.evaluate("() => { for (const o of window.__hidden2) window.scene.add(o); }")
    pg.wait_for_timeout(300)
    print("render info:", json.dumps(st2))
    print("toast:", toast)
    print("overlays:", json.dumps(st))
    print("red total:", red, "compass:", compass, "terrain red:", red-compass)
    print("errors:", errs[:3])
    b.close()

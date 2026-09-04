"""Minimal ribbon paint test with explicit requestRender + multiple frames."""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    pg = b.new_context(viewport={"width":1280,"height":800}).new_page()
    pg.set_default_timeout(20000)
    pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
    pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(900)
    pg.evaluate("() => document.getElementById('wp-scratch')?.click()"); pg.wait_for_timeout(900)
    pg.evaluate("() => window.setMode('advanced')"); pg.wait_for_timeout(500)
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
    pg.evaluate("() => { const t = document.querySelector(\".td-tab[data-dock='analyze']\"); if (t) t.click(); }")
    pg.wait_for_timeout(800)
    toast = pg.evaluate("() => { document.getElementById('ta-contour-toggle')?.click(); return document.getElementById('toast').textContent; }")
    pg.wait_for_timeout(1200)
    pg.evaluate("() => document.getElementById('toast').classList.remove('visible')")
    pg.evaluate("() => window.Atmosphere.update(12.0, 45)")
    pg.wait_for_timeout(1000)
    proj = pg.evaluate("""() => {
      let m = null;
      window.scene.traverse(o => { if (o.userData.isContourOverlay && !m) m = o; });
      const cam = window.scene.camera || window.scene.getObjectByProperty('type','PerspectiveCamera') || null;
      let cams = [];
      window.scene.traverse(o => { if (o.type === 'PerspectiveCamera') cams = cams || o; });
      const C = cams || cam;
      if (!m || !C) return { err: 'missing', hasMesh: !!m, hasCam: !!cams };
      const pos = m.geometry.attributes.position;
      m.updateMatrixWorld(true);
      const v = null;
      const out = [];
      const P = m.geometry.attributes.position;
      for (let i = 0; i < Math.min(P.count, 2000); i += 400) {
        out.push([Math.round(P.array[i*3]*10)/10, Math.round(P.array[i*3+1]*10)/10, Math.round(P.array[i*3+2]*10)/10]);
      }
      return { camPos: cams.position ? { x: cams.position.x, y: cams.position.y, z: cams.position.z } : null,
               camType: cams.type,
               meshPos: { x: m.position.x, y: m.position.y, z: m.position.z },
               sampleVerts: out };
    }""")
    print('proj:', json.dumps(proj))
    wsc = pg.evaluate("""() => {
      const T = window._test;
      return { sceneIsWindow: window.scene === T.scene,
               hasRenderer: !!T.renderer, renderCalls: T.renderer ? T.renderer.info.render.calls : null,
               camPos: T.camera ? { x: T.camera.position.x, y: T.camera.position.y, z: T.camera.position.z, type: T.camera.type } : (T.cam ? { x: T.cam.position.x, y: T.cam.position.y, z: T.cam.position.z } : null) };
    }""")
    print('window scene:', json.dumps(wsc))
    cam2 = pg.evaluate("""() => {
      const c = window.activeCamera || null;
      return c ? { type: c.type, pos: { x: Math.round(c.position.x*10)/10, y: Math.round(c.position.y*10)/10, z: Math.round(c.position.z*10)/10 } } : 'no window.activeCamera';
    }""")
    print('activeCamera:', json.dumps(cam2))
    vis = pg.evaluate("""() => {
      let m = null;
      window.scene.traverse(o => { if (o.userData.isContourOverlay && !m) m = o; });
      if (!m) return 'no overlay';
      // is the overlay's world bbox in front of the camera?
      const cam = window.activeCamera;
      const v = m.geometry.boundingSphere ? { center: m.geometry.boundingSphere.center, radius: m.geometry.boundingSphere.radius } : 'no sphere';
      const dist = Math.hypot(m.position.x - cam.position.x, m.position.y - cam.position.y, m.position.z - cam.position.z);
      const near = cam.near, far = cam.far;
      // NDC check of one vertex
      m.updateMatrixWorld(true);
      const P = m.geometry.attributes.position;
      const v0 = { x: P.array[0], y: P.array[1], z: P.array[2] };
      const vec = new (cam.position.constructor === undefined ? Object : Object)();
      return { sphere: v, camDistToMeshOrigin: Math.round(dist), near, far,
               viewDir: { x: Math.round((cam.target ? cam.target.x - cam.position.x : 0)), y: Math.round(cam.target ? cam.target.y - cam.position.y : 0), z: Math.round(cam.target ? cam.target.z - cam.position.z : 0) } };
    }""")
    print('cam/vis:', json.dumps(vis))
    pg.screenshot(path=OUT + "/min_on.png")
    pg.evaluate("() => { const c = window.scene.traverse; let m = null; window.scene.traverse(o => { if (o.userData.isContourOverlay && !m) m = o; }); m.scale.set(100,100,100); window.__reqR = window.requestRender || null; }")
    pg.evaluate("() => window.Atmosphere.update(12.0, 45)")
    pg.wait_for_timeout(900)
    pg.screenshot(path=OUT + "/min_giant.png")
    from PIL import Image
    img = Image.open(OUT + "/min_giant.png").convert('RGB')
    px = img.load()
    red = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>200 and px[x,y][1]<80 and px[x,y][2]<80)
    print("giant red px:", red)
    tmat = pg.evaluate("""() => {
      let yard = null;
      window.scene.traverse(o => { if (o.isMesh && o.geometry && o.geometry.attributes.position && o.geometry.attributes.position.count > 20000) yard = yard || o; });
      if (!yard) return 'no yard mesh';
      return { matType: yard.material.type, params: { vertexColors: yard.material.vertexColors, side: yard.material.side, transparent: yard.material.transparent, opacity: yard.material.opacity, depthTest: yard.material.depthTest, depthWrite: yard.material.depthWrite, polygonOffset: yard.material.polygonOffset, polygonOffsetFactor: yard.material.polygonOffsetFactor, emissive: yard.material.emissive ? yard.material.emissive.getHex() : null } };
    }""")
    print('terrain material:', json.dumps(tmat))
    # swap ribbon material to the terrain's EXACT material instance
    swap = pg.evaluate("""() => {
      let m = null, yard = null;
      window.scene.traverse(o => { if (o.userData.isContourOverlay && !m) m = o; if (o.isMesh && o.geometry && o.geometry.attributes.position && o.geometry.attributes.position.count > 20000 && !yard) yard = o; });
      if (!m || !yard) return 'missing';
      const old = m.material;
      m.material = yard.material;
      old.dispose();
      return 'swapped';
    }""")
    print('swap:', swap)
    pg.evaluate("() => window.Atmosphere.update(12.0, 45)")
    pg.wait_for_timeout(900)
    pg.screenshot(path=OUT + "/min_swapped.png")
    img = Image.open(OUT + "/min_swapped.png").convert('RGB')
    px = img.load()
    red = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>200 and px[x,y][1]<80 and px[x,y][2]<80)
    print('swapped red px:', red)
    addn = pg.evaluate("""() => {
      let m = null, yard = null;
      window.scene.traverse(o => { if (o.userData.isContourOverlay && !m) m = o; if (o.isMesh && o.geometry && o.geometry.attributes.position && o.geometry.attributes.position.count > 20000 && !yard) yard = o; });
      m.geometry.computeVertexNormals();
      return 'normals added: ' + !!m.geometry.attributes.normal;
    }""")
    print(addn)
    pg.evaluate("() => window.Atmosphere.update(12.0, 45)")
    pg.wait_for_timeout(900)
    pg.screenshot(path=OUT + "/min_normals.png")
    img = Image.open(OUT + "/min_normals.png").convert('RGB')
    px = img.load()
    red = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>200 and px[x,y][1]<80 and px[x,y][2]<80)
    print('normals red px:', red)
    pg.evaluate("() => { let m = null; window.scene.traverse(o => { if (o.userData.isContourOverlay && !m) m = o; }); m.scale.set(1,1,1); }")
    pg.evaluate("() => window.Atmosphere.update(12.0, 45)")
    pg.wait_for_timeout(900)
    pg.screenshot(path=OUT + "/min_reset.png")
    img = Image.open(OUT + "/min_reset.png").convert('RGB')
    px = img.load()
    red = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>200 and px[x,y][1]<80 and px[x,y][2]<80)
    print('reset red px:', red)
    force = pg.evaluate("""() => {
      let m = null;
      window.scene.traverse(o => { if (o.userData.isContourOverlay && !m) m = o; });
      const col = m.geometry.attributes.color;
      for (let i = 0; i < col.array.length; i += 3) { col.array[i] = 1; col.array[i+1] = 0; col.array[i+2] = 0; }
      col.needsUpdate = true;
      m.material.depthTest = false; m.material.depthWrite = false; m.material.needsUpdate = true;
      return 'forced red';
    }""")
    pg.evaluate("() => window.Atmosphere.update(12.0, 45)")
    pg.wait_for_timeout(900)
    pg.screenshot(path=OUT + "/min_forced.png")
    img = Image.open(OUT + "/min_forced.png").convert('RGB')
    px = img.load()
    red = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>200 and px[x,y][1]<80 and px[x,y][2]<80)
    print('forced red px:', red)
    box = pg.evaluate("""() => {
      let yard = null;
      window.scene.traverse(o => { if (o.isMesh && o.geometry && o.geometry.attributes.position && o.geometry.attributes.position.count > 20000 && !yard) yard = o; });
      const G = yard.geometry.constructor;
      const g = new G();
      g.setAttribute('position', new (yard.geometry.attributes.position.constructor)(new Float32Array([
        -6, -14.5, -14,  -6, -14.5, -6,  -2, -14.5, -14,
        -2, -14.5, -14,  -6, -14.5, -6,  -2, -14.5, -6 ]), 3));
      const col = new Float32Array(18);
      for (let i = 0; i < 18; i += 3) { col[i] = 1; }
      g.setAttribute('color', new (yard.geometry.attributes.color.constructor)(col, 3));
      const mesh = new (yard.constructor)(g, yard.material);
      mesh.renderOrder = 1003;
      window.__box = mesh;
      window.scene.add(mesh);
      return 'box added';
    }""")
    pg.evaluate("() => window.Atmosphere.update(12.0, 45)")
    pg.wait_for_timeout(900)
    pg.screenshot(path=OUT + "/min_box.png")
    img = Image.open(OUT + "/min_forced.png").convert('RGB')
    img2 = Image.open(OUT + "/min_box.png") if False else None
    im2 = Image.open(OUT + "/min_forced.png")
    import PIL.Image as PI2
    im2 = PI2.open(OUT + "/min_forced.png")  # wrong shot; re-shoot below
    pg.screenshot(path=OUT + "/min_box2.png")
    img = Image.open(OUT + "/min_box2.png").convert('RGB')
    px = img.load()
    red = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>200 and px[x,y][1]<80 and px[x,y][2]<80)
    print('box red px:', red)
    b.close()

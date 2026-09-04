"""Prototype: contour segments as triangle-strip quads (Mesh, vertexColors)."""
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
    pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(400)
    pg.evaluate("() => document.getElementById('toast').classList.remove('visible')")
    pg.evaluate("() => window.Atmosphere.update(12.01, 45)")
    pg.wait_for_timeout(600)
    pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(300)
    pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()"); pg.wait_for_timeout(1500)
    pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()"); pg.wait_for_timeout(400)
    out = pg.evaluate("""() => {
      const audit = [];
      window.scene.traverse(o => { if (o.userData && o.userData.isContourOverlay) audit.push({ type: o.type, verts: o.geometry.attributes.position.count, visible: o.visible, hasColor: !!o.geometry.attributes.color }); });
      let proto = null, meshProto = null;
      window.scene.traverse(o => { if (o.userData && o.userData.isContourOverlay && !proto) proto = o; if (o.isMesh && !meshProto) meshProto = o; });
      const GEOM = proto.geometry.constructor, MESH = meshProto.constructor, ATTR = proto.geometry.attributes.position.constructor;
      const src = proto.geometry.attributes.position.array;
      const positions = [], colors = [];
      const w = 0.22, lift = 0.12;
      for (let i = 0; i < src.length; i += 6) {
        const x0 = src[i], y0 = src[i+1], z0 = src[i+2];
        const x1 = src[i+3], y1 = src[i+4], z1 = src[i+5];
        const dx = x1 - x0, dz = z1 - z0;
        const len = Math.max(1e-6, Math.hypot(dx, dz));
        const nx = -dz / len * w, nz = dx / len * w;
        const y = (y0 + y1) / 2 + lift;
        positions.push(x0-nx, y, z0-nz,  x0+nx, y, z0+nz,  x1-nx, y, z1-nz);
        positions.push(x0+nx, y, z0+nz,  x1+nx, y, z1+nz,  x1-nx, y, z1-nz);
        for (let k = 0; k < 6; k++) colors.push(1, 0, 0);
      }
      const geo = new GEOM();
      geo.setAttribute('position', new ATTR(new Float32Array(positions), 3));
      geo.setAttribute('color', new ATTR(new Float32Array(colors), 3));
      const matProto = meshProto.material.constructor;
      const mat = new matProto({ vertexColors: true, side: 2, depthTest: false, transparent: true, opacity: 0.9 });
      const mesh = new MESH(geo, mat);
      mesh.renderOrder = 998;
      window.__ribbon = mesh;
      window.scene.add(mesh);
      return { audit, quads: positions.length / 18 };
    }""")
    print(json.dumps(out))
    pg.evaluate("() => window.Atmosphere.update(12.01, 45)")
    pg.wait_for_timeout(900)
    print(json.dumps({"audit": out.get("audit") if isinstance(out, dict) else out}, default=str))
    from PIL import Image
    img = Image.open(OUT + "/diag_contour_ribbon.png").convert('RGB')
    px = img.load()
    red = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>170 and px[x,y][1]<100 and px[x,y][2]<100)
    print('RED ribbon px:', red)
    b.close()

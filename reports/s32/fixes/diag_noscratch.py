"""wizard-skip ONLY (no wp-scratch): does the app contour build paint?"""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
errs=[]

def run_sim_march():
    import json as J
    ter = J.load(open('/tmp/terrain_live.json'))
    segs_n = 200; halfW = 25; halfD = 50; cellW = 0.25; cellD = 0.5
    pts = []
    def h(ix, iz):
        v = ter[iz*(segs_n+1)+ix]
        return v if v else 0
    for iz in range(segs_n):
        for ix in range(segs_n):
            h00, h10, h11, h01 = h(ix,iz), h(ix+1,iz), h(ix+1,iz+1), h(ix,iz+1)
            x0, x1 = ix*cellW-halfW, (ix+1)*cellW-halfW
            z0, z1 = iz*cellD-halfD, (iz+1)*cellD-halfD
            def interp(ha, hb, xa, xb, za, zb, level):
                if hb == ha: return None
                t = (level-ha)/(hb-ha)
                if t < 0 or t > 1: return None
                return (xa+t*(xb-xa), level+0.05, za+t*(zb-za))
            for level in (-2.0, -1.0, 0.0):
                e = [interp(h00,h10,x0,x1,z0,z0,level), interp(h10,h11,x1,x1,z0,z1,level), interp(h01,h11,x0,x1,z1,z1,level), interp(h00,h01,x0,x0,z0,z1,level)]
                v = [p for p in e if p is not None]
                if len(v) == 2:
                    pts.extend(v[0]); pts.extend(v[1])
                elif len(v) == 4:
                    pts.extend(v[0]); pts.extend(v[1]); pts.extend(v[2]); pts.extend(v[3])
    return pts

with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    pg = b.new_context(viewport={"width":1280,"height":800}).new_page()
    pg.set_default_timeout(20000)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
    pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(900)
    pg.evaluate("() => window.setMode('advanced')"); pg.wait_for_timeout(400)
    opened = pg.evaluate("""() => { const t = document.querySelector(".td-tab[data-dock='analyze']"); if (t) t.click(); return !!t; }""")
    pg.wait_for_timeout(800)
    print('dock tab present:', opened)
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
    pg.evaluate("() => { const t = document.querySelector(\".td-tab[data-dock='analyze']\"); if (t && !document.getElementById('ta-contour-toggle')?.offsetParent) t.click(); }")
    pg.wait_for_timeout(600)
    vis = pg.evaluate("() => !!document.getElementById('ta-contour-toggle')?.offsetParent")
    print('toggle visible:', vis)
    toast = pg.evaluate("() => { document.getElementById('ta-contour-toggle')?.click(); return document.getElementById('toast').textContent; }")
    pg.wait_for_timeout(1500)
    pg.evaluate("() => document.getElementById('toast').classList.remove('visible')")
    pg.evaluate("() => window.Atmosphere.update(12.01, 45)")
    pg.wait_for_timeout(900)
    dump = pg.evaluate("""() => {
      let m = null;
      window.scene.traverse(o => { if (o.userData.isContourOverlay && !m) m = o; });
      if (!m) return { noOverlay: true, enabled: window._test.contourEnabled };
      const p = m.geometry.attributes.position.array;
      return { floats: Array.from(p.slice(0, 36)).map(v => Math.round(v*100)/100) };
    }""")
    print('dump:', dump)
    print('first 36 floats:', dump)
    mpts = pg.evaluate("""() => {
      const T = window._test;
      const pts = T.marchContourLevel ? T.marchContourLevel(-14.95, 200, 0.25, 0.5, 25, 50) : null;
      return pts ? Array.from(pts.slice(0, 18)).map(v => Math.round(v*100)/100) : 'no seam';
    }""")
    print('march raw:', mpts)
    cdbg = pg.evaluate("() => window.__cdbg")
    print('builder debug:', str(cdbg)[:200])
    import json as J2
    sim_pts = run_sim_march()
    inject = pg.evaluate("""(segs) => {
      let M = null, G = null, A = null;
      window.scene.traverse(o => { if (!M && o.isMesh) { M = o.material.constructor; G = o.geometry.constructor; A = o.geometry.attributes.position.constructor; } });
      const pos = [];
      for (let i = 0; i + 5 < segs.length; i += 6) {
        const ax = segs[i], ay = segs[i+1], az = segs[i+2];
        const bx = segs[i+3], by = segs[i+4], bz = segs[i+5];
        const dx = bx-ax, dz = bz-az;
        const len = Math.max(1e-6, Math.hypot(dx,dz));
        const nx = -dz/len*0.18, nz = dx/len*0.18;
        const y = (ay+by)/2 + 0.3;
        pos.push(ax-nx, y, az-nz, ax+nx, y, az+nz, bx-nx, y, bz-nz);
        pos.push(ax+nx, y, az+nz, bx+nx, y, bz+nz, bx-nx, y, bz-nz);
      }
      const g = new G();
      g.setAttribute('position', new A(new Float32Array(pos), 3));
      const col = new Float32Array(pos.length);
      for (let i = 0; i < col.length; i += 3) { col[i] = 1; }
      g.setAttribute('color', new A(col, 3));
      const mesh = new (window.scene.children.find(c => c.isMesh).constructor)(g, new M({ vertexColors: true, side: 2, depthTest: false, transparent: true, opacity: 0.95 }));
      mesh.renderOrder = 1002; mesh.frustumCulled = false;
      window.__sim = mesh;
      window.scene.add(mesh);
      return { verts: pos.length/3 };
    }""", sim_pts)
    print('injected sim ribbon:', inject)
    pg.wait_for_timeout(800)
    pg.evaluate("() => { window.__others = []; window.scene.children.forEach(c => { if (c !== window.__sim) window.__others.push(c); }); for (const c of window.__others) window.scene.remove(c); }")
    pg.evaluate("() => window.Atmosphere.update(12.01, 45)")
    pg.wait_for_timeout(1200)
    pg.screenshot(path=OUT + "/sim_solo.png")
    pg.evaluate("() => { for (const c of window.__others) window.scene.add(c); }")
    pg.wait_for_timeout(300)
    pg.screenshot(path=OUT + "/sim_ribbon.png")
    pg.screenshot(path=OUT + "/noscratch.png")
    from PIL import Image
    img = Image.open(OUT + "/noscratch.png").convert('RGB')
    px = img.load()
    red = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>170 and px[x,y][1]<100 and px[x,y][2]<100)
    print("toast:", toast, "| noscratch red px:", red)
    print("errors:", errs[:3])
    b.close()

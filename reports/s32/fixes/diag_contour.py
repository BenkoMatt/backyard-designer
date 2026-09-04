"""S32-P0 contour diagnosis: mesh exists — why invisible? Test camera distance, polygonOffset,
depth, and whether lines sit above terrain (level+0.05 with terrain drawn at same heights)."""
import json, time
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    pg = b.new_context(viewport={"width":1280,"height":800}).new_page()
    pg.set_default_timeout(15000)
    pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
    pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(500)
    pg.evaluate("() => window.setMode('advanced')"); pg.wait_for_timeout(400)
    # dig pit via paintTerrain seam (faster, deterministic)
    pg.evaluate("""() => {
      const T = window._test;
      T.ensureTerrainArray();
      for (let iz = 60; iz <= 100; iz++) for (let ix = 70; ix <= 110; ix++) {
        const dx = (ix-85)/25, dz = (iz-80)/20;
        const d = Math.sqrt(dx*dx+dz*dz);
        if (d < 1) T.state.terrain[iz*201+ix] = -15*(1-d)*(1-d);
      }
      T.applyTerrainToMesh();
      T.state.terrainDeformed = true;
    }""")
    pg.wait_for_timeout(2500)
    terr = pg.evaluate("() => { const t = window._test.state.terrain; return {min: Math.min(...t), max: Math.max(...t)}; }")
    # enable contour 0.5ft
    pg.evaluate("""() => {
      document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click();
    }"""); pg.wait_for_timeout(500)
    pg.evaluate("() => { document.getElementById('ta-contour-interval').value = '0.5'; document.getElementById('ta-contour-interval').dispatchEvent(new Event('change')); }")
    pg.wait_for_timeout(200)
    pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()")
    pg.wait_for_timeout(1200)
    diag = pg.evaluate("""() => {
      const out = { overlay: null, camera: null, terrainPos: null, renderInfo: null };
      window.scene.traverse(o => { if (o.isLineSegments && o.geometry.attributes.position.count > 100 && !out.overlay) {
        const p = o.geometry.attributes.position;
        out.overlay = { verts: p.count, visible: o.visible, renderOrder: o.renderOrder,
                        depthTest: o.material.depthTest, polygonOffset: o.material.polygonOffset,
                        polygonOffsetFactor: o.material.polygonOffsetFactor,
                        yMin: Math.min(...Array.from(p.array).filter((_,i)=>i%3===1)),
                        yMax: Math.max(...Array.from(p.array).filter((_,i)=>i%3===1)),
                        parent: o.parent ? (o.parent.type || 'scene') : null };
      }});
      const c = window._test.activeCamera;
      out.camera = { pos: c.position.toArray().map(v=>+v.toFixed(1)), fov: c.fov, near: c.near, far: c.far, type: c.type };
      const ym = window._test.yardMesh;
      out.terrainPos = { count: ym.geometry.attributes.position.count, materialType: ym.material.type };
      out.renderInfo = window._test.renderer.info.render;
      return out;
    }""")
    print("TERRAIN:", json.dumps(terr))
    print("DIAG:", json.dumps(diag, indent=1))
    pg.screenshot(path="/root/byd32-fix/reports/s32/fixes/diag_contour_1.png")
    # count contour-colored pixels (r .15-.25 g .10-.18 b .05-.08 dark brown index/inter lines) — they may anti-alias; scan for dark-brown-ish px on the terrain area
    from PIL import Image
    img = Image.open("/root/byd32-fix/reports/s32/fixes/diag_contour_1.png").convert('RGB')
    px = img.load()
    cnt = 0
    for y in range(56, 780, 2):
        for x in range(284, 1276, 2):
            r,g,bb = px[x,y]
            if 10 <= r <= 70 and 5 <= g <= 50 and 0 <= bb <= 40 and abs(r-g) < 30:
                cnt += 1
    print("dark-brown-ish px (possible contour):", cnt)
    b.close()
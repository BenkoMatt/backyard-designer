"""Deep contour rasterization probe: frustum culling, render call witness, forced render, screenshot."""
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
    pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()"); pg.wait_for_timeout(1200)
    info = pg.evaluate("""() => {
      let c = null;
      window.scene.traverse(o => { if (o.isLineSegments && o.geometry.attributes.position.count === 1936) c = o; });
      if (!c) return { err: 'not found' };
      const T = window._test;
      const r = T.renderer.info.render;
      const bs = c.geometry.boundingSphere;
      return { frustumCulled: c.frustumCulled, boundingSphere: bs ? { center: bs.center.toArray(), radius: +bs.radius.toFixed(1) } : null,
               visible: c.visible, parentVisible: c.parent ? c.parent.visible : null,
               matType: c.material.type, linewidth: c.material.linewidth, transparent: c.material.transparent,
               renderBefore: { ...r } };
    }""")
    print("INFO:", json.dumps(info, indent=1))
    # disable frustum culling + force render via a tiny camera nudge through requestRender
    pg.evaluate("""() => {
      window.scene.traverse(o => { if (o.isLineSegments && o.geometry.attributes.position.count === 1936) { o.frustumCulled = false; } });
    }""")
    # force a render: nudge sun time slightly via Atmosphere.update (calls requestRender)
    pg.evaluate("() => window.Atmosphere.update(12.01, 45)")
    pg.wait_for_timeout(800)
    pg.screenshot(path=f"{OUT}/diag_contour_nocull.png")
    from PIL import Image
    img = Image.open(f"{OUT}/diag_contour_nocull.png").convert('RGB')
    px = img.load()
    h1 = sum(1 for y in range(52,800) for x in range(280,1280) if abs(px[x,y][0]-38)<8 and abs(px[x,y][1]-26)<7 and abs(px[x,y][2]-13)<7)
    h2 = sum(1 for y in range(52,800) for x in range(280,1280) if abs(px[x,y][0]-64)<8 and abs(px[x,y][1]-46)<7 and abs(px[x,y][2]-20)<7)
    print('no-cull: index', h1, 'normal', h2)
    b.close()
"""Draw-call delta: does adding the red box increase renderer draw calls + does it paint above terrain?"""
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
    pg.wait_for_timeout(600)
    pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()")
    pg.wait_for_timeout(1200)
    pg.evaluate("() => document.getElementById('toast').classList.remove('visible')")
    pg.evaluate("() => window.Atmosphere.update(12.0, 45)")
    pg.wait_for_timeout(1000)
    info = pg.evaluate("""() => { const i = window._test.renderer.info; return { calls: i.render.calls, tris: i.render.triangles, frame: i.render.frame, lost: window._test.renderer.getContext().isContextLost() }; }""")
    print("before box:", json.dumps(info))
    pg.evaluate("""() => {
      let yard = null;
      window.scene.traverse(o => { if (o.isMesh && o.geometry && o.geometry.attributes.position && o.geometry.attributes.position.count > 20000 && !yard) yard = o; });
      const g = new (yard.geometry.constructor)();
      g.setAttribute('position', new (yard.geometry.attributes.position.constructor)(new Float32Array([
        -6, -13.8, -14,  -6, -13.8, -6,  -2, -13.8, -14,
        -2, -13.8, -14,  -6, -13.8, -6,  -2, -13.8, -6 ]), 3));
      const col = new Float32Array(18);
      for (let i = 0; i < 18; i += 3) { col[i] = 1; }
      g.setAttribute('color', new (yard.geometry.attributes.color.constructor)(col, 3));
      const mesh = new (yard.constructor)(g, yard.material);
      mesh.renderOrder = 1003;
      window.__box = mesh;
      window.scene.add(mesh);
      window.Atmosphere.update(12.0, 45);
    }""")
    pg.wait_for_timeout(1000)
    info2 = pg.evaluate("""() => { const i = window._test.renderer.info; return { calls: i.render.calls, tris: i.render.triangles, frame: i.render.frame }; }""")
    print("after box:", json.dumps(info2))
    pg.screenshot(path=OUT + "/box_above.png")
    from PIL import Image
    img = Image.open(OUT + "/box_above.png").convert('RGB')
    px = img.load()
    red = sum(1 for y in range(52,800) for x in range(280,1280) if px[x,y][0]>200 and px[x,y][1]<80 and px[x,y][2]<80)
    print("box red px:", red)
    b.close()

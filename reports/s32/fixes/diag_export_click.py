"""Diagnose: why did #export-stl click succeed on the UNFIXED page? Where is the item rect, what's at the click point?"""
import json, time
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    pg = b.new_context(viewport={"width":1280,"height":800}).new_page()
    pg.set_default_timeout(12000)
    pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
    pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(500)
    pg.evaluate("() => window.setMode('advanced')"); pg.wait_for_timeout(800)
    pg.click("#btn-export"); pg.wait_for_timeout(400)
    st = pg.evaluate("""() => {
      const m = document.getElementById('export-menu');
      const r = m.getBoundingClientRect();
      const items = ['export-stl','export-obj','export-heightmap','export-screenshot-hd'].map(id => {
        const el = document.getElementById(id); const ir = el.getBoundingClientRect();
        const cx = ir.x+ir.width/2, cy = ir.y+ir.height/2;
        const hit = document.elementFromPoint(cx, cy);
        return { id, rect: {x:Math.round(ir.x),y:Math.round(ir.y),w:Math.round(ir.width),h:Math.round(ir.height)},
                 cx: Math.round(cx), cy: Math.round(cy), hit: hit ? (hit.id || hit.tagName) : null };
      });
      const tb = document.getElementById('topbar');
      return { menu: {x:Math.round(r.x),y:Math.round(r.y),h:Math.round(r.height)}, items,
               tbOverflowY: getComputedStyle(tb).overflowY, tbScroll: tb.scrollLeft };
    }""")
    print(json.dumps(st, indent=1))
    # now try REAL mouse click at STL item center
    it = st['items'][0]
    try:
        with pg.expect_download(timeout=30000) as dl:
            pg.mouse.click(it['cx'], it['cy'])
        print("RAW mouse click ->", dl.value.suggested_filename)
    except Exception as e:
        print("RAW mouse click FAIL:", str(e)[:140])
    b.close()
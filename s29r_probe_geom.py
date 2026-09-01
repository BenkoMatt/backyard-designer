#!/usr/bin/env python3
"""Read-only geometry probe: scale-bar vs bottom toolbar buttons; sun-panel header;
excavate open refreshes buried list; where terrain-btn sits."""
import json
from playwright.sync_api import sync_playwright

URL = "http://localhost:8220/index.html"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1280, "height": 800})
    pg.goto(URL, wait_until="networkidle", timeout=30000)
    pg.wait_for_timeout(1500)
    pg.evaluate("() => { try{localStorage.removeItem('backyard-recovery-snapshot');}catch(e){} }")
    pg.reload(wait_until="networkidle"); pg.wait_for_timeout(1500)
    skip = pg.locator("#wizard-skip")
    if skip.count() > 0:
        skip.click(); pg.wait_for_timeout(800)
    # zoom in a bit so scale bar is long? keep default. Measure rects.
    rects = pg.evaluate("""() => {
      const sels = ['#scale-bar','#tape-measure-btn','#sun-btn','#excavate-btn',
                    '#terrain-analysis-btn','#innovation-btn','#terrain-btn',
                    '#sun-panel','#excavate-panel','#terrain-controls','#status-bar',
                    '#bottom-left-toolbar','#tool-dock'];
      const out = {};
      for (const s of sels) {
        const el = document.querySelector(s);
        if (!el) { out[s] = null; continue; }
        const cs = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        out[s] = {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
                  h:Math.round(r.height),right:Math.round(r.right),bottom:Math.round(r.bottom),
                  disp:cs.display};
      }
      return out;
    }""")
    print(json.dumps(rects, indent=1))
    # overlap math scale-bar vs buttons
    sb = rects["#scale-bar"]
    if sb:
        for btn in ["#tape-measure-btn", "#sun-btn", "#excavate-btn", "#terrain-analysis-btn", "#innovation-btn", "#terrain-btn"]:
            bb = rects[btn]
            if not bb: continue
            ox = max(0, min(sb["right"], bb["right"]) - max(sb["x"], bb["x"]))
            oy = max(0, min(sb["bottom"], bb["bottom"]) - max(sb["y"], bb["y"]))
            print(f"scale-bar vs {btn}: overlapX={ox} overlapY={oy} area={ox*oy}")
    # sun panel header check
    hdr = pg.evaluate("""() => {
      const sp = document.getElementById('sun-panel');
      return {html: sp ? sp.innerHTML.slice(0, 300) : null,
              hasHeader: !!(sp && sp.querySelector('.sun-header, .excavate-header, .innov-header'))};
    }""")
    print("SUN PANEL:", json.dumps(hdr, indent=1))
    # does opening excavate refresh buried list? bury 2 via _test then click excavate
    pg.evaluate("""() => { // _test setup
      const T = window._test;
      T.addObject('shed', {}, {x:-12, y:-6, z:0});
      T.addObject('pergola', {}, {x:8, y:-9, z:4});
      return T.getBuriedObjects().length;
    }""")
    pg.locator("#excavate-btn").click(); pg.wait_for_timeout(900)
    buried = pg.evaluate("""() => ({
      count: document.getElementById('buried-count').textContent,
      items: [...document.querySelectorAll('#buried-list .buried-item')].map(e => e.textContent.trim().slice(0,40))
    })""")
    print("BURIED AFTER OPEN:", json.dumps(buried))
    b.close()
print("DONE")
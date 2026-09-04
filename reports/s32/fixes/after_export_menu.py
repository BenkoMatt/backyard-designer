"""S32-C2: export menu portal — before verification at 2 viewports (current broken state captured in probe_before)."""
import json, time, os
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"

def probe(pg, tag):
    pg.click("#btn-export"); pg.wait_for_timeout(400)
    st = pg.evaluate("""() => {
      const m = document.getElementById('export-menu');
      const r = m.getBoundingClientRect();
      const tb = document.getElementById('topbar').getBoundingClientRect();
      const cx = r.x + r.width/2, cy = Math.min(r.y + r.height/2, 790);
      const hit = document.elementFromPoint(cx, cy);
      let chain = []; let el = hit;
      while (el && chain.length < 4) { chain.push(el.id || el.className || el.tagName); el = el.parentElement; }
      const item = document.getElementById('export-stl');
      const ir = item.getBoundingClientRect();
      const itemHit = document.elementFromPoint(ir.x + ir.width/2, ir.y + ir.height/2);
      return { parent: m.parentElement.id || m.parentElement.tagName, display: m.style.display,
               rect: {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},
               topbarBottom: Math.round(tb.bottom), centerHit: chain,
               itemHitIsItem: itemHit === item || (itemHit && itemHit.closest && itemHit.closest('#export-menu') !== null),
               belowTopbarVisible: r.bottom > tb.bottom + 10 };
    }""")
    pg.screenshot(path=f"{OUT}/{tag}.png")
    # real-click the STL item and watch for download
    dl = None
    try:
        with pg.expect_download(timeout=60000) as dli:
            pg.click("#export-stl", timeout=4000)
        dl = dli.value.suggested_filename
    except Exception as e:
        dl = f"FAIL {str(e)[:90]}"
    pg.keyboard.press("Escape"); pg.mouse.click(640, 400); pg.wait_for_timeout(250)
    return st, dl

res = {}
with sync_playwright() as pw:
    for (w,h,tag) in [(1280,800,"after_export_1280"),(1024,768,"after_export_1024")]:
        b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
        ctx = b.new_context(viewport={"width":w,"height":h})
        pg = ctx.new_page(); pg.set_default_timeout(12000)
        errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
        pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(500)
        pg.evaluate("() => window.setMode('advanced')"); pg.wait_for_timeout(400)
        st, dl = probe(pg, tag)
        res[tag] = {"probe": st, "stl_download": dl, "errors": errs}
        print(tag, json.dumps(st), "DL:", dl)
        b.close()
json.dump(res, open(f"{OUT}/after_export_menu.json","w"), indent=1)
print("saved")
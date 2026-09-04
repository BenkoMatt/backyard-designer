"""S32-C2 raw-mouse verification: human-equivalent click at STL item center must export."""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
res = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    pg = b.new_context(viewport={"width":1280,"height":800}).new_page()
    pg.set_default_timeout(12000)
    pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
    pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(500)
    pg.evaluate("() => window.setMode('advanced')"); pg.wait_for_timeout(1200)
    pg.click("#btn-export"); pg.wait_for_timeout(400)
    st = pg.evaluate("""() => {
      const ir = document.getElementById('export-stl').getBoundingClientRect();
      return { cx: Math.round(ir.x+ir.width/2), cy: Math.round(ir.y+ir.height/2) };
    }""")
    try:
        with pg.expect_download(timeout=25000) as dl:
            pg.mouse.click(st['cx'], st['cy'])  # raw CDP mouse at item center — human-equivalent
        ok = dl.value.suggested_filename
    except Exception as e:
        ok = f"FAIL {str(e)[:80]}"
    # second viewport raw-click (heightmap item at 1024x768)
    res = {"stl_center": st, "raw_click_stl": ok}
    print(json.dumps(res))
    b.close()
json.dump(res, open(f"{OUT}/after_export_rawclick.json","w"), indent=1)
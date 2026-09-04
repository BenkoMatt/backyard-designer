"""AFTER-probe for S32-C1: share copy now succeeds via exec fallback."""
import json, time, os
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
res = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    ctx = b.new_context(viewport={"width":1280,"height":800})
    pg = ctx.new_page(); pg.set_default_timeout(12000)
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
    pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(500)
    pg.evaluate("() => window.setMode('advanced')"); pg.wait_for_timeout(300)
    # grant clipboard-permission DENY to force the writeText rejection path deterministically
    ctx2 = ctx  # (already-default; we instead rely on real behavior)
    pg.click("#btn-share"); pg.wait_for_timeout(500)
    url = pg.evaluate("() => document.getElementById('share-url-box').textContent")
    pg.click("#share-copy-btn"); pg.wait_for_timeout(700)
    toast = pg.evaluate("() => document.getElementById('toast')?.textContent || ''")
    toastcls = pg.evaluate("() => document.getElementById('toast')?.className || ''")
    pg.screenshot(path=f"{OUT}/after_share_copy.png")
    # 3 repeats for determinism
    reps=[]
    for i in range(3):
        pg.click("#share-copy-btn"); pg.wait_for_timeout(500)
        reps.append(pg.evaluate("() => document.getElementById('toast')?.textContent || ''"))
    res = {"url_len": len(url), "toast": toast, "toast_class": toastcls, "repeats": reps, "errors": errs}
    b.close()
json.dump(res, open(f"{OUT}/after_share_copy.json","w"), indent=1)
print(json.dumps(res, indent=1))
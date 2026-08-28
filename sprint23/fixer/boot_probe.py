"""Load the app and capture boot errors (pageerror + console)."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errs = []
    console = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.on("console", lambda m: console.append(f"{m.type}: {m.text[:300]}") if m.type in ("error", "warning") else None)
    page.goto("http://localhost:8304/index.html", timeout=30000)
    page.wait_for_timeout(3000)
    print("PAGE ERRORS:", len(errs))
    for e in errs[:10]:
        print("  ", e[:500])
    print("CONSOLE err/warn:", len(console))
    for c in console[:10]:
        print("  ", c[:400])
    boot = page.evaluate("() => ({yardReady: window._bydState ? !!window._bydState.yardReady : 'no _bydState', hasTHREE: !!window._bydTHREE})")
    print("boot:", boot)
    browser.close()
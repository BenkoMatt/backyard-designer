"""Get real catalog type names for the retest."""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1500)
    types = page.evaluate("""() => {
        // probe CATALOG via a test object
        return Object.keys(window._bydState ? {} : {});
    }""")
    # probe via addObject with fake types is noisy; instead use lib-item clicks
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    names = page.evaluate("""() => Array.from(document.querySelectorAll('.lib-item')).slice(0, 6).map(el => el.getAttribute('aria-label'))""")
    print("first lib items:", json.dumps(names, indent=1))
    # check which of my test types exist
    for t in ["bush_round", "hedge_formal", "tree_deciduous"]:
        ok = page.evaluate(f"type => {{ try {{ const id = window.addObject(type, {{}}, {{x: 0, y: 0, z: 0}}); return id !== null && id !== undefined; }} catch(e) {{ return String(e); }} }}", t)
        print(f"type {t}: addable={ok}")
    ctx.close()
    browser.close()
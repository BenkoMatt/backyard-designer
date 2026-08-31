"""Re-shoot dock area with full-width-safe crop; verify no viewport clipping."""
import json
from playwright.sync_api import sync_playwright
from s23a_common import load_app, to_advanced
import s23a_common
s23a_common.URL = "http://localhost:8092/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    load_app(page)
    to_advanced(page)
    page.click('.td-tab[data-dock="underground"]')
    page.wait_for_timeout(500)
    r = page.evaluate("""() => {
        const dp = document.getElementById('dock-underground').getBoundingClientRect();
        return { right: Math.round(dp.right), bottom: Math.round(dp.bottom), vw: innerWidth, vh: innerHeight,
                 clippedRight: dp.right > innerWidth, clippedBottom: dp.bottom > innerHeight };
    }""")
    print(json.dumps(r, indent=1))
    page.screenshot(path="s23b_after_3_dock_area.png", clip={"x": 0, "y": 400, "width": 840, "height": 400})
    browser.close()
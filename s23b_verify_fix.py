"""Verify dock-panel no longer covers tool-dock labels at 1280x800."""
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
        const td = document.getElementById('tool-dock').getBoundingClientRect();
        const dp = document.getElementById('dock-underground').getBoundingClientRect();
        const ix = Math.max(0, Math.min(td.right, dp.right) - Math.max(td.left, dp.left));
        const iy = Math.max(0, Math.min(td.bottom, dp.bottom) - Math.max(td.top, dp.top));
        return { toolDock: {x: td.x, y: td.y, w: td.width, h: td.height},
                 dockPanel: {x: dp.x, y: dp.y, w: dp.width, h: dp.height},
                 overlapPx: Math.round(ix * iy) };
    }""")
    print(json.dumps(r, indent=1))
    page.screenshot(path="s23b_after_3_dock_area.png", clip={"x": 0, "y": 480, "width": 700, "height": 320})
    page.screenshot(path="s23b_after_2_docktab_plus_excavate.png")
    # also verify duplicate header gone in full shot
    browser.close()
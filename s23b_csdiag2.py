"""Diag: is cross-section-toggle clickable, and does its classList toggle?"""
from playwright.sync_api import sync_playwright
from s23a_common import load_app, to_advanced
import s23a_common
s23a_common.URL = "http://localhost:8092/index.html"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1280, "height": 800})
    load_app(pg)
    to_advanced(pg)
    pg.click('.td-tab[data-dock="underground"]')
    pg.wait_for_timeout(500)
    for attempt in range(3):
        try:
            pg.click("#cross-section-toggle", force=True, timeout=3000)
            path = "CDP click"
        except Exception as e:
            path = f"CDP failed ({type(e).__name__}); JS click"
            pg.evaluate("() => document.getElementById('cross-section-toggle').click()")
        pg.wait_for_timeout(400)
        st = pg.evaluate("""() => ({
            csVisible: document.getElementById('cross-section-panel').classList.contains('visible'),
            btnActive: document.getElementById('cross-section-toggle').classList.contains('active') })""")
        print(attempt, path, st)
        if st["csVisible"]:
            break
        # toggle back for next attempt
        pg.evaluate("() => document.getElementById('cross-section-toggle').click()")
        pg.wait_for_timeout(250)
    b.close()
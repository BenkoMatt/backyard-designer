"""Check Playwright chromium availability for Bug Hunt C."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    print("chromium path:", p.chromium.executable_path)
    try:
        b = p.chromium.launch(headless=True)
        pg = b.new_page()
        pg.goto("http://localhost:8303/index.html", wait_until="domcontentloaded", timeout=20000)
        print("title:", pg.title())
        b.close()
        print("BROWSER OK")
    except Exception as e:
        print("LAUNCH FAIL:", e)
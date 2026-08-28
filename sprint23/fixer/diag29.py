"""Check for JS runtime errors after the openModal/closeModal stack edits."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8304/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    msgs = []
    page.on("pageerror", lambda e: msgs.append(("pageerror", str(e))))
    page.on("console", lambda m: msgs.append((m.type, m.text)) if m.type in ("error",) else None)
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(2500)
    print("errors:", msgs[:10])
    print("openModal exists:", page.evaluate("() => typeof openModal"))
    print("closeModal exists:", page.evaluate("() => typeof closeModal"))
    print("escape sweep test: press Esc and check wizard")
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    print("wizard display:", repr(page.evaluate("() => document.getElementById('wizard').style.display")))
    print("all errors:", msgs[:10])
    ctx.close()
    browser.close()
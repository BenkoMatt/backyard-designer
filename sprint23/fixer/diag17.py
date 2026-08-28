"""V01: find the object's exact screen position via pixel-bisect after each reload,
then select, drag, undo. Reuse diag15's working sequence (drag DID move the object
there: -15 -> -4.12). In diag15 the drag worked WITHOUT prior click-select.
So: place -> drag -> undo directly."""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"
errors = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    page.locator("#wp-scratch").click(); page.wait_for_timeout(300)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(600)
    # diag15 sequence: slow drag at (540,372) worked without pre-click
    pos_before = page.evaluate("() => window._bydState.objects.get(1).position.x")
    page.mouse.move(540, 372)
    page.mouse.down()
    for i in range(1, 11):
        page.mouse.move(540 + i * 8, 372 + i * 4)
        page.wait_for_timeout(30)
    page.mouse.up()
    page.wait_for_timeout(400)
    pos_after = page.evaluate("() => window._bydState.objects.get(1).position.x")
    page.keyboard.press("Control+z")
    page.wait_for_timeout(400)
    pos_undo = page.evaluate("() => window._bydState.objects.get(1)?.position.x")
    cnt = page.evaluate("() => window._bydState.objects.size")
    ok = abs(pos_after - pos_before) > 5 and pos_undo is not None and abs(pos_undo - pos_before) < 2 and cnt == 1
    print(f"V01: before={pos_before} after={pos_after} undo={pos_undo} count={cnt} -> {'PASS' if ok else 'FAIL'}")
    print("page errors:", errors[:5])
    ctx.close()
    browser.close()
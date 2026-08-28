"""V01: check camera vs object. The camera projection says screen (455,428) but the
drag doesn't grab. Maybe the object is NOT under the cursor (projection of group
position vs mesh position, or the camera looks from an angle and the object is
offset). Use the app's own raycast through a synthetic probe: dispatch a real
pointerdown and then read where the app THOUGHT the mouse was (via selectObject
side effects: selectedId). Then bisect: click at various screen points to find
where the object actually is on screen.
"""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    page.locator("#wp-scratch").click(); page.wait_for_timeout(300)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(600)
    # scan a grid of points; after each plain click check selectedId
    points = []
    r = page.evaluate("() => { const b = window._bydRenderer.domElement.getBoundingClientRect(); return {x: b.left, y: b.top, w: b.width, h: b.height}; }")
    found = None
    for gx in range(0, 680, 60):
        for gy in range(0, 848, 60):
            x, y = r["x"] + gx + 20, r["y"] + gy + 20
            page.mouse.click(x, y)
            page.wait_for_timeout(60)
            sid = page.evaluate("() => window._bydState.selectedId")
            if sid == 1:
                found = (x, y)
                break
        if found:
            break
    print("found object at screen:", found)
    if found:
        pos_before = page.evaluate("() => window._bydState.objects.get(1).position.x")
        page.mouse.move(found[0], found[1])
        page.mouse.down()
        page.mouse.move(found[0] + 80, found[1] + 40, steps=8)
        page.mouse.up()
        page.wait_for_timeout(400)
        pos_after = page.evaluate("() => window._bydState.objects.get(1).position.x")
        print(f"drag at found point: {pos_before} -> {pos_after}")
        page.keyboard.press("Control+z"); page.wait_for_timeout(300)
        print("after undo:", page.evaluate("() => window._bydState.objects.get(1)?.position.x"))
    ctx.close()
    browser.close()
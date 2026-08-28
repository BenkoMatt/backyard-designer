"""V01 final repro: drag using viewport-relative projection (canvas at 280,52)."""
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
    screen = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        if (!g) return null;
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const r = window._bydRenderer.domElement.getBoundingClientRect();
        return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
    }""")
    pos_before = page.evaluate("() => JSON.parse(JSON.stringify(window._bydState.objects.get(1).position))")
    page.mouse.move(screen["x"], screen["y"])
    page.mouse.down()
    page.mouse.move(screen["x"] + 80, screen["y"] + 40, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)
    pos_after = page.evaluate("() => JSON.parse(JSON.stringify(window._bydState.objects.get(1).position))")
    page.keyboard.press("Control+z")
    page.wait_for_timeout(400)
    pos_undo = page.evaluate("() => JSON.parse(JSON.stringify(window._bydState.objects.get(1).position))")
    ok = (pos_after and pos_undo and abs(pos_after["x"] - pos_before["x"]) > 30
          and abs(pos_undo["x"] - pos_before["x"]) < 2)
    print(f"V01: before={pos_before} after={pos_after} undo={pos_undo} -> {'PASS' if ok else 'FAIL'}")
    print("errors:", errors[:5])
    ctx.close()
    browser.close()
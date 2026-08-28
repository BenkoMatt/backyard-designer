"""V01 final: object got REMOVED by undo? Check object count + undo behavior step by step."""
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
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const r = window._bydRenderer.domElement.getBoundingClientRect();
        return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
    }""")
    pos_before = page.evaluate("() => window._bydState.objects.get(1).position.x")
    page.mouse.move(screen["x"], screen["y"])
    page.mouse.down()
    page.mouse.move(screen["x"] + 80, screen["y"] + 40, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)
    pos_after = page.evaluate("() => window._bydState.objects.get(1).position.x")
    stack = page.evaluate("""() => window._bydState.undoStack.map(c => (c.undo ? c.undo.toString().slice(0, 100) : 'nofn'))""")
    print("undoStack after drag:", stack)
    page.keyboard.press("Control+z")
    page.wait_for_timeout(400)
    cnt = page.evaluate("() => window._bydState.objects.size")
    pos_undo = page.evaluate("() => { const o = window._bydState.objects.get(1); return o ? o.position.x : 'REMOVED'; }")
    print(f"V01: before x={pos_before} after x={pos_after} undoStack={stack}")
    print(f"V01: after Ctrl+Z count={cnt} x={pos_undo}")
    print("errors:", errors[:5])
    ctx.close()
    browser.close()
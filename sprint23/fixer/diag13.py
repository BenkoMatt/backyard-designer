"""V01: does the drag work with the props panel CLOSED? Test panel-open vs panel-closed drag."""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"

def proj_expr():
    return """() => {
        const g = window._bydSceneObjects.get(1);
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const r = window._bydRenderer.domElement.getBoundingClientRect();
        return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
    }"""

def drag(page, screen, dx, dy):
    page.mouse.move(screen["x"], screen["y"])
    page.mouse.down()
    page.mouse.move(screen["x"] + dx, screen["y"] + dy, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # Case A: props panel closed before dragging (deselect first via Escape)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    page.locator("#wp-scratch").click(); page.wait_for_timeout(300)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(600)
    page.keyboard.press("Escape")  # deselect -> hides props (deselectObject)
    page.wait_for_timeout(400)
    print("A props visible:", page.evaluate("() => document.getElementById('properties').classList.contains('visible')"))
    screen = page.evaluate(proj_expr())
    print("A screen:", screen)
    pos_before = page.evaluate("() => window._bydState.objects.get(1).position.x")
    drag(page, screen, 80, 40)
    pos_after = page.evaluate("() => window._bydState.objects.get(1).position.x")
    print(f"A drag with panel closed: {pos_before} -> {pos_after}")
    # undo
    page.keyboard.press("Control+z"); page.wait_for_timeout(300)
    pos_undo = page.evaluate("() => window._bydState.objects.get(1)?.position.x")
    cnt = page.evaluate("() => window._bydState.objects.size")
    print(f"A after Ctrl+Z: x={pos_undo} count={cnt}")
    ctx.close()

    # Case B: panel open (as after add)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    page.locator("#wp-scratch").click(); page.wait_for_timeout(300)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(600)
    print("B props visible:", page.evaluate("() => document.getElementById('properties').classList.contains('visible')"))
    screen = page.evaluate(proj_expr())
    print("B screen:", screen)
    pos_before = page.evaluate("() => window._bydState.objects.get(1).position.x")
    drag(page, screen, 80, 40)
    pos_after = page.evaluate("() => window._bydState.objects.get(1).position.x")
    print(f"B drag with panel open: {pos_before} -> {pos_after}")
    ctx.close()
    browser.close()
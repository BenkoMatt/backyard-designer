"""V01: instrument onPointerDown itself by reading app code path via monkey-patch-free probe.

Strategy: capture-phase listener on document that logs pointerdown, plus check whether
the viewport handler even runs (it must, since pointer events reach the canvas).
The suspect: with the properties panel docked (S23-V02), the canvas is 680px wide and
the object at (456,428) is over the canvas, but OrbitControls (attached to renderer.domElement?)
may capture pointerdown FIRST and stopPropagation... or the app's handler checks
e.target === viewport canvas.
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
    screen = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const vp = document.getElementById('viewport').getBoundingClientRect();
        return { x: vp.left + (v.x + 1) / 2 * vp.width, y: vp.top + (1 - v.y) / 2 * vp.height };
    }""")
    # canvas position + size
    canvas_info = page.evaluate("""() => {
        const c = document.querySelector('#viewport canvas');
        const r = c.getBoundingClientRect();
        return { left: r.left, top: r.top, w: r.width, h: r.height };
    }""")
    print("canvas rect:", canvas_info, "object screen:", screen)
    # Is the object's screen pos actually ON the canvas?
    on_canvas = (screen["x"] >= canvas_info["left"] and screen["x"] <= canvas_info["left"] + canvas_info["w"]
                 and screen["y"] >= canvas_info["top"] and screen["y"] <= canvas_info["top"] + canvas_info["h"])
    print("object over canvas:", on_canvas)
    # project with the CORRECT viewport-relative canvas
    screen2 = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        const c = document.querySelector('#viewport canvas');
        const cr = c.getBoundingClientRect();
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        return { x: cr.left + (v.x + 1) / 2 * cr.width, y: cr.top + (1 - v.y) / 2 * cr.height,
                vx: (v.x + 1)/2, vy: (v.y+1)/2 };
    }""")
    print("screen2 (canvas-anchored):", screen2)
    page.mouse.move(screen2["x"], screen2["y"])
    page.mouse.down()
    page.mouse.move(screen2["x"] + 80, screen2["y"] + 40, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)
    pos = page.evaluate("() => window._bydState.objects.get(1)?.position")
    print("pos after canvas-anchored drag:", pos)
    print("selectedId:", page.evaluate("() => window._bydState.selectedId"))
    ctx.close()
    browser.close()
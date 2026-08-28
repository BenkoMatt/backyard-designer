"""Find where the V01 drag happens: which handler consumed the pointer events."""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    # instrument pointer events
    page.evaluate("""() => {
        window.__ptr = [];
        const vp = document.getElementById('viewport');
        ['pointerdown','pointermove','pointerup'].forEach(t =>
            vp.addEventListener(t, e => window.__ptr.push({t, x: e.clientX, y: e.clientY, target: e.target.tagName})));
    }""")
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(600)
    screen = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const vp = document.getElementById('viewport').getBoundingClientRect();
        return { x: vp.left + (v.x + 1) / 2 * vp.width, y: vp.top + (1 - v.y) / 2 * vp.height };
    }""")
    print("screen:", screen)
    page.mouse.move(screen["x"], screen["y"])
    page.mouse.down()
    page.mouse.move(screen["x"] + 80, screen["y"] + 40, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)
    print("ptr log:", json.dumps(page.evaluate("() => window.__ptr"), indent=0)[:600])
    print("pos:", page.evaluate("() => window._bydState.objects.get(1)?.position"))
    print("isDragging/dragObject are module-scoped; undoStack:", page.evaluate("() => window._bydState.undoStack.map(c => (c.undo||'').toString?.().slice(0,80) || 'fn')"))
    # check if props panel opened (auto-select on pointerdown hit)
    print("props visible:", page.evaluate("() => document.getElementById('properties').classList.contains('visible')"))
    print("selectedId:", page.evaluate("() => window._bydState.selectedId"))
    browser.close()
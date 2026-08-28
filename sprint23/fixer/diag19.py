"""V01: after the drag-through, WHAT happened? selectedId? undoStack content?

The pattern 'after=unchanged, undo REMOVES object' means Ctrl+Z ran the ADD-undo
(removeObject) — so the drag command was never pushed AND the add was the top of
stack. So the drag never moved the object: onPointerDown hit-test failed on the
drag's pointerdown (else position would change on move)...

BUT WAIT: maybe the drag DID happen and the move applied to a DIFFERENT object?
No, single object.

Or... the pointerdown at hit-point hit the object and set isDragging=true, but
pointermove raycast MISSED the yard (hits.length==0) and intersectPlane returned
a point far away, clamped... no, position would still change.

Focus: does the object's POSITION change during move at all? Log position
mid-drag.
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
    page.wait_for_timeout(800)
    proj = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const r = window._bydRenderer.domElement.getBoundingClientRect();
        return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
    }""")
    hit = None
    for dx in range(-40, 41, 10):
        for dy in range(-40, 41, 10):
            page.mouse.click(proj["x"] + dx, proj["y"] + dy)
            page.wait_for_timeout(80)
            sid = page.evaluate("() => window._bydState.selectedId")
            if sid == 1:
                hit = (proj["x"] + dx, proj["y"] + dy)
                break
        if hit:
            break
    print("hit:", hit)
    # instrument: log positions during drag via rAF polling
    page.evaluate("""() => {
        window.__posLog = [];
        window.__poll = setInterval(() => {
            const o = window._bydState.objects.get(1);
            if (o) window.__posLog.push([o.position.x.toFixed(2), o.position.z.toFixed(2)]);
        }, 100);
    }""")
    page.mouse.move(hit[0], hit[1])
    page.mouse.down()
    for i in range(1, 11):
        page.mouse.move(hit[0] + i * 8, hit[1] + i * 4)
        page.wait_for_timeout(25)
    page.mouse.up()
    page.wait_for_timeout(600)
    page.evaluate("() => clearInterval(window.__poll)")
    print("posLog:", page.evaluate("() => window.__posLog"))
    print("selectedId after:", page.evaluate("() => window._bydState.selectedId"))
    print("undoStack len:", page.evaluate("() => window._bydState.undoStack.length"))
    print("undo top:", page.evaluate("() => window._bydState.undoStack[window._bydState.undoStack.length-1]?.undo?.toString?.().slice(0,80)"))
    ctx.close()
    browser.close()
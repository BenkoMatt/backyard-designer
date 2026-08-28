"""V01: check whether OrbitControls swallows pointerdown (stopPropagation?) and
whether the app's own handlers are on `viewport` while the CANVAS is the target.

Key question: when Playwright clicks the canvas, does the viewport-level
pointerdown handler run BEFORE OrbitControls' canvas-level handler? Both fire
(bubbling). The app handler doesn't stopPropagation, so OrbitControls ALSO
receives it. OrbitControls with enabled=true will ORBIT the camera on drag and
calls preventDefault... but the app already set controls.enabled=false AFTER
its own handler runs (same event loop turn). Actually both listeners fire for
the same pointerdown: the app's (viewport, bubble) and controls' (canvas). If
controls' listener runs first (capture or earlier registration), it may
setPointerCapture on the canvas — pointermove events then still fire on canvas.

The real question: after mouse.down at a point that SELECTS (selectedId=1),
does isDragging become true? Hint says 'Drag to position' (from add), and
onPointerDown would set 'Drag to move • Release to place' — diag12 showed the
hint did NOT change to 'Drag to move'. But wait — diag12's listener observed
'class' attribute + text; initial hints pushed 4 entries 'Drag to position' —
those were the LIBRARY click's showToast/hint. The drag-hint never appeared.

So the raycast MISSED at (540,372) for the DRAG but the plain CLICK selected?
Both go through the same handler! Unless... the click that 'found' the object
in diag14 was the click at that position — selectedId became 1. Then the drag
pointerdown at the same point: hits raycast — should hit again...

AH WAIT. Look at diag14: 'found object at (540,372)' — that was a CLICK that
selected. Then 'drag at found point: -15 -> -15'. If the drag started,
isDragging=true, and pointermove moved the object... but position unchanged.

Is it possible the app is in a state where pointerdown on object sets
isDragging=true but a DIFFERENT pointerdown handler (OrbitControls) ALSO got
the event and ORBITED the camera, so by pointerup the object moved in world
space but... no, position.x stayed -15 exactly.

Hypothesis: THREE.js raycast against the bush mesh at that screen point hits
the YARD first (yardMesh pushed after objects, objHit finds objectId mesh) —
fine. But for the DRAG path: hits.length>0 but objHit undefined -> deselect!
Then isDragging=false -> move does nothing. But then selectedId would be null
after the drag... check that.
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
    # click to select at found point
    page.mouse.click(540, 372)
    page.wait_for_timeout(200)
    print("selectedId after click:", page.evaluate("() => window._bydState.selectedId"))
    # slow drag with small steps
    page.mouse.move(540, 372)
    page.mouse.down()
    for i in range(1, 11):
        page.mouse.move(540 + i * 8, 372 + i * 4)
        page.wait_for_timeout(40)
    page.mouse.up()
    page.wait_for_timeout(500)
    print("pos:", page.evaluate("() => window._bydState.objects.get(1).position"))
    print("selectedId after drag:", page.evaluate("() => window._bydState.selectedId"))
    print("props visible:", page.evaluate("() => document.getElementById('properties').classList.contains('visible')"))
    print("undoStack:", page.evaluate("() => window._bydState.undoStack.length"))
    ctx.close()
    browser.close()
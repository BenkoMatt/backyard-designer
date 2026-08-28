"""V01: bisect the exact object hit point reliably, then drag, then undo.

diag15 got the object moved (-15 -> -4.12) with the SAME sequence that now fails.
Flakiness = pointer-events race with props panel opening (S23-V02 note: panel
open/close resizes canvas + shifts raycast screen coords — re-scan before every
click). The props panel opened AFTER placement (auto-showProperties). Canvas
resized 680 wide at that moment. In diag15 the first drag attempt happened when
the panel had JUST opened (canvas 680px). Position (540,372): x=540 within
canvas x-range [280, 960]... yes. But after undo, canvas reverts.

Stable approach: recompute the object's screen pos AFTER any panel settles,
using renderer.domElement rect, with SLOW drag and re-projecting between steps
(project once, small movement). If pointer leaves the object, the drag STILL
continues (isDragging independent of hit) — pointermove raycasts the GROUND,
so the object follows the ground point. So as long as pointerdown HITS the
object, everything after works.

Plan: click at projected point; if selectedId==1, drag with slow steps from
THERE; undo; verify.
"""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"
errors = []

def project(page):
    return page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        if (!g) return null;
        const box = new (window._bydTHREE ? window._bydTHREE.Box3 : Object)();
        return null;
    }""")

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
    page.wait_for_timeout(800)

    # find hit point by scanning small grid around projected position
    proj = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const r = window._bydRenderer.domElement.getBoundingClientRect();
        return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
    }""")
    print("projected:", proj)
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
    print("hit point:", hit)
    if hit:
        pos_before = page.evaluate("() => window._bydState.objects.get(1).position.x")
        # deselect first (plain click on empty space) so drag starts from a clean select
        page.mouse.click(hit[0] + 250, hit[1] + 250)  # far corner: deselect
        page.wait_for_timeout(200)
        # now drag THROUGH the object
        page.mouse.move(hit[0], hit[1])
        page.mouse.down()
        for i in range(1, 11):
            page.mouse.move(hit[0] + i * 8, hit[1] + i * 4)
            page.wait_for_timeout(25)
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
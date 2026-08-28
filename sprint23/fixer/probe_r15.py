"""Run-15 probe: V01 drag-undo detail + V04 counter-case modal stack trace."""
import time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8304/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---------- V01 detail ----------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    try:
        wp = page.locator("#wp-scratch")
        if wp.count() > 0 and wp.is_visible():
            wp.click(); page.wait_for_timeout(300)
    except Exception:
        pass
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
            if page.evaluate("() => window._bydState.selectedId") == 1:
                hit = (proj["x"] + dx, proj["y"] + dy)
                break
        if hit: break
    print("HIT:", hit, flush=True)
    if hit:
        before = page.evaluate("() => { const o = window._bydState.objects.get(1); return {x: o.position.x, z: o.position.z}; }")
        us_len_before = page.evaluate("() => window._bydState.undoStack.length")
        page.mouse.move(hit[0], hit[1])
        page.mouse.down()
        for i in range(1, 16):
            page.mouse.move(hit[0] + i * 8, hit[1] + i * 4)
            page.wait_for_timeout(25)
        page.mouse.up()
        page.wait_for_timeout(500)
        after = page.evaluate("() => { const o = window._bydState.objects.get(1); return {x: o.position.x, z: o.position.z}; }")
        us_len_drag = page.evaluate("() => window._bydState.undoStack.length")
        page.keyboard.press("Control+z")
        page.wait_for_timeout(500)
        undone = page.evaluate("() => { const o = window._bydState.objects.get(1); return o ? {x: o.position.x, z: o.position.z} : null; }")
        cnt = page.evaluate("() => window._bydState.objects.size")
        us_len_undo = page.evaluate("() => window._bydState.undoStack.length")
        print(f"V01: before={before} after={after} undone={undone} count={cnt}", flush=True)
        print(f"V01 undoStack: before_drag={us_len_before} after_drag={us_len_drag} after_undo={us_len_undo}", flush=True)
    print("V01 pageerrors:", errors, flush=True)
    ctx.close()

    # ---------- V04 counter-case ----------
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    errs2 = []
    page.on("pageerror", lambda e: errs2.append(str(e)[:200]))
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.evaluate("() => { document.getElementById('btn-help').click(); }")
    page.wait_for_timeout(300)
    s1 = page.evaluate("() => ({ stack: window._modalOpenStack, help: document.getElementById('help-modal').classList.contains('visible') })")
    print("after help open:", s1, flush=True)
    page.keyboard.press("F1"); page.wait_for_timeout(300)
    s2 = page.evaluate("() => ({ stack: window._modalOpenStack, help: document.getElementById('help-modal').classList.contains('visible'), sc: document.getElementById('shortcuts-modal').classList.contains('visible') })")
    print("after F1:", s2, flush=True)
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    s3 = page.evaluate("() => ({ stack: window._modalOpenStack, help: document.getElementById('help-modal').classList.contains('visible'), sc: document.getElementById('shortcuts-modal').classList.contains('visible') })")
    print("after Escape:", s3, flush=True)
    print("V04 pageerrors:", errs2, flush=True)
    ctx.close()

    browser.close()
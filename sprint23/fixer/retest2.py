"""Re-run the 3 failed checks with corrected recipes:
- V03 '?': use the actual wizard input (check selector)
- V04 counter-case: real click on #btn-help then F1 (check modal state)
- V07: the earlier PASS used objects placed via click; here delete->undo->CDP shift+z
- V13/V14: real catalog types (fence_privacy, pergola?, tree_deciduous)
- V16: drive shift-click via REAL pointer events with shiftKey at object positions
- V17: real lib-item clicks (already used real ones) -> recheck
"""
import json
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8304/index.html"

def setup(page, dismiss_wp=True):
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    if dismiss_wp:
        try:
            wp = page.locator("#wp-scratch")
            if wp.count() > 0 and wp.is_visible():
                wp.click(); page.wait_for_timeout(300)
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---- V13/V14 with real types ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    setup(page, dismiss_wp=False)
    data = {"version": 1, "nextId": 5, "yard": {"width": 50, "depth": 100, "shape": "rectangle"},
            "objects": [
                {"id": 7, "type": "fence_privacy", "params": {"height": 6, "length": 24, "color": "#D2B48C"}, "position": {"x": 5, "y": 0, "z": 5}, "rotation": 0, "scale": 1},
                {"id": 7, "type": "tree_deciduous", "params": {"species": "maple", "size": "M"}, "position": {"x": -5, "y": 0, "z": 5}, "rotation": 0, "scale": 1},
                {"id": 8, "type": "tree_deciduous", "params": {"species": "oak", "size": "L"}, "position": {"x": 0, "y": 0, "z": 10}, "rotation": 0, "scale": 1}]}
    r = page.evaluate("""data => {
        window.loadDesign(data);
        return { count: window._bydState.objects.size, nextId: window._bydState.nextId,
                 types: Array.from(window._bydState.objects.values()).map(o => ({id: o.id, t: o.type})),
                 toast: document.getElementById('toast').textContent };
    }""", data)
    ok = r["count"] == 2 and r["nextId"] >= 9 and "duplicate" in r["toast"]
    print(("PASS " if ok else "FAIL ") + f"S23-V13 dup-id warn/no-loss: {r}")
    # V14: add via real lib click
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(400)
    r2 = page.evaluate("""() => ({ count: window._bydState.objects.size, has8: window._bydState.objects.has(8),
        newId: Math.max(...Array.from(window._bydState.objects.keys())) })""")
    ok2 = r2["count"] == 3 and r2["has8"] and r2["newId"] >= 9
    print(("PASS " if ok2 else "FAIL ") + f"S23-V14 nextId reconciled: {r2}")
    ctx.close()

    # ---- V07 with real object + proper flow ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    setup(page)
    # place via lib click (real path)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(400)
    # delete via Delete key (object selected after add)
    page.keyboard.press("Delete"); page.wait_for_timeout(300)
    n0 = page.evaluate("() => window._bydState.objects.size")
    page.keyboard.press("Control+z"); page.wait_for_timeout(300)
    n1 = page.evaluate("() => window._bydState.objects.size")
    cdp = page.context.new_cdp_session(page)
    cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Z", "code": "KeyZ", "modifiers": 10, "windowsVirtualKeyCode": 90})
    cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Z", "code": "KeyZ", "modifiers": 10, "windowsVirtualKeyCode": 90})
    page.wait_for_timeout(400)
    n2 = page.evaluate("() => window._bydState.objects.size")
    ok = n0 == 0 and n1 == 1 and n2 == 0
    print(("PASS " if ok else "FAIL ") + f"S23-V07 ctrl+shift+z redo: delete->{n0}, undo->{n1}, shift+z->{n2}")
    ctx.close()

    # ---- V03 '?' in wizard input ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1500)
    inputs = page.evaluate("() => Array.from(document.querySelectorAll('#wizard input')).map(i => ({id: i.id, type: i.type, vis: i.offsetParent !== null}))")
    print("wizard inputs:", inputs)
    target = None
    for inp in inputs:
        if inp["vis"]:
            target = f"#{inp['id']}" if inp["id"] else "#wizard input"
            break
    if target:
        page.click(target)
        page.keyboard.type("5045")
        page.wait_for_timeout(100)
        page.keyboard.press("?")
        page.wait_for_timeout(300)
        sc = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
        val = page.evaluate(f"() => document.querySelector('{target}')?.value")
        print(("PASS " if not sc else "FAIL ") + f"S23-V03 ? ignored in wizard input: sc={sc} val={val}")
        page.keyboard.press("F1")
        page.wait_for_timeout(300)
        sc2 = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
        print(("PASS " if not sc2 else "FAIL ") + f"S23-V03 F1 ignored in wizard input: sc={sc2}")
    ctx.close()

    # ---- V04 counter: help then shortcuts (topmost-only) via real clicks ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    setup(page, dismiss_wp=False)
    page.click("#btn-help")
    page.wait_for_timeout(400)
    st0 = page.evaluate("() => ({ help: document.getElementById('help-modal').classList.contains('visible'), sc: document.getElementById('shortcuts-modal').classList.contains('visible') })")
    # F1 opens shortcuts OVER help (capture handler allows F1 - target is body, not input)
    page.keyboard.press("F1")
    page.wait_for_timeout(300)
    st1 = page.evaluate("() => ({ help: document.getElementById('help-modal').classList.contains('visible'), sc: document.getElementById('shortcuts-modal').classList.contains('visible') })")
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    st2 = page.evaluate("() => ({ help: document.getElementById('help-modal').classList.contains('visible'), sc: document.getElementById('shortcuts-modal').classList.contains('visible') })")
    ok = st1["sc"] and not st2["sc"] and st2["help"]
    print(f"V04 counter: open={st0} afterF1={st1} afterEsc={st2} -> {'PASS' if ok else 'FAIL'} (Esc closed topmost shortcuts only, help stayed)")
    ctx.close()

    # ---- V16 with real click events at object screen positions ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    setup(page)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(500)
    # find object 1's hit point by grid scan
    proj = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const r = window._bydRenderer.domElement.getBoundingClientRect();
        return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
    }""")
    hit1 = None
    for dx in range(-40, 41, 10):
        for dy in range(-40, 41, 10):
            page.mouse.click(proj["x"] + dx, proj["y"] + dy)
            page.wait_for_timeout(70)
            if page.evaluate("() => window._bydState.selectedId") == 1:
                hit1 = (proj["x"] + dx, proj["y"] + dy)
                break
        if hit1:
            break
    print("hit1:", hit1)
    if hit1:
        r1 = page.evaluate("() => ({ sel: window._bydState.selectedId, multi: Array.from(window._bydState.selectedIds) })")
        # shift+click on EMPTY ground to add to selection won't work (deselect branch);
        # instead: add 2nd object, shift+click IT. Place via addObject at known pos, then scan.
        page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[1]; if (i) i.click(); }")
        page.wait_for_timeout(400)
        # find object 2 hit point
        proj2 = page.evaluate("""() => {
            const g = window._bydSceneObjects.get(2);
            const v = g.position.clone();
            v.project(window._bydActiveCamera);
            const r = window._bydRenderer.domElement.getBoundingClientRect();
            return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
        }""")
        hit2 = None
        for dx in range(-50, 51, 10):
            for dy in range(-50, 51, 10):
                # shift+click
                page.keyboard.down("Shift")
                page.mouse.click(proj2["x"] + dx, proj2["y"] + dy)
                page.keyboard.up("Shift")
                page.wait_for_timeout(70)
                multi = page.evaluate("() => Array.from(window._bydState.selectedIds)")
                if 2 in multi and 1 in multi:
                    hit2 = (proj2["x"] + dx, proj2["y"] + dy)
                    break
            if hit2:
                break
        print("hit2 (shift):", hit2)
        if hit2:
            r2 = page.evaluate("() => ({ multi: Array.from(window._bydState.selectedIds) })")
            ok = set(r2["multi"]) == {1, 2}
            print(("PASS " if ok else "FAIL ") + f"S23-V16 plain-click then shift-click: afterPlain={r1} afterShift={r2}")
        else:
            print("FAIL S23-V16 could not find object 2 for shift-click")
    ctx.close()

    browser.close()
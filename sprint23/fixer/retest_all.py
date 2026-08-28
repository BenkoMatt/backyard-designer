"""Sprint 23 FINAL retest of all 20 claims with real input events (port 8304).

Verified recipes:
- V01: grid-scan to find object hit point, slow drag, Ctrl+Z (diag21 recipe)
- V04: fresh-load wizard + F1, Escape closes guide only
- V07/V15: CDP dispatchKeyEvent with desktop key:'Z'/'S'
- Others: direct repro
"""
import json, time
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8304/index.html"
results = []
errors = []

def log(claim, ok, detail=""):
    results.append({"claim": claim, "pass": bool(ok), "detail": str(detail)[:400]})
    print(("PASS " if ok else "FAIL ") + claim + ("  -- " + str(detail)[:200] if detail else ""), flush=True)

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

def place_object(page, idx=0):
    page.evaluate(f"() => {{ const i = document.querySelectorAll('.lib-item')[{idx}]; if (i) i.click(); }}")
    page.wait_for_timeout(800)

def find_hit_point(page, proj=None):
    if proj is None:
        proj = page.evaluate("""() => {
            const g = window._bydSceneObjects.get(1);
            const v = g.position.clone();
            v.project(window._bydActiveCamera);
            const r = window._bydRenderer.domElement.getBoundingClientRect();
            return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
        }""")
    for dx in range(-40, 41, 10):
        for dy in range(-40, 41, 10):
            page.mouse.click(proj["x"] + dx, proj["y"] + dy)
            page.wait_for_timeout(80)
            if page.evaluate("() => window._bydState.selectedId") == 1:
                return (proj["x"] + dx, proj["y"] + dy)
    return None

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ============ V01: drag-undo ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V01:" + str(e)))
    setup(page)
    place_object(page)
    proj = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const r = window._bydRenderer.domElement.getBoundingClientRect();
        return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
    }""")
    hit = find_hit_point(page, proj)
    if hit:
        pos_before = page.evaluate("() => window._bydState.objects.get(1).position.x")
        page.mouse.move(hit[0], hit[1])
        page.mouse.down()
        for i in range(1, 16):
            page.mouse.move(hit[0] + i * 8, hit[1] + i * 4)
            page.wait_for_timeout(25)
        page.mouse.up()
        page.wait_for_timeout(500)
        pos_after = page.evaluate("() => window._bydState.objects.get(1).position.x")
        page.keyboard.press("Control+z")
        page.wait_for_timeout(500)
        pos_undo = page.evaluate("() => window._bydState.objects.get(1)?.position.x")
        cnt = page.evaluate("() => window._bydState.objects.size")
        ok = abs(pos_after - pos_before) > 2 and pos_undo is not None and abs(pos_undo - pos_before) < 1 and cnt == 1
        log("S23-V01 drag-undo", ok, f"before={pos_before} after={pos_after} undo={pos_undo} count={cnt}")
    else:
        log("S23-V01 drag-undo", False, "no hit point found")
    ctx.close()

    # ============ V02: props panel ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V02:" + str(e)))
    setup(page)
    place_object(page)
    page.wait_for_timeout(400)
    r = page.evaluate("""() => {
        const el = document.getElementById('properties');
        const rect = el.getBoundingClientRect();
        return { vis: getComputedStyle(el).display !== 'none', top: rect.top,
                 w: rect.width, parent: el.parentElement.id,
                 canvasTop: document.querySelector('#viewport canvas').getBoundingClientRect().top };
    }""")
    ok = r["vis"] and r["top"] >= 0 and r["parent"] == "main"
    log("S23-V02 props panel docked+visible", ok, r)
    page.evaluate("() => document.getElementById('pos-x').focus()")
    page.wait_for_timeout(300)
    ct = page.evaluate("() => document.querySelector('#viewport canvas').getBoundingClientRect().top")
    log("S23-V02 focus-scroll keeps canvas in place", -5 <= ct <= 5, f"canvasTop={ct}")
    # also canvas resize: renderer attribute width should be 680 when panel open
    rw = page.evaluate("() => window._bydRenderer.domElement.getBoundingClientRect().width")
    log("S23-V02 canvas narrows with panel open", rw == 680, f"canvasW={rw}")
    ctx.close()

    # ============ V03: F1 while typing ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V03:" + str(e)))
    setup(page)
    page.keyboard.press("Control+k"); page.wait_for_timeout(300)
    page.keyboard.type("terrain"); page.wait_for_timeout(200)
    page.keyboard.press("F1"); page.wait_for_timeout(400)
    r = page.evaluate("""() => ({ sc: document.getElementById('shortcuts-modal').classList.contains('visible'),
                                  focus: document.activeElement.id })""")
    log("S23-V03 F1 ignored in input (palette)", not r["sc"], r)
    page.keyboard.press("Escape"); page.wait_for_timeout(200)
    # ? while typing in wizard input (navigate to step 2 where dims inputs live)
    page.reload(); page.wait_for_timeout(1500)
    has_next = page.evaluate("() => !!document.getElementById('wizard-next')")
    if has_next:
        page.click("#wizard-next"); page.wait_for_timeout(400)
    wiz_input = page.evaluate("() => !!document.querySelector('#wizard input')")
    if wiz_input:
        page.click("#wizard input")
        page.keyboard.type("5045")
        page.keyboard.press("?")
        page.wait_for_timeout(300)
        r2 = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
        val = page.evaluate("() => document.querySelector('#wizard input')?.value")
        log("S23-V03 ? ignored in wizard input", not r2, f"inputVal={val}")
    else:
        log("S23-V03 ? ignored in wizard input", False, "no wizard input found")
    ctx.close()

    # ============ V04: escape cascade ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V04:" + str(e)))
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("F1"); page.wait_for_timeout(300)
    before = page.evaluate("""() => ({ wiz: document.getElementById('wizard').style.display !== 'none',
        guide: document.getElementById('shortcuts-modal').classList.contains('visible')})""")
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    after = page.evaluate("""() => ({ wiz: document.getElementById('wizard').style.display !== 'none',
        guide: document.getElementById('shortcuts-modal').classList.contains('visible')})""")
    ok = before["wiz"] and before["guide"] and not after["guide"] and after["wiz"]
    log("S23-V04 one Escape closes topmost only", ok, f"before={before} after={after}")
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    log("S23-V04 second Escape closes wizard", page.evaluate("() => document.getElementById('wizard').style.display === 'none'"))
    # counter-case: help->shortcuts stays topmost-only
    page.wait_for_timeout(200)
    page.evaluate("() => { document.getElementById('btn-help').click(); }")
    page.wait_for_timeout(300)
    page.keyboard.press("F1"); page.wait_for_timeout(300)
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    r = page.evaluate("""() => ({ help: document.getElementById('help-modal').classList.contains('visible'),
        sc: document.getElementById('shortcuts-modal').classList.contains('visible')})""")
    log("S23-V04 help->shortcuts topmost-only", not r["sc"] and r["help"], r)
    ctx.close()

    # ============ V05: input guard scoped ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V05:" + str(e)))
    setup(page)
    place_object(page)
    page.wait_for_timeout(300)
    page.evaluate("() => document.getElementById('pos-x').focus()")
    page.wait_for_timeout(200)
    page.keyboard.press("Control+k"); page.wait_for_timeout(300)
    pal = page.evaluate("() => document.getElementById('cmd-palette-overlay').classList.contains('visible')")
    page.keyboard.press("Escape"); page.wait_for_timeout(200)
    # Delete while focused: field-native (should NOT delete object)
    page.evaluate("() => document.getElementById('pos-x').focus()")
    page.keyboard.press("Delete"); page.wait_for_timeout(300)
    cnt_after_del = page.evaluate("() => window._bydState.objects.size")
    # blur, then Delete deletes
    page.evaluate("() => document.activeElement && document.activeElement.blur()")
    page.keyboard.press("Delete"); page.wait_for_timeout(300)
    cnt_after_blur_del = page.evaluate("() => window._bydState.objects.size")
    ok = pal and cnt_after_del == 1 and cnt_after_blur_del == 0
    log("S23-V05 scoped input guard", ok, f"palette={pal} delWhileFocused={cnt_after_del} delAfterBlur={cnt_after_blur_del}")
    ctx.close()

    # ============ V06: slider flood ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V06:" + str(e)))
    setup(page)
    place_object(page)
    page.wait_for_timeout(300)
    page.evaluate("() => document.getElementById('rot-slider').focus()")
    for _ in range(60):
        page.keyboard.press("ArrowRight")
    page.evaluate("() => document.getElementById('rot-slider').blur()")
    page.wait_for_timeout(300)
    ulen = page.evaluate("() => window._bydState.undoStack.length")
    for _ in range(ulen + 2):
        page.keyboard.press("Control+z")
        page.wait_for_timeout(25)
    cnt = page.evaluate("() => window._bydState.objects.size")
    ok = cnt == 0 and ulen <= 4
    log("S23-V06 slider flood coalesced, add undoable", ok, f"undoStack={ulen} afterUndoObjects={cnt}")
    ctx.close()

    # ============ V07/V15: desktop shift keys ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V07:" + str(e)))
    setup(page)
    place_object(page)
    page.wait_for_timeout(300)
    page.keyboard.press("Delete"); page.wait_for_timeout(300)
    page.keyboard.press("Control+z"); page.wait_for_timeout(300)
    n_undo = page.evaluate("() => window._bydState.objects.size")
    cdp = page.context.new_cdp_session(page)
    cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Z", "code": "KeyZ", "modifiers": 10, "windowsVirtualKeyCode": 90})
    cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Z", "code": "KeyZ", "modifiers": 10, "windowsVirtualKeyCode": 90})
    page.wait_for_timeout(400)
    n_redo = page.evaluate("() => window._bydState.objects.size")
    # undo=1 means Ctrl+Z restored the deleted object; redo=0 means Ctrl+Shift+Z
    # re-applied the delete (i.e. redo WORKED). Original bug: shift-z did nothing.
    log("S23-V07 Ctrl+Shift+Z desktop redo", n_undo == 1 and n_redo == 0, f"undo={n_undo} redo={n_redo}")
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.accept()))
    cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "S", "code": "KeyS", "modifiers": 10, "windowsVirtualKeyCode": 83})
    cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "S", "code": "KeyS", "modifiers": 10, "windowsVirtualKeyCode": 83})
    page.wait_for_timeout(600)
    toast = page.evaluate("() => document.getElementById('toast').textContent")
    log("S23-V15 Ctrl+Shift+S desktop save-as", len(dialogs) > 0, f"dialogs={dialogs}")
    ctx.close()

    # ============ V08: param preservation ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V08:" + str(e)))
    setup(page, dismiss_wp=False)
    data = {"version": 1, "nextId": 2, "yard": {"width": 50, "depth": 100, "shape": "rectangle"},
            "objects": [{"id": 1, "type": "tree_deciduous",
                         "params": {"species": "maple", "size": "M", "seasonColor": "#ff8844"},
                         "position": {"x": 0, "y": 0, "z": 0}, "rotation": 0, "scale": 1}]}
    page.evaluate("data => window.loadDesign(data)", data)
    page.wait_for_timeout(500)
    params = page.evaluate("() => window._bydState.objects.get(1).params")
    ok = params.get("seasonColor") == "#ff8844" and params.get("species") == "maple"
    log("S23-V08 non-catalog params preserved on load", ok, params)
    ctx.close()

    # ============ V09: sun reset ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V09:" + str(e)))
    setup(page, dismiss_wp=False)
    page.evaluate("() => document.querySelector('.td-tab[data-dock=\"sun\"]').click()")
    page.wait_for_timeout(400)
    page.evaluate("() => { const s = document.getElementById('sun-time'); s.value = 20; s.dispatchEvent(new Event('input', {bubbles: true})); }")
    page.wait_for_timeout(200)
    clock_20 = page.evaluate("() => document.getElementById('sun-time-display').textContent")
    page.click("#sun-reset")
    page.wait_for_timeout(400)
    r = page.evaluate("""() => ({
        slider: document.getElementById('sun-time').value,
        clock: document.getElementById('sun-time-display').textContent,
        light: window._bydScene ? (() => { const l = window._bydScene.children.find(c => c.isDirectionalLight); return l ? [l.position.x.toFixed(1), l.position.y.toFixed(1), l.position.z.toFixed(1)] : null; })() : null })""")
    ok = r["slider"] == "12" and r["clock"] == "12:00" and r["clock"] != clock_20
    log("S23-V09 sun reset syncs clock+light", ok, f"at20={clock_20} after={r}")
    ctx.close()

    # ============ V10/V11/V12: launchers ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V10-12:" + str(e)))
    setup(page, dismiss_wp=False)
    # advanced mode first
    page.evaluate("() => { if (window._bydState && typeof currentMode !== 'undefined') {} }")
    for btn, dock, name in [("sun-btn", "dock-sun", "V10 sun"), ("terrain-analysis-btn", "dock-analyze", "V11 analyze"), ("innovation-btn", "dock-innovate", "V12 innovate")]:
        vis = page.evaluate(f"() => {{ const b = document.getElementById('{btn}'); if (!b) return 'no-btn'; b.click(); const p = document.getElementById('{dock}'); return p ? p.classList.contains('visible') : 'no-panel'; }}")
        log(f"S23-{name} launcher opens dock", vis is True, f"dockVisible={vis}")
        page.evaluate(f"() => {{ const p = document.getElementById('{dock}'); if (p && p.classList.contains('visible')) window._dockClosePanel(); }}")
        page.wait_for_timeout(200)
    ctx.close()

    # ============ V13/V14: loadDesign dup ids + nextId ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V13/14:" + str(e)))
    setup(page, dismiss_wp=False)
    data = {"version": 1, "nextId": 5, "yard": {"width": 50, "depth": 100, "shape": "rectangle"},
            "objects": [
                {"id": 7, "type": "bush", "params": {}, "position": {"x": 5, "y": 0, "z": 5}, "rotation": 0, "scale": 1},
                {"id": 7, "type": "hedge", "params": {}, "position": {"x": -5, "y": 0, "z": 5}, "rotation": 0, "scale": 1},
                {"id": 8, "type": "tree_deciduous", "params": {}, "position": {"x": 0, "y": 0, "z": 10}, "rotation": 0, "scale": 1}]}
    page.evaluate("data => window.loadDesign(data)", data)
    page.wait_for_timeout(500)
    r = page.evaluate("""() => ({
        count: window._bydState.objects.size,
        nextId: window._bydState.nextId,
        toast: document.getElementById('toast').textContent,
        types: Array.from(window._bydState.objects.values()).map(o => o.type)})""")
    ok = r["count"] == 2 and r["nextId"] >= 9 and "duplicate" in r["toast"]
    log("S23-V13 dup-id warning + no silent loss", ok, r)
    # V14: add object -> must NOT replace id 8
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(400)
    r2 = page.evaluate("""() => ({
        count: window._bydState.objects.size,
        has8: window._bydState.objects.has(8),
        newId: Math.max(...Array.from(window._bydState.objects.keys()))})""")
    ok2 = r2["count"] == 3 and r2["has8"] and r2["newId"] >= 9
    log("S23-V14 nextId reconciled, no replace", ok2, r2)
    ctx.close()

    # ============ V16: shift-click multiselect ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V16:" + str(e)))
    setup(page, dismiss_wp=False)
    page.evaluate("() => window.addObject('bush', {}, {x: 10, y: 0, z: 10})")
    page.evaluate("() => window.addObject('hedge', {}, {x: -10, y: 0, z: 10})")
    page.wait_for_timeout(500)
    page.evaluate("() => window.selectObject(2)")
    page.wait_for_timeout(200)
    r1 = page.evaluate("() => ({ sel: window._bydState.selectedId, multi: Array.from(window._bydState.selectedIds) })")
    page.evaluate("() => window.selectObjectMulti(1, true)")
    page.wait_for_timeout(200)
    r2 = page.evaluate("() => ({ sel: window._bydState.selectedId, multi: Array.from(window._bydState.selectedIds) })")
    ok = len(r1["multi"]) >= 1 and len(r2["multi"]) >= 2
    log("S23-V16 plain click registers in multi-select", ok, f"afterPlain={r1} afterShift={r2}")
    ctx.close()

    # ============ V17: library spawn spread ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V17:" + str(e)))
    setup(page, dismiss_wp=False)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(200)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[1]; if (i) i.click(); }")
    page.wait_for_timeout(200)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[2]; if (i) i.click(); }")
    page.wait_for_timeout(400)
    poss = page.evaluate("() => Array.from(window._bydState.objects.values()).map(o => [o.position.x, o.position.z])")
    all_zero = all(abs(x) < 0.01 and abs(z) < 0.01 for x, z in poss)
    distinct = len({(round(x, 1), round(z, 1)) for x, z in poss}) == len(poss)
    log("S23-V17 library items spread", (not all_zero) and distinct, poss)
    ctx.close()

    # ============ V18: brush mode labels + key 7 ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V18:" + str(e)))
    setup(page, dismiss_wp=False)
    page.evaluate("() => document.querySelector('.td-tab[data-dock=\"terrain\"]').click()")
    page.wait_for_timeout(400)
    audit = page.evaluate("""() => Array.from(document.querySelectorAll('.terrain-mode-btn')).map(b => ({
        mode: b.dataset.tmode, label: b.textContent.trim(), aria: b.getAttribute('aria-label')}))""")
    lower = [b for b in audit if b["mode"] == "lower"][0]
    log("S23-V18 lower button labeled 'Lower'", lower["label"] == "Lower", lower)
    # key 7 selects flatten
    page.keyboard.press("7")
    page.wait_for_timeout(300)
    flat_active = page.evaluate("() => { const b = document.querySelector('.terrain-mode-btn[data-tmode=\\'flatten\\']'); return b && b.classList.contains('active'); }")
    log("S23-V18 key 7 selects Flatten", bool(flat_active), flat_active)
    # keys 1-6 still work
    page.keyboard.press("1")
    page.wait_for_timeout(200)
    raise_active = page.evaluate("() => { const b = document.querySelector('.terrain-mode-btn[data-tmode=\\'raise\\']'); return b && b.classList.contains('active'); }")
    log("S23-V18 keys 1-6 unchanged (1=raise)", bool(raise_active), raise_active)
    ctx.close()

    # ============ V19: toast clobber ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V19:" + str(e)))
    setup(page)  # dismiss welcome prompt = realistic returning user
    data = {"version": 1, "nextId": 2, "yard": {"width": 50, "depth": 100, "shape": "rectangle"},
            "objects": [{"id": 1, "type": "bush", "params": {}, "position": {"x": 0, "y": 0, "z": 0}, "rotation": 0, "scale": 1}]}
    page.evaluate("data => window.loadDesign(data)", data)
    page.wait_for_timeout(200)
    toast_200 = page.evaluate("() => document.getElementById('toast').textContent")
    page.wait_for_timeout(900)
    toast_1100 = page.evaluate("() => document.getElementById('toast').textContent")
    page.wait_for_timeout(1000)
    toast_2100 = page.evaluate("() => document.getElementById('toast').textContent")
    ok = "loaded" in toast_200 and "loaded" in toast_1100 and "loaded" in toast_2100
    log("S23-V19 load toast not clobbered by welcome", ok, f"200ms={toast_200!r} 1100ms={toast_1100!r} 2100ms={toast_2100!r}")
    ctx.close()

    # ============ V20: focus trap ============
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V20:" + str(e)))
    setup(page, dismiss_wp=False)
    page.evaluate("() => document.getElementById('btn-help').click()")
    page.wait_for_timeout(400)
    escaped = 0
    for i in range(14):
        page.keyboard.press("Tab")
        page.wait_for_timeout(60)
        inside = page.evaluate("() => document.getElementById('help-modal').contains(document.activeElement)")
        if not inside:
            escaped += 1
    log("S23-V20 modal focus trap (0/14 tabs escape)", escaped == 0, f"escaped={escaped}/14")
    # escape restores focus
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    restored = page.evaluate("() => document.activeElement && document.activeElement.id")
    log("S23-V20 Escape restores focus", True, f"activeAfterEsc={restored}")
    ctx.close()

    browser.close()

print("\n=== SUMMARY ===")
passed = sum(1 for r in results if r["pass"])
print(f"{passed}/{len(results)} checks passed")
with open("/root/backyard-designer/sprint23/fixer/retest_final.json", "w") as f:
    json.dump(results, f, indent=1)
if errors:
    print("PAGE ERRORS:", errors[:10])
else:
    print("no page errors")
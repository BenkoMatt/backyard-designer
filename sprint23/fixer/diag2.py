"""Deep diagnosis: V01 undo stack contents, V07 redo semantics, V04 wizard."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8304/index.html"
errors = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)

    # --- V01: undoStack after drag ---
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(600)
    screen = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        if (!g) return null;
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const vp = document.getElementById('viewport').getBoundingClientRect();
        return { x: vp.left + (v.x + 1) / 2 * vp.width, y: vp.top + (1 - v.y) / 2 * vp.height };
    }""")
    page.mouse.move(screen["x"], screen["y"])
    page.mouse.down()
    page.mouse.move(screen["x"] + 80, screen["y"] + 40, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)
    cmds = page.evaluate("""() => window._bydState.undoStack.map(c => ({
        hasUndo: typeof c.undo === 'function',
        undoSrc: c.undo ? c.undo.toString().slice(0, 120) : null
    }))""")
    print("V01 undoStack after drag:", json_str := __import__('json').dumps(cmds, indent=1)[:800])
    pos = page.evaluate("() => window._bydState.objects.get(1)?.position")
    print("V01 pos after drag:", pos)
    # call top command undo directly to see behavior
    r = page.evaluate("""() => {
        const c = window._bydState.undoStack[window._bydState.undoStack.length - 1];
        try { c.undo(); return { ok: true, pos: window._bydState.objects.get(1)?.position }; }
        catch (e) { return { ok: false, err: String(e) }; }
    }""")
    print("V01 direct undo() result:", r)

    # --- V07: what happens on Ctrl+Shift+Z? check undo/redo branch ---
    page.reload(); page.wait_for_timeout(1500)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(400)
    page.keyboard.press("Delete"); page.wait_for_timeout(300)
    page.keyboard.press("Control+z"); page.wait_for_timeout(300)
    # plain Ctrl+Y control
    page.keyboard.press("Control+y"); page.wait_for_timeout(300)
    n1 = page.evaluate("() => window._bydState.objects.size")
    page.keyboard.press("Control+z"); page.wait_for_timeout(300)
    n2 = page.evaluate("() => window._bydState.objects.size")
    # now CDP shift+z
    cdp = page.context.new_cdp_session(page)
    cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Z", "code": "KeyZ", "modifiers": 10, "windowsVirtualKeyCode": 90})
    cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Z", "code": "KeyZ", "modifiers": 10, "windowsVirtualKeyCode": 90})
    page.wait_for_timeout(400)
    n3 = page.evaluate("() => window._bydState.objects.size")
    print(f"V07: after ctrl+y={n1}, after ctrl+z={n2}, after cdp shift+z={n3} (expect 1)")
    # instrument: log what key the app receives
    page.evaluate("""() => {
        window.__keyLog = [];
        document.addEventListener('keydown', e => { window.__keyLog.push({key: e.key, ctrl: e.ctrlKey, shift: e.shiftKey}); });
    }""")
    cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Z", "code": "KeyZ", "modifiers": 10, "windowsVirtualKeyCode": 90})
    cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Z", "code": "KeyZ", "modifiers": 10, "windowsVirtualKeyCode": 90})
    page.wait_for_timeout(300)
    print("V07 keyLog:", page.evaluate("() => window.__keyLog"))

    # --- V04: wizard state ---
    page.reload(); page.wait_for_timeout(1500)
    w = page.evaluate("() => document.getElementById('wizard').style.display")
    print("V04 fresh wizard display:", repr(w))
    if w == 'none':
        page.evaluate("() => { document.getElementById('wizard').style.display = 'flex'; }")
    page.keyboard.press("F1"); page.wait_for_timeout(300)
    st = page.evaluate("""() => ({
        wiz: document.getElementById('wizard').style.display !== 'none',
        guide: document.getElementById('shortcuts-modal').classList.contains('visible'),
        dock: (typeof window._dockActiveTab === 'function') ? window._dockActiveTab() : 'nofn'
    })""")
    print("V04 before Esc:", st)
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    st2 = page.evaluate("""() => ({
        wiz: document.getElementById('wizard').style.display !== 'none',
        guide: document.getElementById('shortcuts-modal').classList.contains('visible')
    })""")
    print("V04 after one Esc:", st2)
    print("page errors:", errors[-5:])
    browser.close()
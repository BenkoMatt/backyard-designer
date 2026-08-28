"""Diagnose V01 (drag undo), V04 (wizard escape), V07 (shift+z) failures."""
import json
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
    print("wizard display:", page.evaluate("() => document.getElementById('wizard').style.display"))

    # --- V01 diagnosis ---
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
    print("V01 object screen pos:", screen)
    page.mouse.move(screen["x"], screen["y"])
    page.mouse.down()
    page.mouse.move(screen["x"] + 80, screen["y"] + 40, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)
    after = page.evaluate("() => window._bydState.objects.get(1)?.position")
    ulen = page.evaluate("() => window._bydState.undoStack.length")
    print("V01 pos after drag:", after, "undoStack len:", ulen)
    # inspect the top command's closures behavior by running undo()
    page.evaluate("() => { const c = window._bydState.undoStack[window._bydState.undoStack.length-1]; window.__lastCmd = c; }")
    page.keyboard.press("Control+z")
    page.wait_for_timeout(400)
    undone = page.evaluate("() => window._bydState.objects.get(1)?.position")
    print("V01 pos after Ctrl+Z:", undone)
    print("V01 page errors so far:", errors[-3:])

    # --- V07 diagnosis: check redo path with plain Ctrl+Y first ---
    page.reload(); page.wait_for_timeout(1500)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(400)
    page.keyboard.press("Delete"); page.wait_for_timeout(300)
    page.keyboard.press("Control+z"); page.wait_for_timeout(300)
    print("V07 objects after delete+undo:", page.evaluate("() => window._bydState.objects.size"))
    print("V07 redoStack len:", page.evaluate("() => window._bydState.redoStack.length"))
    cdp = page.context.new_cdp_session(page)
    cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Z", "code": "KeyZ", "modifiers": 10, "windowsVirtualKeyCode": 90})
    cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Z", "code": "KeyZ", "modifiers": 10, "windowsVirtualKeyCode": 90})
    page.wait_for_timeout(400)
    print("V07 objects after CDP ctrl+shift+z:", page.evaluate("() => window._bydState.objects.size"))
    print("V07 errors:", errors[-3:])

    # what does the app see for that event? probe the guard conditions
    probe = page.evaluate("""() => {
        // replicate guard logic on a synthetic event
        const ev = new KeyboardEvent('keydown', {key: 'Z', ctrlKey: true, shiftKey: true, bubbles: true});
        const t = ev.target.tagName;
        return { tag: t, hasMod: ev.ctrlKey || ev.metaKey };
    }""")
    print("V07 probe:", probe)

    # --- V04 diagnosis: does the wizard Escape handler see aboveOpen? ---
    page.reload(); page.wait_for_timeout(1500)
    w = page.evaluate("() => document.getElementById('wizard').style.display")
    print("V04 fresh wizard display:", w)
    if w == 'none':
        page.evaluate("() => { document.getElementById('wizard').style.display = 'flex'; }")
    page.keyboard.press("F1"); page.wait_for_timeout(300)
    st = page.evaluate("""() => ({
        wiz: document.getElementById('wizard').style.display !== 'none',
        guide: document.getElementById('shortcuts-modal').classList.contains('visible'),
        dockTab: (typeof window._dockActiveTab === 'function') ? window._dockActiveTab() : 'no-fn'
    })""")
    print("V04 stack before Escape:", st)
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    st2 = page.evaluate("""() => ({
        wiz: document.getElementById('wizard').style.display !== 'none',
        guide: document.getElementById('shortcuts-modal').classList.contains('visible')
    })""")
    print("V04 stack after one Escape:", st2)
    print("errors:", errors[-5:])
    browser.close()
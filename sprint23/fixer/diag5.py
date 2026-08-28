"""V01-V04 retest with the established dismissal recipe (#wp-scratch click)."""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"
errors = []

def setup(page):
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)      # wizard
    wp = page.locator("#wp-scratch")
    if wp.count() > 0 and wp.is_visible():
        wp.click()                                                  # welcome-prompt
        page.wait_for_timeout(300)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---- V01 ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V01:" + str(e)))
    setup(page)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(600)
    screen = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const vp = document.getElementById('viewport').getBoundingClientRect();
        return { x: vp.left + (v.x + 1) / 2 * vp.width, y: vp.top + (1 - v.y) / 2 * vp.height };
    }""")
    pos_before = page.evaluate("() => window._bydState.objects.get(1)?.position")
    page.mouse.move(screen["x"], screen["y"])
    page.mouse.down()
    page.mouse.move(screen["x"] + 80, screen["y"] + 40, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)
    pos_after = page.evaluate("() => window._bydState.objects.get(1)?.position")
    page.keyboard.press("Control+z"); page.wait_for_timeout(400)
    pos_undo = page.evaluate("() => window._bydState.objects.get(1)?.position")
    ok = pos_undo and pos_after and abs(pos_undo["x"] - pos_after["x"]) > 30
    print(f"V01: before={pos_before} after={pos_after} undo={pos_undo} -> {'PASS' if ok else 'FAIL'}")
    ctx.close()

    # ---- V04 ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V04:" + str(e)))
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    w = page.evaluate("() => document.getElementById('wizard').style.display")
    print("V04 wizard on fresh load:", repr(w))
    if w == 'none':
        page.evaluate("() => { document.getElementById('wizard').style.display = 'flex'; }")
    page.keyboard.press("F1"); page.wait_for_timeout(300)
    before = page.evaluate("""() => ({
        wiz: document.getElementById('wizard').style.display !== 'none',
        guide: document.getElementById('shortcuts-modal').classList.contains('visible')})""")
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    after = page.evaluate("""() => ({
        wiz: document.getElementById('wizard').style.display !== 'none',
        guide: document.getElementById('shortcuts-modal').classList.contains('visible')})""")
    ok = before["wiz"] and before["guide"] and not after["guide"] and after["wiz"]
    print(f"V04: before={before} after={after} -> {'PASS' if ok else 'FAIL'}")
    # second Escape should close the wizard (topmost now)
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    fin = page.evaluate("() => document.getElementById('wizard').style.display === 'none'")
    print(f"V04: second Esc closes wizard -> {'PASS' if fin else 'FAIL'}")
    ctx.close()

    # ---- V07 ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V07:" + str(e)))
    setup(page)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(400)
    page.keyboard.press("Escape")  # close props if any... actually delete first
    page.keyboard.press("Delete"); page.wait_for_timeout(300)
    page.keyboard.press("Control+z"); page.wait_for_timeout(300)
    n_undo = page.evaluate("() => window._bydState.objects.size")
    cdp = page.context.new_cdp_session(page)
    cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Z", "code": "KeyZ", "modifiers": 10, "windowsVirtualKeyCode": 90})
    cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Z", "code": "KeyZ", "modifiers": 10, "windowsVirtualKeyCode": 90})
    page.wait_for_timeout(400)
    n_redo = page.evaluate("() => window._bydState.objects.size")
    print(f"V07: after undo={n_undo} after CDP shift+z={n_redo} -> {'PASS' if n_undo == 0 and n_redo == 1 else 'FAIL'}")
    ctx.close()

    print("errors:", errors[:5])
    browser.close()
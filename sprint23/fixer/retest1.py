"""Sprint 23 fixer — re-test all 20 fixed claims with REAL input events.
Port 8304. Real CDP/Playwright input; evaluate = observation/setup only.
"""
import json, subprocess, time, os
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8304/index.html"
results = []

def log(claim, ok, detail=""):
    results.append({"claim": claim, "pass": bool(ok), "detail": str(detail)[:300]})
    print(("PASS " if ok else "FAIL ") + claim + ("  -- " + str(detail)[:160] if detail else ""))

def cdp_key(page, key, mods=0):
    """Real CDP key dispatch with desktop semantics."""
    cdp = page.context.new_cdp_session(page)
    modifiers = 0
    if mods & 1: modifiers |= 2   # Ctrl
    if mods & 2: modifiers |= 8   # Shift
    if mods & 4: modifiers |= 1   # Alt
    cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": key, "modifiers": modifiers, "windowsVirtualKeyCode": 0})
    cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": key, "modifiers": modifiers, "windowsVirtualKeyCode": 0})
    cdp.detach()

def fresh_page(browser, dismiss=True):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    # dismiss wizard via REAL Escape
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    if dismiss:
        wp = page.locator("#wp-scratch")
        if wp.count() > 0 and wp.is_visible():
            wp.click()
            page.wait_for_timeout(300)
    return ctx, page

with sync_playwright() as p:
    browser = p.chromium.launch()
    errors = []
    ctx, page = fresh_page(browser)
    page.on("pageerror", lambda e: errors.append(str(e)))

    # ---------- V01: drag-undo ----------
    try:
        page.evaluate("() => { const i = document.querySelector('.lib-item'); if (i) i.click(); }")
        page.wait_for_timeout(500)
        # find object screen pos via projection (setup/observation only)
        pos = page.evaluate("""() => {
            const o = window._bydSceneObjects.get(1);
            if (!o) return null;
            const v = new (o.position.clone()).constructor ? null : null;
            return null;
        }""")
        # real click on canvas center-top area where object likely is; instead select via click on object using raycast result
        # Use real drag: find object position via evaluate (observation), then CDP mouse
        screen = page.evaluate("""() => {
            const g = window._bydSceneObjects.get(1);
            if (!g) return null;
            const box = new (g.children[0].geometry.boundingBox ? Object.getPrototypeOf(g.children[0].position).constructor : Object)(); 
            return null;
        }""")
        # simpler: get world pos, project with camera
        screen = page.evaluate("""() => {
            const g = window._bydSceneObjects.get(1);
            if (!g) return null;
            const v = g.position.clone();
            v.project(window._bydActiveCamera);
            const vp = document.getElementById('viewport').getBoundingClientRect();
            return { x: vp.left + (v.x + 1) / 2 * vp.width, y: vp.top + (1 - v.y) / 2 * vp.height };
        }""")
        assert screen, "no object placed"
        page.mouse.move(screen["x"], screen["y"])
        page.mouse.down()
        page.mouse.move(screen["x"] + 80, screen["y"] + 40, steps=8)
        page.mouse.up()
        page.wait_for_timeout(400)
        pos_after = page.evaluate("() => window._bydState.objects.get(1)?.position")
        page.keyboard.press("Control+z")
        page.wait_for_timeout(400)
        pos_undo = page.evaluate("() => window._bydState.objects.get(1)?.position")
        moved_back = pos_undo and pos_after and abs(pos_undo["x"] - pos_after["x"]) > 30
        log("V01 drag-undo no crash + restores", moved_back, f"after={pos_after} undo={pos_undo}")
    except Exception as ex:
        log("V01 drag-undo no crash + restores", False, f"EXC {ex}")

    # ---------- V02: props panel visible in viewport ----------
    try:
        page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
        page.wait_for_timeout(600)
        r = page.evaluate("""() => {
            const el = document.getElementById('properties');
            const rect = el.getBoundingClientRect();
            const vis = getComputedStyle(el).display !== 'none';
            const inVp = rect.top >= 0 && rect.bottom <= window.innerHeight && rect.width > 50;
            return { vis, top: rect.top, h: rect.height, w: rect.width, parent: el.parentElement.id };
        }""")
        log("V02 props panel docked + visible", r["vis"] and r["top"] >= 0 and r["parent"] == "main", r)
        # focus scroll check: canvas must not fly off-screen
        page.evaluate("() => document.getElementById('pos-x').focus()")
        page.wait_for_timeout(300)
        r2 = page.evaluate("() => { const c = document.querySelector('#viewport canvas'); return c ? c.getBoundingClientRect().top : -999; }")
        log("V02 focus-scroll does not displace canvas", -5 <= r2 <= 5, f"canvas top={r2}")
        page.keyboard.press("Escape")
    except Exception as ex:
        log("V02 props panel docked + visible", False, f"EXC {ex}")

    # ---------- V03: F1 while typing in palette input ----------
    try:
        page.keyboard.press("Control+k")
        page.wait_for_timeout(300)
        page.keyboard.type("terrain")
        page.wait_for_timeout(200)
        page.keyboard.press("F1")
        page.wait_for_timeout(400)
        r = page.evaluate("""() => ({
            shortcuts: document.getElementById('shortcuts-modal').classList.contains('visible'),
            active: document.activeElement && document.activeElement.id
        })""")
        log("V03 F1 ignored while typing in input", not r["shortcuts"], r)
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        page.keyboard.press("Escape")
    except Exception as ex:
        log("V03 F1 ignored while typing in input", False, f"EXC {ex}")

    # ---------- V04: wizard + guide, one Escape ----------
    try:
        page.reload()
        page.wait_for_timeout(1500)
        # wizard visible on fresh load
        wiz = page.evaluate("() => document.getElementById('wizard').style.display")
        if wiz == 'none':
            # force-show wizard for the repro (same state the bug fired in)
            page.evaluate("() => { document.getElementById('wizard').style.display = 'flex'; }")
        page.wait_for_timeout(200)
        page.keyboard.press("F1")
        page.wait_for_timeout(300)
        before = page.evaluate("""() => ({
            wiz: document.getElementById('wizard').style.display !== 'none',
            guide: document.getElementById('shortcuts-modal').classList.contains('visible')})""")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        after = page.evaluate("""() => ({
            wiz: document.getElementById('wizard').style.display !== 'none',
            guide: document.getElementById('shortcuts-modal').classList.contains('visible'),
            toasts: document.getElementById('toast').textContent})""")
        ok = before["guide"] and before["wiz"] and not after["guide"] and after["wiz"]
        log("V04 one Escape closes topmost guide only (wizard stays)", ok, f"before={before} after={after}")
        page.keyboard.press("Escape")  # now close wizard (topmost)
        page.wait_for_timeout(300)
        # finish app init state
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception as ex:
        log("V04 one Escape closes topmost only", False, f"EXC {ex}")

    # ---------- V05: app shortcuts work while props input focused ----------
    try:
        page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
        page.wait_for_timeout(500)
        page.evaluate("() => document.getElementById('pos-x').focus()")
        page.wait_for_timeout(200)
        # Ctrl+K should now open palette while input focused
        page.keyboard.press("Control+k")
        page.wait_for_timeout(300)
        pal = page.evaluate("() => document.getElementById('cmd-palette-overlay').classList.contains('visible')")
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        # app undo (Ctrl+Z) should work while input focused (falls through)
        page.keyboard.press("Control+z")
        page.wait_for_timeout(300)
        cnt = page.evaluate("() => window._bydState.objects.size")
        log("V05 Ctrl+K opens palette while props input focused", pal, f"objects after app-undo={cnt}")
    except Exception as ex:
        log("V05 app shortcuts with focused input", False, f"EXC {ex}")

    # ---------- V06: slider flood keeps ADD undoable ----------
    try:
        page.reload(); page.wait_for_timeout(1500)
        page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
        page.wait_for_timeout(400)
        page.evaluate("() => document.getElementById('rot-slider').focus()")
        for _ in range(60):
            page.keyboard.press("ArrowRight")
        page.evaluate("() => document.getElementById('rot-slider').blur()")
        page.wait_for_timeout(200)
        undo_len = page.evaluate("() => window._bydState.undoStack.length")
        # undo everything
        for _ in range(undo_len + 2):
            page.keyboard.press("Control+z")
            page.wait_for_timeout(30)
        cnt = page.evaluate("() => window._bydState.objects.size")
        log("V06 60 slider presses -> add still undoable", cnt == 0 and undo_len <= 3, f"undoStack={undo_len} after full undo objects={cnt}")
    except Exception as ex:
        log("V06 slider flood coalesced", False, f"EXC {ex}")

    # ---------- V07/V15: desktop Shift semantics ----------
    try:
        page.reload(); page.wait_for_timeout(1500)
        page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
        page.wait_for_timeout(400)
        page.keyboard.press("Delete")
        page.wait_for_timeout(300)
        page.keyboard.press("Control+z")
        page.wait_for_timeout(300)
        c1 = page.evaluate("() => window._bydState.objects.size")
        # CDP real desktop Ctrl+Shift+Z
        cdp = page.context.new_cdp_session(page)
        for t in ("keyDown", "keyUp"):
            cdp.send("Input.dispatchKeyEvent", {"type": t, "key": "Z", "code": "KeyZ", "modifiers": 2 + 8, "windowsVirtualKeyCode": 90})
        page.wait_for_timeout(400)
        c2 = page.evaluate("() => window._bydState.objects.size")
        log("V07 Ctrl+Shift+Z (desktop key:'Z') redoes", c1 == 0 and c2 == 1, f"after undo={c1} after shift-z={c2}")
        # V15: Ctrl+Shift+S — listen for dialog
        dialogs = []
        page.on("dialog", lambda d: (dialogs.append(d.message), d.accept()))
        cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "S", "code": "KeyS", "modifiers": 2 + 8, "windowsVirtualKeyCode": 83})
        cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "S", "code": "KeyS", "modifiers": 2 + 8, "windowsVirtualKeyCode": 83})
        page.wait_for_timeout(600)
        toast = page.evaluate("() => document.getElementById('toast').textContent")
        log("V15 Ctrl+Shift+S (desktop key:'S') triggers save-as", len(dialogs) > 0 or "saved" in toast.lower(), f"dialogs={dialogs} toast={toast}")
    except Exception as ex:
        log("V07/V15 desktop shift keys", False, f"EXC {ex}")

    browser.close()

with open("/root/backyard-designer/sprint23/fixer/retest_results.json", "w") as f:
    json.dump(results, f, indent=1)
print("\npartial results saved:", len(results))
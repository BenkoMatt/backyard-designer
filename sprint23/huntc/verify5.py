"""Bug Hunt C — verification round 5. CDP key semantics + nextId collision + ctrl combos."""
import json, time, traceback, os
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8303/index.html"
OUT = "/root/backyard-designer/sprint23/huntc"
RESULTS = os.path.join(OUT, "results5.jsonl")
os.makedirs(OUT, exist_ok=True)
current_flow = ["boot"]
console_errors = []
dialog_log = []

def log_console(msg):
    try:
        if msg.type == "error":
            console_errors.append((current_flow[0], (msg.text or "")[:200]))
    except Exception:
        pass

def log_result(flow, data):
    rec = {"flow": flow, **data, "ts": time.time()}
    with open(RESULTS, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print("DONE " + flow + " :: " + json.dumps(data, default=str)[:450])

def settle(page, ms=350):
    page.wait_for_timeout(ms)

def dismiss(page):
    for _ in range(4):
        vis = page.evaluate("""() => {
            const out = [];
            for (const id of ['wizard','help-modal','shortcuts-modal','cmd-palette-overlay','welcome-prompt']) {
                const el = document.getElementById(id);
                if (!el) continue;
                const vis = id === 'wizard' ? getComputedStyle(el).display !== 'none' : el.classList.contains('visible');
                if (vis) out.push(id);
            }
            return out;
        }""")
        if not vis:
            break
        page.keyboard.press("Escape")
        settle(page, 350)

def toast_text(page):
    return page.evaluate("() => { const t = document.getElementById('toast'); return t ? t.textContent : null; }")

def cdp_key(page, key, vk, ctrl=True, shift=True):
    """Dispatch key events via raw CDP with an EXPLICIT key value (as a real
    desktop browser produces). Observation pipeline, not app-function calls."""
    mods = 0
    if ctrl: mods |= 2
    if shift: mods |= 8
    for type_, params in (("rawKeyDown", {"key": key, "code": "Key" + key.upper(), "windowsVirtualKeyCode": vk}),
                          ("keyUp", {"key": key, "code": "Key" + key.upper(), "windowsVirtualKeyCode": vk})):
        args = {"type": type_, "modifiers": mods, **params}
        if type_ == "keyDown" and len(key) == 1 and key.isalpha() and shift:
            args["text"] = key.upper()
        page.context.new_cdp_session(page) if not hasattr(page, "_cdp") else None
    page._cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "modifiers": mods, "key": key,
                                              "code": "Key" + key.upper(), "windowsVirtualKeyCode": vk})
    page._cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "modifiers": mods, "key": key,
                                              "code": "Key" + key.upper(), "windowsVirtualKeyCode": vk})

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        page = ctx.new_page()
        page.on("console", log_console)
        page.on("pageerror", lambda e: console_errors.append((current_flow[0], str(e)[:250])))
        def on_dialog(d):
            dialog_log.append((current_flow[0], d.type, (d.message or "")[:60]))
            d.dismiss()
        page.on("dialog", on_dialog)
        page.goto(BASE, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("#cmd-palette-input", state="attached", timeout=20000)
        settle(page, 2200)
        page.evaluate("() => localStorage.clear()")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_selector("#cmd-palette-input", state="attached", timeout=20000)
        settle(page, 2000)
        page.keyboard.press("Escape"); settle(page, 500)
        page._cdp = ctx.new_cdp_session(page)

        # ---- X1: what e.key does Playwright's Ctrl+Shift+s produce? (observation) ----
        current_flow[0] = "X1"
        try:
            dismiss(page)
            page.evaluate("() => { window.__keys = []; document.addEventListener('keydown', e => window.__keys.push({key: e.key, ctrl: e.ctrlKey, shift: e.shiftKey}), true); }")
            page.keyboard.press("Control+Shift+s"); settle(page, 400)
            keys = page.evaluate("() => window.__keys")
            log_result("X1_key_value_observation", {"observed_keys": keys,
                "note": "if key:'s' with shift — platform quirk explains why combos work in Playwright but not real Chrome (which reports 'S')"})
        except Exception:
            log_result("X1", {"error": traceback.format_exc()[-300:]})

        # ---- X2: CDP key='S' ctrl+shift -> does saveAs fire? ----
        current_flow[0] = "X2"
        try:
            dismiss(page)
            dialog_log.clear()
            page._cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "modifiers": 10, "key": "S",
                                                      "code": "KeyS", "windowsVirtualKeyCode": 83})
            page._cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "modifiers": 10, "key": "S",
                                                      "code": "KeyS", "windowsVirtualKeyCode": 83})
            settle(page, 700)
            # prompt dialog would appear if handler matched 'S'
            prompt_seen = any(t == "prompt" for _, t, _ in dialog_log)
            log_result("X2_cdp_S_saveas", {"dialogs": [t for _, t, _ in dialog_log],
                "prompt_seen": prompt_seen,
                "expected_if_bug": "no prompt — handler matches only lowercase 's' (index.html:5390), real desktop Chrome sends 'S'"})
        except Exception:
            log_result("X2", {"error": traceback.format_exc()[-300:]})

        # ---- X3: CDP key='Z' ctrl+shift -> redo fires? ----
        current_flow[0] = "X3"
        try:
            dismiss(page)
            card = page.query_selector(".lib-item")
            card.click(); settle(page, 400)
            page.keyboard.press("Delete"); settle(page, 400)
            n_del = page.evaluate("() => window._bydState.objects.size")
            page.keyboard.press("Control+z"); settle(page, 400)
            n_undo = page.evaluate("() => window._bydState.objects.size")
            dialog_log.clear()
            page._cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "modifiers": 10, "key": "Z",
                                                      "code": "KeyZ", "windowsVirtualKeyCode": 90})
            page._cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "modifiers": 10, "key": "Z",
                                                      "code": "KeyZ", "windowsVirtualKeyCode": 90})
            settle(page, 600)
            n_redo = page.evaluate("() => window._bydState.objects.size")
            log_result("X3_cdp_Z_shift_redo", {
                "after_delete": n_del, "after_undo": n_undo, "after_cdp_shift_z": n_redo,
                "expected_if_bug": "redo NOT applied (n stays 1) — handler needs lowercase 'z' (index.html:5388)",
                "verdict_bug": n_redo == n_undo})
        except Exception:
            log_result("X3", {"error": traceback.format_exc()[-300:]})

        # ---- X4: nextId collision — file nextId points AT an existing id ----
        current_flow[0] = "X4"
        try:
            dismiss(page)
            page.evaluate("() => window._bydLoadDesign({version:4, objects:[{id:5,type:'tree_deciduous',params:{height:15},position:{x:0,z:0},rotation:0,scale:1}], yard:{width:50,depth:100}, nextId:5, terrain:null})")
            settle(page, 800)
            before = page.evaluate("() => { const s = window._bydState; return {ids: Array.from(s.objects.keys()), nextId: s.nextId}; }")
            card = page.query_selector(".lib-item")
            card.click(); settle(page, 500)
            after = page.evaluate("() => { const s = window._bydState; return {ids: Array.from(s.objects.keys()), types: Array.from(s.objects.values()).map(o => o.type), nextId: s.nextId}; }")
            page.screenshot(path=os.path.join(OUT, "x4_nextid_collision.png"))
            log_result("X4_nextid_collision", {
                "before": before, "after_catalog_click": after,
                "expected_if_bug": "loaded tree (id 5) silently REPLACED by the new fence — same id; undo stack + selection corrupted",
                "verdict_bug": 5 not in after["ids"] or len(after["ids"]) < 2 or after["types"].count("fence_privacy") == 2})
        except Exception:
            log_result("X4", {"error": traceback.format_exc()[-300:]})

        # ---- X5: Ctrl+A select-all + Ctrl+D duplicate (real keys) ----
        current_flow[0] = "X5"
        try:
            dismiss(page)
            page.evaluate("() => window._bydLoadDesign({version:4, objects:[], yard:{width:50,depth:100}, nextId:1, terrain:null})")
            settle(page, 800)
            cards = page.query_selector_all(".lib-item")
            cards[0].click(); settle(page, 300)
            cards[3].click(); settle(page, 300)
            n0 = page.evaluate("() => window._bydState.objects.size")
            page.keyboard.press("Control+a"); settle(page, 400)
            sel_n = page.evaluate("() => window._bydState.selectedIds.size")
            batch = page.evaluate("() => document.getElementById('batch-bar').classList.contains('visible')")
            page.keyboard.press("Control+d"); settle(page, 500)
            n1 = page.evaluate("() => window._bydState.objects.size")
            page.screenshot(path=os.path.join(OUT, "x5_ctrl_a_d.png"))
            log_result("X5_ctrl_a_ctrl_d", {
                "objects_before": n0, "selected_after_ctrl_a": sel_n,
                "objects_after_ctrl_d": n1,
                "expected": "Ctrl+A selects 2 + batch bar; Ctrl+D duplicates selected",
                "verdict_ok": sel_n == 2})
        except Exception:
            log_result("X5", {"error": traceback.format_exc()[-300:]})

        browser.close()

    print("\n=== DIALOGS ===")
    for f, t, m in dialog_log:
        print(f"[{f}] {t}: {m}")
    print("\n=== PAGE ERRORS round5 ===")
    for f, t in console_errors:
        print(f"[{f}] {t}")

if __name__ == "__main__":
    run()
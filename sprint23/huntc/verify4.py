"""Bug Hunt C — verification round 4. Final confirmations."""
import json, time, traceback, os
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8303/index.html"
OUT = "/root/backyard-designer/sprint23/huntc"
RESULTS = os.path.join(OUT, "results4.jsonl")
os.makedirs(OUT, exist_ok=True)
current_flow = ["boot"]
console_errors = []

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
    # ensure perf panel closed
    page.evaluate("() => { const el = document.getElementById('perf-panel'); if (el && getComputedStyle(el).display !== 'none') { const c = document.getElementById('perf-close'); if (c) c.click(); } }")
    settle(page, 200)

def toast_text(page):
    return page.evaluate("() => { const t = document.getElementById('toast'); return t ? t.textContent : null; }")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        page = ctx.new_page()
        page.on("console", log_console)
        page.on("pageerror", lambda e: console_errors.append((current_flow[0], str(e)[:250])))
        page.goto(BASE, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("#cmd-palette-input", state="attached", timeout=20000)
        settle(page, 2200)
        page.evaluate("() => localStorage.clear()")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_selector("#cmd-palette-input", state="attached", timeout=20000)
        settle(page, 2000)
        page.keyboard.press("Escape"); settle(page, 500)

        # ---- W1: Ctrl+Shift+Z redo dead? (real keys) ----
        current_flow[0] = "W1"
        try:
            dismiss(page)
            card = page.query_selector(".lib-item")
            card.click(); settle(page, 400)
            n1 = page.evaluate("() => window._bydState.objects.size")
            page.keyboard.press("Delete"); settle(page, 400)
            n2 = page.evaluate("() => window._bydState.objects.size")
            page.keyboard.press("Control+z"); settle(page, 400)
            n3 = page.evaluate("() => window._bydState.objects.size")
            page.keyboard.press("Control+Shift+z"); settle(page, 500)
            n4 = page.evaluate("() => window._bydState.objects.size")
            # control: Ctrl+Y redo should work
            page.keyboard.press("Control+z"); settle(page, 300)   # undo again (if shift-redo worked, this undoes the redo)
            n5 = page.evaluate("() => window._bydState.objects.size")
            page.keyboard.press("Control+y"); settle(page, 400)
            n6 = page.evaluate("() => window._bydState.objects.size")
            page.screenshot(path=os.path.join(OUT, "w1_ctrl_shift_z.png"))
            log_result("W1_shift_redo", {
                "after_add": n1, "after_delete": n2, "after_ctrl_z": n3,
                "after_ctrl_shift_z": n4, "after_ctrl_z2": n5, "after_ctrl_y": n6,
                "expected": "ctrl_shift_z restores object (n4==1); if n4==0 the Shift+Z redo is dead",
                "verdict_bug": n4 != n3})
        except Exception:
            log_result("W1", {"error": traceback.format_exc()[-300:]})

        # ---- W2: brush keys 1-6 mapping vs guide (real keys) ----
        current_flow[0] = "W2"
        try:
            dismiss(page)
            mapping = {}
            for key in ["1", "2", "3", "4", "5", "6"]:
                page.keyboard.press(key); settle(page, 250)
                mapping[key] = page.evaluate("() => { const b = document.querySelector('.terrain-mode-btn.active'); return b ? b.getAttribute('data-tmode') : null; }")
            page.screenshot(path=os.path.join(OUT, "w2_brush_map.png"))
            log_result("W2_brush_mapping", {
                "observed": mapping,
                "guide_says": "1 Raise, 2 Lower, 3 Smooth, 4 Erode, 5 Dig, 6 Fill",
                "handler_order": "['raise','lower','smooth','erode','dig','fill'] (index.html:15794)",
                "verdict_ok": mapping == {"1": "raise", "2": "lower", "3": "smooth", "4": "erode", "5": "dig", "6": "fill"}})
        except Exception:
            log_result("W2", {"error": traceback.format_exc()[-300:]})

        # ---- W3: empty .json file load (real Load flow) ----
        current_flow[0] = "W3"
        try:
            dismiss(page)
            empty = os.path.join(OUT, "empty.json")
            with open(empty, "w") as f:
                f.write("")
            page.click("#btn-load", timeout=4000); settle(page, 300)
            page.set_input_files("#import-input", empty)
            settle(page, 800)
            tt = toast_text(page)
            n = page.evaluate("() => window._bydState.objects.size")
            yard = page.evaluate("() => window._bydState.yard")
            log_result("W3_empty_json", {"toast": tt, "objects": n, "yard": yard,
                "expected": "error toast 'Could not read this file'; state unchanged",
                "verdict_ok": bool(tt) and "Could not read" in tt})
        except Exception:
            log_result("W3", {"error": traceback.format_exc()[-300:]})

        # ---- W4: Ctrl+Shift+S dead combo — dialog + download observables (real keys) ----
        current_flow[0] = "W4"
        try:
            dismiss(page)
            dialogs = []
            def on_dialog(d):
                dialogs.append(d.type)
                d.dismiss()
            page.on("dialog", on_dialog)
            got_download = False
            try:
                with page.expect_download(timeout=5000) as dl_info:
                    page.keyboard.press("Control+Shift+s")
                dl = dl_info.value
                got_download = True
                dl.save_as(os.path.join(OUT, "w4_shift_s.json"))
            except Exception:
                got_download = False
            settle(page, 400)
            tt = toast_text(page)
            page.screenshot(path=os.path.join(OUT, "w4_ctrl_shift_s.png"))
            # control: Ctrl+S fires download (proves keyboard path works at all)
            with page.expect_download(timeout=6000) as dl_info:
                page.keyboard.press("Control+s")
            ctrl_s = dl_info.value.suggested_filename
            log_result("W4_ctrl_shift_s_dead", {
                "dialogs_on_shift_s": dialogs, "download_on_shift_s": got_download,
                "toast_after_shift_s": tt, "ctrl_s_filename_control": ctrl_s,
                "expected_if_bug": "no prompt, no download, no toast on Ctrl+Shift+S while Ctrl+S works",
                "verdict_bug": not dialogs and not got_download})
        except Exception:
            log_result("W4", {"error": traceback.format_exc()[-300:]})

        # ---- W5: toast clobber on load (fixed harness) ----
        current_flow[0] = "W5"
        try:
            dismiss(page)
            valid = os.path.join(OUT, "w5_design.json")
            with open(valid, "w") as f:
                json.dump({"version": 4, "yard": {"width": 40, "depth": 60, "shape": "rectangle"},
                           "objects": [{"id": 2, "type": "tree_deciduous", "params": {"height": 15}, "position": {"x": 3, "z": 3}, "rotation": 0, "scale": 1}],
                           "nextId": 3, "terrain": None}, f)
            page.click("#btn-load", timeout=4000); settle(page, 400)
            page.set_input_files("#import-input", valid)
            t0 = time.time()
            seen = []
            for _ in range(24):
                tt = toast_text(page)
                tv = page.evaluate("() => document.getElementById('toast').classList.contains('visible')")
                if tv and tt and (not seen or seen[-1]["text"] != tt):
                    seen.append({"at_ms": int((time.time() - t0) * 1000), "text": tt})
                page.wait_for_timeout(120)
            page.screenshot(path=os.path.join(OUT, "w5_toast_clobber.png"))
            log_result("W5_toast_clobber", {
                "toast_sequence": seen,
                "expected_if_bug": "'Design loaded successfully!' appears then is replaced by welcome toast ~500ms later",
                "verdict_bug": any("loaded successfully" in s["text"] for s in seen) and any("Welcome!" in s["text"] for s in seen)})
        except Exception:
            log_result("W5", {"error": traceback.format_exc()[-300:]})

        # ---- W6: Ctrl+Shift+S while palette input focused — does 'S' char type? (info) ----
        current_flow[0] = "W6"
        try:
            dismiss(page)
            page.keyboard.press("Control+k"); settle(page, 300)
            page.keyboard.press("Control+Shift+s"); settle(page, 400)
            val = page.evaluate("() => document.getElementById('cmd-palette-input').value")
            pal = page.evaluate("() => document.getElementById('cmd-palette-overlay').classList.contains('visible')")
            dismiss(page)
            log_result("W6_shift_s_in_palette", {"palette_input_value": val, "palette_open": pal,
                "note": "palette input keydown stops propagation for ctrl combos? check info only"})
        except Exception:
            log_result("W6", {"error": traceback.format_exc()[-300:]})

        browser.close()

    print("\n=== PAGE ERRORS round4 ===")
    for f, t in console_errors:
        print(f"[{f}] {t}")

if __name__ == "__main__":
    run()
"""Bug Hunt C — verification round 3. Focused probes to confirm/refute candidates.

Real input events for all interactions; evaluate only for state reads +
labeled loadDesign code-path probes (marked LABELED-PROBE).
"""
import json, time, traceback, os
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8303/index.html"
OUT = "/root/backyard-designer/sprint23/huntc"
RESULTS = os.path.join(OUT, "results3.jsonl")
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

VISIBLE_OVERLAYS = """() => {
    const out = [];
    for (const id of ['wizard','help-modal','shortcuts-modal','share-modal','cmd-palette-overlay','welcome-prompt']) {
        const el = document.getElementById(id);
        if (!el) continue;
        const vis = id === 'wizard' ? getComputedStyle(el).display !== 'none' : el.classList.contains('visible');
        if (vis) out.push(id);
    }
    return out;
}"""

def dismiss(page):
    for _ in range(4):
        if not page.evaluate(VISIBLE_OVERLAYS):
            return
        page.keyboard.press("Escape")
        settle(page, 350)

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
        page.keyboard.press("Escape"); settle(page, 500)  # close wizard

        # ---- V1: dup-id load with VALID types (LABELED-PROBE) ----
        current_flow[0] = "V1"
        try:
            page.evaluate("() => window._bydLoadDesign({version:4, objects:[{id:7,type:'fence_privacy',params:{height:6,length:24,color:'#D2B48C'},position:{x:0,z:0},rotation:0,scale:1},{id:7,type:'pergola',params:{width:10,depth:10,color:'#8a5a3a'},position:{x:6,z:6},rotation:0,scale:1},{id:8,type:'tree_deciduous',params:{height:20},position:{x:-6,z:-6},rotation:0,scale:1}], yard:{width:50,depth:100}, nextId:9, terrain:null})")
            settle(page, 1000)
            st = page.evaluate("() => { const s = window._bydState; return {n: s.objects.size, ids: Array.from(s.objects.keys()), types: Array.from(s.objects.values()).map(o => o.type), nextId: s.nextId}; }")
            toast = toast_text(page)
            shot = page.screenshot(path=os.path.join(OUT, "v1_dup_ids_valid.png"))
            log_result("V1_dup_ids_valid_types", {
                "state": st, "toast": toast,
                "expected": "3 objects loaded (two share id 7 — must both survive)",
                "verdict_bug": st["n"] != 3})
        except Exception:
            log_result("V1", {"error": traceback.format_exc()[-300:]})

        # ---- V2: nextId collision after load (real catalog click) ----
        current_flow[0] = "V2"
        try:
            page.evaluate("() => window._bydLoadDesign({version:4, objects:[{id:5,type:'tree_deciduous',params:{height:15},position:{x:0,z:0},rotation:0,scale:1}], yard:{width:50,depth:100}, nextId:1, terrain:null})")
            settle(page, 800)
            before = page.evaluate("() => { const s = window._bydState; return {ids: Array.from(s.objects.keys()), nextId: s.nextId}; }")
            card = page.query_selector(".lib-item")
            card.click(); settle(page, 400)
            after = page.evaluate("() => { const s = window._bydState; return {ids: Array.from(s.objects.keys()), nextId: s.nextId}; }")
            toast = toast_text(page)
            page.screenshot(path=os.path.join(OUT, "v2_nextid_collision.png"))
            log_result("V2_nextid_collision", {
                "before": before, "after_click": after, "toast": toast,
                "expected": "new object gets a FRESH id, not 5",
                "verdict_bug": 5 in after["ids"][1:] if len(after["ids"]) > 1 else False})
        except Exception:
            log_result("V2", {"error": traceback.format_exc()[-300:]})

        # ---- V3: '?' while typing in palette (real keys) ----
        current_flow[0] = "V3"
        try:
            dismiss(page)
            page.keyboard.press("Control+k"); settle(page, 300)
            page.keyboard.type("terr", delay=25); settle(page, 200)
            page.keyboard.press("Shift+Slash"); settle(page, 400)  # '?'
            sc = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
            page.screenshot(path=os.path.join(OUT, "v3_question_in_palette.png"))
            dismiss(page)
            log_result("V3_question_while_typing", {
                "shortcuts_opened": sc,
                "expected_if_bug": "same as F1 — handler at index.html:5270-5273 ignores input focus"})
        except Exception:
            log_result("V3", {"error": traceback.format_exc()[-300:]})

        # ---- V4: '?' opens guide normally + F1 opens guide (clean state) ----
        current_flow[0] = "V4"
        try:
            dismiss(page)
            page.keyboard.press("Shift+Slash"); settle(page, 400)
            sc_q = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
            dismiss(page)
            page.keyboard.press("F1"); settle(page, 400)
            sc_f1 = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
            dismiss(page)
            log_result("V4_question_and_f1_clean", {"question_opens": sc_q, "f1_opens": sc_f1,
                "expected": "both true — guide docs correct in clean state"})
        except Exception:
            log_result("V4", {"error": traceback.format_exc()[-300:]})

        # ---- V5: 'r' reset view with camera capture ----
        current_flow[0] = "V5"
        try:
            dismiss(page)
            # dirty the camera with real mouse orbit: drag on canvas
            page.mouse.move(700, 450)
            page.mouse.down()
            page.mouse.move(880, 380, steps=8)
            page.mouse.up()
            settle(page, 400)
            cam_before = page.evaluate("() => { const c = window._bydActiveCamera; return c ? {x: Math.round(c.position.x*10)/10, y: Math.round(c.position.y*10)/10, z: Math.round(c.position.z*10)/10} : null; }")
            page.keyboard.press("r"); settle(page, 500)
            cam_after = page.evaluate("() => { const c = window._bydActiveCamera; return c ? {x: Math.round(c.position.x*10)/10, y: Math.round(c.position.y*10)/10, z: Math.round(c.position.z*10)/10} : null; }")
            log_result("V5_r_reset_view", {"cam_before": cam_before, "cam_after": cam_after,
                "expected": "camera returns to default; changed = works",
                "verdict_ok": cam_before != cam_after})
        except Exception:
            log_result("V5", {"error": traceback.format_exc()[-300:]})

        # ---- V6: arrows + Delete with clean selection (no dock open) ----
        current_flow[0] = "V6"
        try:
            dismiss(page)
            card = page.query_selector(".lib-item")
            card.click(); settle(page, 400)
            sel = page.evaluate("() => window._bydState.selectedId")
            x0 = page.evaluate("() => window._bydState.objects.get(window._bydState.selectedId).position.x")
            page.keyboard.press("ArrowLeft"); settle(page, 300)
            x1 = page.evaluate("() => window._bydState.objects.get(window._bydState.selectedId).position.x")
            page.keyboard.press("Shift+ArrowRight"); settle(page, 300)
            x2 = page.evaluate("() => window._bydState.objects.get(window._bydState.selectedId).position.x")
            page.keyboard.press("Delete"); settle(page, 400)
            n_after_del = page.evaluate("() => window._bydState.objects.size")
            log_result("V6_arrows_delete", {
                "sel": sel, "x0": x0, "after_left": x1, "after_shift_right": x2,
                "objects_after_delete": n_after_del,
                "expected": "x0-1, then -0.9 net, then object deleted",
                "verdict_ok": abs((x1 - x0) + 1) < 0.01 and n_after_del == 0})
        except Exception:
            log_result("V6", {"error": traceback.format_exc()[-300:]})

        # ---- V7: perf panel Ctrl+Shift+P (lazy element) ----
        current_flow[0] = "V7"
        try:
            dismiss(page)
            page.keyboard.press("Control+Shift+KeyP"); settle(page, 600)
            st1 = page.evaluate("() => { const el = document.getElementById('perf-panel'); return el ? getComputedStyle(el).display : 'NOT_CREATED'; }")
            page.screenshot(path=os.path.join(OUT, "v7_perf_panel.png"))
            page.keyboard.press("Control+Shift+KeyP"); settle(page, 500)
            st2 = page.evaluate("() => { const el = document.getElementById('perf-panel'); return el ? getComputedStyle(el).display : 'NOT_CREATED'; }")
            log_result("V7_perf_panel", {"after_first": st1, "after_second": st2,
                "expected": "block then none", "verdict_ok": st1 == "block" and st2 == "none"})
        except Exception:
            log_result("V7", {"error": traceback.format_exc()[-300:]})

        # ---- V8: toast clobber on Load (welcome toast vs loaded toast) ----
        current_flow[0] = "V8"
        try:
            dismiss(page)
            valid = os.path.join(OUT, "v8_design.json")
            with open(valid, "w") as f:
                json.dump({"version": 4, "yard": {"width": 40, "depth": 60, "shape": "rectangle"},
                           "objects": [{"id": 2, "type": "tree_deciduous", "params": {"height": 15}, "position": {"x": 3, "z": 3}, "rotation": 0, "scale": 1}],
                           "nextId": 3, "terrain": None}, f)
            page.click("#btn-load", timeout=4000); settle(page, 300)
            page.set_input_files("#import-input", valid)
            t0 = time.time()
            early = None
            for _ in range(12):
                tt = toast_text(page)
                tv = page.evaluate("() => document.getElementById('toast').classList.contains('visible')")
                if tv and tt and "loaded successfully" in tt:
                    early = {"at_ms": int((time.time() - t0) * 1000), "text": tt}
                    break
                page.wait_for_timeout(80)
            page.wait_for_timeout(1100)
            late = {"at_ms": int((time.time() - t0) * 1000), "text": toast_text(page),
                    "visible": page.evaluate("() => document.getElementById('toast').classList.contains('visible')")}
            page.screenshot(path=os.path.join(OUT, "v8_toast_clobber.png"))
            log_result("V8_toast_clobber", {
                "early_success_toast": early, "late_toast": late,
                "expected": "user should still see 'Design loaded successfully!' — but welcome toast replaces it at ~+500ms",
                "verdict_bug": bool(early) and late.get("text") != early.get("text")})
        except Exception:
            log_result("V8", {"error": traceback.format_exc()[-300:]})

        # ---- V9: Ctrl+Shift+S opens Save-As prompt (real key) ----
        current_flow[0] = "V9"
        try:
            dismiss(page)
            dialogs = []
            page.on("dialog", lambda d: (dialogs.append(d.type + ":" + (d.message or "")[:40]), d.dismiss()))
            with page.expect_download(timeout=8000) as dl_info:
                page.keyboard.press("Control+Shift+s")
            dl = dl_info.value
            fname = dl.suggested_filename
            path = os.path.join(OUT, "v9_saveas.json")
            dl.save_as(path)
            size = os.path.getsize(path)
            log_result("V9_ctrl_shift_s", {"dialogs": dialogs, "filename": fname, "bytes": size,
                "expected": "prompt dialog appears; default filename used; download fires",
                "verdict_ok": size > 0 and len(dialogs) >= 1})
        except Exception:
            log_result("V9", {"error": traceback.format_exc()[-300:]})

        # ---- V10: W walk mode enter + Esc exit ----
        current_flow[0] = "V10"
        try:
            dismiss(page)
            page.keyboard.press("w"); settle(page, 700)
            walk_ui = page.evaluate("""() => {
                const hits = [];
                document.querySelectorAll('body *').forEach(el => {
                    const id = (el.id || '').toLowerCase();
                    const cls = String(el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className || '').toLowerCase();
                    if ((id.includes('walk') || cls.includes('walk')) && el.offsetParent !== null) hits.push((el.id || el.className).toString().slice(0, 40));
                });
                return hits.slice(0, 8);
            }""")
            page.screenshot(path=os.path.join(OUT, "v10_walk_mode.png"))
            page.keyboard.press("Escape"); settle(page, 500)
            walk_after = page.evaluate("""() => {
                const hits = [];
                document.querySelectorAll('body *').forEach(el => {
                    const id = (el.id || '').toLowerCase();
                    const cls = String(el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className || '').toLowerCase();
                    if ((id.includes('walk') || cls.includes('walk')) && el.offsetParent !== null) hits.push((el.id || el.className).toString().slice(0, 40));
                });
                return hits.slice(0, 8);
            }""")
            log_result("V10_walk_mode", {"walk_ui_enter": walk_ui, "walk_ui_after_esc": walk_after,
                "expected": "walk HUD appears on W, gone after Esc",
                "verdict_ok": len(walk_ui) > 0 and len(walk_after) == 0})
        except Exception:
            log_result("V10", {"error": traceback.format_exc()[-300:]})

        # ---- V11: rapid Escape x3 with palette open (idempotent close) ----
        current_flow[0] = "V11"
        try:
            dismiss(page)
            page.keyboard.press("Control+k"); settle(page, 300)
            for _ in range(3):
                page.keyboard.press("Escape"); settle(page, 150)
            pal = page.evaluate("() => document.getElementById('cmd-palette-overlay').classList.contains('visible')")
            sel_state = page.evaluate("() => window._bydState.selectedId")
            log_result("V11_triple_escape", {"palette_open": pal, "selectedId": sel_state,
                "expected": "closed; no errors", "verdict_ok": not pal})
        except Exception:
            log_result("V11", {"error": traceback.format_exc()[-300:]})

        # ---- V12: v/b view toggle round trip (real keys) ----
        current_flow[0] = "V12"
        try:
            dismiss(page)
            page.keyboard.press("b"); settle(page, 400)
            v2d = page.evaluate("() => { const b = document.querySelector('#view-toggle [aria-pressed=\"true\"]'); return b ? b.textContent.trim() : null; }")
            page.keyboard.press("v"); settle(page, 400)
            v3d = page.evaluate("() => { const b = document.querySelector('#view-toggle [aria-pressed=\"true\"]'); return b ? b.textContent.trim() : null; }")
            log_result("V12_view_toggle", {"after_b": v2d, "after_v": v3d,
                "expected": "2D then 3D", "verdict_ok": bool(v2d) and bool(v3d) and v2d != v3d})
        except Exception:
            log_result("V12", {"error": traceback.format_exc()[-300:]})

        browser.close()

    print("\n=== PAGE ERRORS round3 ===")
    for f, t in console_errors:
        print(f"[{f}] {t}")

if __name__ == "__main__":
    run()
"""Sprint 23 Bug Hunt C — persistence & edge cases (READ-ONLY hunter).

Playwright harness, REAL input events (keyboard.press / locator.click / set_input_files).
page.evaluate is used ONLY for state reads (DOM/storage) and clearly-labeled
code-path probes — NEVER to drive click/key paths (per card constraint 5).

Port: 8303 (assigned). Output: sprint23/huntc/results.jsonl + PNG evidence.
"""
import json, time, traceback, os
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8303/index.html"
OUT = "/root/backyard-designer/sprint23/huntc"
RESULTS = os.path.join(OUT, "results.jsonl")
os.makedirs(OUT, exist_ok=True)

flows_run = []
console_errors = []   # (flow, kind, text)
current_flow = ["boot"]

def log_console(msg):
    try:
        if msg.type in ("error", "warning"):
            console_errors.append((current_flow[0], msg.type, (msg.text or "")[:300]))
    except Exception:
        pass

def log_result(flow, ok, data):
    rec = {"flow": flow, "ok": ok, **data, "ts": time.time()}
    with open(RESULTS, "a") as f:
        f.write(json.dumps(rec) + "\n")
    flows_run.append(flow)
    print(("PASS " if ok else "INFO ") + flow + " :: " + json.dumps(data)[:400])

def shot(page, name):
    path = os.path.join(OUT, name)
    page.screenshot(path=path)
    return name

def settle(page, ms=350):
    page.wait_for_timeout(ms)

def toast_visible(page):
    return page.evaluate("() => { const t = document.getElementById('toast'); return t ? t.classList.contains('visible') : null; }")

def toast_text(page):
    return page.evaluate("() => { const t = document.getElementById('toast'); return t ? t.textContent : null; }")

def modal_visible(page, mid):
    return page.evaluate("id => document.getElementById(id).classList.contains('visible')", mid)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.on("console", log_console)
        page.on("pageerror", lambda e: console_errors.append((current_flow[0], "pageerror", str(e)[:300])))

        # ---------------- F01 boot & console ----------------
        current_flow[0] = "F01"
        try:
            page.goto(BASE, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("#cmd-palette-input", timeout=20000)
            settle(page, 2500)
            wizard_disp = page.evaluate("() => getComputedStyle(document.getElementById('wizard')).display")
            welcome_vis = page.evaluate("() => document.getElementById('welcome-prompt').classList.contains('visible')")
            has_continue = page.evaluate("() => !!document.getElementById('wizard-continue')")
            shot(page, "f01_boot.png")
            log_result("F01_boot", True, {
                "wizard_display": wizard_disp, "welcome_visible": welcome_vis,
                "autosave_continue_btn": has_continue,
                "console_errors_boot": [e for f, k, e in console_errors if k == "pageerror"]})
        except Exception:
            log_result("F01_boot", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F02 wizard complete (real clicks) ----------------
        current_flow[0] = "F02"
        try:
            page.evaluate("() => localStorage.clear()")  # setup: clean profile
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector("#cmd-palette-input", timeout=20000)
            settle(page, 2000)
            wd = page.evaluate("() => getComputedStyle(document.getElementById('wizard')).display")
            page.click("#wizard-next", timeout=4000)
            settle(page, 400)
            shot(page, "f02a_wizard_step2.png")
            page.fill("#wiz-width", "60")
            page.fill("#wiz-depth", "80")
            page.click("#wizard-finish", timeout=4000)
            settle(page, 900)
            wd2 = page.evaluate("() => getComputedStyle(document.getElementById('wizard')).display")
            yard = page.evaluate("() => { const s = window._bydState; return s ? {w: s.yard.width, d: s.yard.depth} : 'NO _bydState'; }")
            shot(page, "f02b_after_finish.png")
            log_result("F02_wizard_complete", wd2 == "none" and yard != "NO _bydState", {
                "wizard_before": wd, "wizard_after": wd2, "yard_after": yard,
                "expected": "yard 60x80, wizard hidden"})
        except Exception:
            log_result("F02_wizard_complete", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F03 autosave persistence across reload ----------------
        current_flow[0] = "F03"
        try:
            # add an object through the real UI: click catalog card (real click)
            added = page.evaluate("() => { const c = document.querySelector('.item-card, .cat-item, [data-type]'); return c ? c.className : null; }")
            page.click("[data-type]", timeout=4000) if page.query_selector("[data-type]") else None
            settle(page, 2700)  # autosave debounce 2s
            autosave_raw = page.evaluate("() => localStorage.getItem('backyard-design-autosave')")
            autosave = json.loads(autosave_raw) if autosave_raw else None
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector("#cmd-palette-input", timeout=20000)
            settle(page, 2000)
            wd = page.evaluate("() => getComputedStyle(document.getElementById('wizard')).display")
            has_continue = page.evaluate("() => !!document.getElementById('wizard-continue')")
            shot(page, "f03_reload_state.png")
            log_result("F03_autosave_reload", True, {
                "catalog_card_selector_found": bool(added),
                "autosave_present": bool(autosave),
                "autosave_yard": (autosave or {}).get("yard"),
                "objects_in_autosave": len((autosave or {}).get("objects", [])),
                "wizard_shown_after_reload": wd,
                "continue_btn_shown": has_continue,
                "note": "expected: wizard returns with Continue previous design button (user must re-choose; design itself only loads on explicit click)"})
        except Exception:
            log_result("F03_autosave_reload", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F04 palette open/close via Ctrl+K + Escape ----------------
        current_flow[0] = "F04"
        try:
            # dismiss wizard via its own path (Escape) so canvas is live
            page.keyboard.press("Escape"); settle(page, 600)
            page.keyboard.press("Control+k"); settle(page, 400)
            pal = page.evaluate("() => document.getElementById('cmd-palette-overlay').classList.contains('visible')")
            shot(page, "f04a_palette_open.png")
            page.keyboard.press("Escape"); settle(page, 300)
            pal2 = page.evaluate("() => document.getElementById('cmd-palette-overlay').classList.contains('visible')")
            shot(page, "f04b_palette_closed.png")
            log_result("F04_palette_esc", pal and not pal2, {"open_after_ctrlk": pal, "open_after_esc": pal2})
        except Exception:
            log_result("F04_palette_esc", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F05 palette keyboard navigation ----------------
        current_flow[0] = "F05"
        try:
            page.keyboard.press("Control+k"); settle(page, 300)
            page.keyboard.type("view", delay=25); settle(page, 250)
            n1 = page.evaluate("() => document.querySelectorAll('#cmd-palette-results .cmd-item').length")
            sel0 = page.evaluate("() => (document.querySelector('#cmd-palette-results .cmd-item.selected')||{}).textContent")
            page.keyboard.press("ArrowDown"); page.keyboard.press("ArrowDown"); settle(page, 150)
            sel1 = page.evaluate("() => (document.querySelector('#cmd-palette-results .cmd-item.selected')||{}).textContent")
            page.keyboard.press("ArrowUp"); settle(page, 150)
            sel2 = page.evaluate("() => (document.querySelector('#cmd-palette-results .cmd-item.selected')||{}).textContent")
            shot(page, "f05_palette_nav.png")
            page.keyboard.press("Enter"); settle(page, 500)
            closed = page.evaluate("() => !document.getElementById('cmd-palette-overlay').classList.contains('visible')")
            log_result("F05_palette_nav", n1 > 0 and closed, {
                "results_for_view": n1, "sel0": sel0, "sel_down2": sel1, "sel_up": sel2,
                "closed_after_enter": closed})
        except Exception:
            log_result("F05_palette_nav", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F06 F1 fires while typing in palette input (suspect) ----------------
        current_flow[0] = "F06"
        try:
            page.keyboard.press("Control+k"); settle(page, 300)
            focused = page.evaluate("() => document.activeElement && document.activeElement.id")
            page.keyboard.type("terrain", delay=25); settle(page, 200)
            page.keyboard.press("F1"); settle(page, 400)
            sc = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
            shot(page, "f06_f1_during_typing.png")
            # cleanup: esc closes both
            page.keyboard.press("Escape"); settle(page, 250)
            page.keyboard.press("Escape"); settle(page, 250)
            log_result("F06_f1_during_typing", True, {
                "palette_focus": focused, "shortcuts_opened_while_typing": sc,
                "expected_if_bug": "true — F1/? handler at index.html:5270 has no input-target guard (capture phase)"})
        except Exception:
            log_result("F06_f1_during_typing", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F07 Escape closes wizard AND spawned shortcuts modal in one stroke ----------------
        current_flow[0] = "F07"
        try:
            page.evaluate("() => localStorage.clear()")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector("#cmd-palette-input", timeout=20000)
            settle(page, 2000)
            # open shortcuts guide over the wizard via F1 (real key)
            page.keyboard.press("F1"); settle(page, 400)
            sc_before = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
            wizard_before = page.evaluate("() => getComputedStyle(document.getElementById('wizard')).display")
            shot(page, "f07a_wizard_plus_shortcuts.png")
            page.keyboard.press("Escape"); settle(page, 500)
            sc_after = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
            wizard_after = page.evaluate("() => getComputedStyle(document.getElementById('wizard')).display")
            yard = page.evaluate("() => { const s = window._bydState; return s ? {w: s.yard.width, d: s.yard.depth} : null; }")
            shot(page, "f07b_after_one_escape.png")
            log_result("F07_escape_stacking", True, {
                "shortcuts_before": sc_before, "wizard_before": wizard_before,
                "shortcuts_after_one_esc": sc_after, "wizard_after_one_esc": wizard_after,
                "yard_after": yard,
                "expected_if_bug": "shortcuts AND wizard both closed by single Escape (index.html:5409 closes every visible layer; wizard handler at :8094 fires unconditionally)"})
        except Exception:
            log_result("F07_escape_stacking", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F08 guide doc-drift: drive every documented key ----------------
        current_flow[0] = "F08"
        try:
            page.keyboard.press("F1"); settle(page, 350)
            rows = page.evaluate("""() => Array.from(document.querySelectorAll('#shortcuts-modal .sc-row')).map(r => ({
                desc: r.querySelector('.sc-desc') ? r.querySelector('.sc-desc').textContent.trim() : '',
                keys: Array.from(r.querySelectorAll('.sc-keys kbd')).map(k => k.textContent.trim())
            }))""")
            shot(page, "f08a_guide_open.png")
            page.keyboard.press("Escape"); settle(page, 300)
            # canary object so selection/arrow/delete keys have a target (real UI click)
            if page.query_selector("[data-type]"):
                page.click("[data-type]", timeout=4000)
                settle(page, 400)
            def probe(key, args=None):
                before = page.evaluate("""() => {
                    const s = window._bydState;
                    return {
                        grid: window._bydScene ? window._bydScene.children.some(c => c.isGridHelper && c.visible) : null,
                        sel: s ? s.selectedId : null,
                        n: s ? s.objects.size : null,
                        objX: s && s.selectedId !== null && s.objects.get(s.selectedId) ? s.objects.get(s.selectedId).position.x : null,
                    };
                }""")
                page.keyboard.press(key); settle(page, 220)
                after = page.evaluate("""() => {
                    const s = window._bydState;
                    return {
                        grid: window._bydScene ? window._bydScene.children.some(c => c.isGridHelper && c.visible) : null,
                        sel: s ? s.selectedId : null,
                        n: s ? s.objects.size : null,
                        objX: s && s.selectedId !== null && s.objects.get(s.selectedId) ? s.objects.get(s.selectedId).position.x : null,
                        view: document.getElementById('view-toggle') ? document.getElementById('view-toggle').textContent : null,
                    };
                }""")
                return before, after
            probes = {}
            for key in ["g", "G", "v", "V", "b", "B", "r", "R", "t", "T", "x", "X",
                        "1", "2", "3", "4", "5", "6", "[", "]", "Delete", "m", "M", "?", "F1"]:
                b, a = probe(key)
                probes[key] = {"before": b, "after": a}
            shot(page, "f08b_after_probes.png")
            # summarize which keys produced NO observable change anywhere
            inert = []
            for key, pv in probes.items():
                b, a = pv["before"], pv["after"]
                changed = (b["grid"] != a["grid"] or b["sel"] != a["sel"] or b["n"] != a["n"] or b["objX"] != a["objX"])
                if not changed:
                    inert.append(key)
            log_result("F08_doc_drift", True, {
                "guide_rows": len(rows), "inert_keys_no_state_change": inert,
                "probes": {k: {"grid": (v["before"]["grid"], v["after"]["grid"]),
                               "sel": (v["before"]["sel"], v["after"]["sel"]),
                               "n": (v["before"]["n"], v["after"]["n"]),
                               "objX": (v["before"]["objX"], v["after"]["objX"])} for k, v in probes.items()},
                "note": "M/?/F1/V/B/T/X change UI outside _bydState; 'inert' needs manual read. Full toggles verified per-key below in claims."})
        except Exception:
            log_result("F08_doc_drift", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F09 corrupt/truncated JSON via real file input ----------------
        current_flow[0] = "F09"
        try:
            trunc = os.path.join(OUT, "truncated_design.json")
            with open(trunc, "w") as f:
                f.write('{"version":4,"yard":{"width":50,"depth":100},"objects":[{"id":1,"type":"tree_deciduous"')
            page.click("#btn-load", timeout=4000)
            settle(page, 500)
            page.set_input_files("#import-input", trunc)
            settle(page, 800)
            tv = toast_visible(page)
            tt = toast_text(page)
            objcount = page.evaluate("() => window._bydState.objects.size")
            shot(page, "f09_corrupt_json_toast.png")
            log_result("F09_corrupt_json", tv and objcount is not None, {
                "toast_visible": tv, "toast_text": tt, "objects_after": objcount,
                "expected": "error toast, no state change"})
        except Exception:
            log_result("F09_corrupt_json", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F10 loadDesign code-path probes (LABELED probes, not UI) ----------------
        current_flow[0] = "F10"
        try:
            before_yard = page.evaluate("() => { const s = window._bydState; return {w: s.yard.width, d: s.yard.depth}; }")
            # probe 1: absurd yard dimensions
            page.evaluate("() => window._bydLoadDesign({version:4, objects:[], yard:{width:1e300, depth:1e300, shape:'rectangle'}, nextId:1, terrain:null})")
            settle(page, 700)
            after1 = page.evaluate("() => { const s = window._bydState; return {w: s.yard.width, d: s.yard.depth}; }")
            shot(page, "f10a_absurd_yard.png")
            errs1 = [e for f, k, e in console_errors if f in ("F10",)]
            # probe 2: duplicate/oversized ids
            page.evaluate("() => window._bydLoadDesign({version:4, objects:[{id:7,type:'tree_deciduous',params:{height:20},position:{x:0,z:0},rotation:0,scale:1},{id:7,type:'bench',params:{length:6},position:{x:5,z:5},rotation:0,scale:1},{id:-3,type:'bench',params:{length:6},position:{x:-5,z:5},rotation:0,scale:1}], yard:{width:50,depth:100}, nextId:7, terrain:null})")
            settle(page, 900)
            after2 = page.evaluate("() => { const s = window._bydState; return {n: s.objects.size, ids: Array.from(s.objects.keys()), nextId: s.nextId}; }")
            shot(page, "f10b_dup_ids.png")
            # probe 3: null / bad params
            page.evaluate("() => window._bydLoadDesign({version:4, objects:[{id:1,type:'tree_deciduous',params:null,position:{x:1,z:1}},{id:2,type:'nope_unknown',params:{},position:{x:2,z:2}},{id:3,type:'bench',params:{length:'six'},position:{x:3,z:3}}], yard:{width:50,depth:100}, nextId:4, terrain:[1,2,3]})")
            settle(page, 900)
            after3 = page.evaluate("() => { const s = window._bydState; return {n: s.objects.size, yard: s.yard, segs: s.terrainSegs, tLen: s.terrain ? s.terrain.length : 0}; }")
            shot(page, "f10c_bad_params.png")
            errs_all = [e for f, k, e in console_errors]
            log_result("F10_load_probes", True, {
                "before_yard": before_yard, "after_absurd_yard": after1,
                "after_dup_ids": after2, "after_bad_params": after3,
                "pageerrors_during_probes": errs_all[-6:],
                "expected_1": "yard clamped to sane max (10-500)",
                "expected_2": "3 distinct objects loaded",
                "expected_3": "bad objects rejected, terrainSegs reset to 200 default when terrain rejected"})
        except Exception:
            log_result("F10_load_probes", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F11 Escape stacking: help -> shortcuts, one Escape ----------------
        current_flow[0] = "F11"
        try:
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector("#cmd-palette-input", timeout=20000)
            settle(page, 1800)
            page.keyboard.press("Escape"); settle(page, 300)  # wizard if any
            page.click("#btn-help", timeout=4000); settle(page, 300)
            h1 = page.evaluate("() => document.getElementById('help-modal').classList.contains('visible')")
            page.click("#help-open-shortcuts", timeout=4000); settle(page, 400)
            h2 = page.evaluate("() => document.getElementById('help-modal').classList.contains('visible')")
            s2 = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
            shot(page, "f11a_help_then_shortcuts.png")
            page.keyboard.press("Escape"); settle(page, 400)
            h3 = page.evaluate("() => document.getElementById('help-modal').classList.contains('visible')")
            s3 = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
            shot(page, "f11b_after_escape.png")
            log_result("F11_escape_stacking_modals", True, {
                "help_open": h1, "help_after_link": h2, "shortcuts_after_link": s2,
                "help_after_one_esc": h3, "shortcuts_after_one_esc": s3,
                "expected_if_bug": "BOTH closed by a single Escape (index.html:5413-5414 has no topmost-only break)"})
        except Exception:
            log_result("F11_escape_stacking_modals", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F12 rapid M toggles x8 ----------------
        current_flow[0] = "F12"
        try:
            mode0 = page.evaluate("() => document.body.className")
            for _ in range(8):
                page.keyboard.press("m"); settle(page, 90)
            settle(page, 600)
            mode1 = page.evaluate("() => document.body.className")
            mode_cur = page.evaluate("() => window.getCurrentMode ? window.getCurrentMode() : null")
            toast = toast_text(page)
            shot(page, "f12_after_rapid_m.png")
            expected_class = "byd-basic-mode" if "byd-basic-mode" in mode0 else "byd-advanced-mode"
            log_result("F12_rapid_mode_toggle", expected_class in mode1, {
                "mode_before": mode0, "mode_after": mode1, "getCurrentMode": mode_cur,
                "toast": toast,
                "expected": "8 toggles = back to starting mode; exactly one body mode class"})
        except Exception:
            log_result("F12_rapid_mode_toggle", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F13 resize 1280x800 / 1920x1080 ----------------
        current_flow[0] = "F13"
        try:
            page.set_viewport_size({"width": 1280, "height": 800}); settle(page, 900)
            cv1 = page.evaluate("() => { const c = document.querySelector('#viewport'); const r = c.getBoundingClientRect(); return {w: c.width|0, h: c.height|0, rw: r.width|0, rh: r.height|0}; }")
            shot(page, "f13a_1280x800.png")
            page.set_viewport_size({"width": 1920, "height": 1080}); settle(page, 900)
            cv2 = page.evaluate("() => { const c = document.querySelector('#viewport'); const r = c.getBoundingClientRect(); return {w: c.width|0, h: c.height|0, rw: r.width|0, rh: r.height|0}; }")
            shot(page, "f13b_1920x1080.png")
            errs = [e for f, k, e in console_errors if k == "pageerror"]
            log_result("F13_resize", True, {
                "canvas_at_1280": cv1, "canvas_at_1920": cv2,
                "pageerrors": errs[-4:],
                "expected": "canvas backing size tracks viewport within a frame or two; no pageerrors"})
        except Exception:
            log_result("F13_resize", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F14 Ctrl+Shift+P perf panel ----------------
        current_flow[0] = "F14"
        try:
            page.keyboard.press("Control+Shift+KeyP"); settle(page, 500)
            # find perf panel element heuristically
            pv = page.evaluate("""() => {
                const el = document.querySelector('.perf-panel, #perf-panel, [id*="perf"]');
                if (!el) return null;
                const cs = getComputedStyle(el);
                return {id: el.id || el.className, display: cs.display, visible: el.offsetParent !== null};
            }""")
            shot(page, "f14a_perf_panel.png")
            page.keyboard.press("Control+Shift+KeyP"); settle(page, 500)
            pv2 = page.evaluate("""() => {
                const el = document.querySelector('.perf-panel, #perf-panel, [id*="perf"]');
                if (!el) return null;
                const cs = getComputedStyle(el);
                return {id: el.id || el.className, display: cs.display, visible: el.offsetParent !== null};
            }""")
            shot(page, "f14b_perf_closed.png")
            log_result("F14_ctrl_shift_p", True, {"after_first": pv, "after_second": pv2,
                "expected": "perf panel toggles open then closed (guide says 'Performance panel')"})
        except Exception:
            log_result("F14_ctrl_shift_p", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F15 tab order / focus trap in help modal ----------------
        current_flow[0] = "F15"
        try:
            page.click("#btn-help", timeout=4000); settle(page, 300)
            focus_seq = []
            for _ in range(10):
                page.keyboard.press("Tab"); settle(page, 80)
                focus_seq.append(page.evaluate("() => { const a = document.activeElement; return a ? (a.id || a.tagName + ':' + (a.className || '').toString().slice(0, 20)) : 'none'; }"))
            shot(page, "f15_tab_order_help.png")
            page.keyboard.press("Escape"); settle(page, 300)
            focus_back = page.evaluate("() => { const a = document.activeElement; return a ? (a.id || a.tagName) : 'none'; }")
            log_result("F15_tab_trap", True, {
                "focus_sequence_after_open": focus_seq,
                "focus_after_escape": focus_back,
                "expected_if_bug": "Tab escapes the modal into background topbar (no focus trap); Escape should restore trigger focus"})
        except Exception:
            log_result("F15_tab_trap", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F16 onboarding progressive hint delay ----------------
        current_flow[0] = "F16"
        try:
            page.evaluate("() => localStorage.clear()")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector("#cmd-palette-input", timeout=20000)
            settle(page, 1500)
            # dismiss wizard (real click on skip) then welcome prompt handler
            page.click("#wizard-skip", timeout=4000); settle(page, 800)
            wp = page.evaluate("() => document.getElementById('welcome-prompt').classList.contains('visible')")
            if wp:
                page.click("#wp-scratch", timeout=4000); settle(page, 400)
            t0 = time.time()
            shown_at = None
            for _ in range(100):
                page.wait_for_timeout(500)
                if page.evaluate("() => document.getElementById('progressive-hint').classList.contains('visible')"):
                    shown_at = time.time() - t0
                    break
            shot(page, "f16_progressive_hint.png")
            hint_text = page.evaluate("() => { const el = document.getElementById('progressive-hint'); return el ? el.textContent : null; }")
            log_result("F16_hint_delay", True, {
                "welcome_prompt_seen": wp, "hint_shown_after_s": shown_at,
                "hint_text": hint_text,
                "expected": "~30s per HINT_DELAY (index.html:15370) — 20-40s passes"})
        except Exception:
            log_result("F16_hint_delay", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F17 empty-state hints (left panel categories) ----------------
        current_flow[0] = "F17"
        try:
            tabs = page.evaluate("() => Array.from(document.querySelectorAll('.cat-tab, .mi-tab, [data-cat]')).map(t => ({cls: t.className.slice(0, 40), txt: (t.textContent || '').trim().slice(0, 24), id: t.id}))")
            log_result("F17_empty_state_scan", True, {
                "category_tabs_found": tabs[:12],
                "note": "empty-state only renders when a category filter yields zero items; checked empty_stateHTML usage at index.html:15642"})
            shot(page, "f17_left_panel.png")
        except Exception:
            log_result("F17_empty_state_scan", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F18 Alt+Tab cycles objects ----------------
        current_flow[0] = "F18"
        try:
            # add two objects via real clicks on catalog
            cards = page.query_selector_all("[data-type]")
            n_before = page.evaluate("() => window._bydState.objects.size")
            if len(cards) >= 2:
                cards[0].click(); settle(page, 300)
                cards[1].click(); settle(page, 300)
            n_after = page.evaluate("() => window._bydState.objects.size")
            sel0 = page.evaluate("() => window._bydState.selectedId")
            page.keyboard.press("Alt+Tab"); settle(page, 250)
            sel1 = page.evaluate("() => window._bydState.selectedId")
            page.keyboard.press("Alt+Shift+Tab"); settle(page, 250)
            sel2 = page.evaluate("() => window._bydState.selectedId")
            shot(page, "f18_alttab_cycle.png")
            log_result("F18_alttab_cycle", n_after > n_before and sel1 != sel0, {
                "objects_before": n_before, "objects_after": n_after,
                "sel0": sel0, "sel_after_alttab": sel1, "sel_after_shift_alttab": sel2})
        except Exception:
            log_result("F18_alttab_cycle", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F19 F1 during wizard input typing (suspect 2) ----------------
        current_flow[0] = "F19"
        try:
            page.evaluate("() => localStorage.clear()")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector("#cmd-palette-input", timeout=20000)
            settle(page, 1800)
            page.click("#wizard-next", timeout=4000); settle(page, 300)
            page.click("#wiz-width", timeout=4000)
            page.keyboard.type("45", delay=40)
            page.keyboard.press("F1"); settle(page, 400)
            sc = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
            val = page.evaluate("() => document.getElementById('wiz-width').value")
            shot(page, "f19_f1_in_wizard_input.png")
            # cleanup: single Escape should close BOTH per suspect; verify
            page.keyboard.press("Escape"); settle(page, 400)
            sc2 = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
            wd2 = page.evaluate("() => getComputedStyle(document.getElementById('wizard')).display")
            log_result("F19_f1_in_wizard_input", True, {
                "shortcuts_opened_while_typing_in_wizard": sc, "wiz_width_value": val,
                "shortcuts_after_esc": sc2, "wizard_after_esc": wd2,
                "expected_if_bug": "F1 opens guide over the wizard while typing; one Escape nukes both layers"})
        except Exception:
            log_result("F19_f1_in_wizard_input", False, {"error": traceback.format_exc()[-400:]})

        browser.close()

    # final console error dump
    with open(os.path.join(OUT, "console_errors.json"), "w") as f:
        json.dump([{"flow": f, "kind": k, "text": t} for f, k, t in console_errors], f, indent=1)
    print("\n=== CONSOLE ERRORS (pageerror only) ===")
    for f, k, t in console_errors:
        if k == "pageerror":
            print(f"[{f}] {t}")
    print("\nflows:", len(flows_run), flows_run)

if __name__ == "__main__":
    run()
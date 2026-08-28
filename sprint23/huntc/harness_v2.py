"""Sprint 23 Bug Hunt C — persistence & edge cases, harness v2 (READ-ONLY hunter).

REAL input events only for click/key paths. page.evaluate used ONLY for
state reads (DOM/storage) and labeled code-path probes (F10).
Port 8303. Output: results.jsonl, PNG evidence, console_errors.json.
"""
import json, time, traceback, os
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8303/index.html"
OUT = "/root/backyard-designer/sprint23/huntc"
RESULTS = os.path.join(OUT, "results.jsonl")
os.makedirs(OUT, exist_ok=True)

flows_run = []
console_errors = []
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
    print(("PASS " if ok else "INFO ") + flow + " :: " + json.dumps(data, default=str)[:500])

def shot(page, name):
    path = os.path.join(OUT, name)
    page.screenshot(path=path)
    return name

def settle(page, ms=350):
    page.wait_for_timeout(ms)

def app_ready(page):
    page.wait_for_selector("#cmd-palette-input", state="attached", timeout=20000)
    settle(page, 1800)

VISIBLE_OVERLAYS = """() => {
    const out = [];
    for (const id of ['wizard','help-modal','shortcuts-modal','share-modal','cmd-palette-overlay','templates-modal','gallery-modal','welcome-prompt']) {
        const el = document.getElementById(id);
        if (!el) continue;
        const vis = id === 'wizard' ? getComputedStyle(el).display !== 'none' : el.classList.contains('visible');
        if (vis) out.push(id);
    }
    return out;
}"""

def dismiss_overlays(page, max_esc=3):
    """Close any blocking overlay using REAL Escape presses only."""
    for _ in range(max_esc):
        if not page.evaluate(VISIBLE_OVERLAYS):
            return []
        page.keyboard.press("Escape")
        settle(page, 350)
    return page.evaluate(VISIBLE_OVERLAYS)

def toast_text(page):
    return page.evaluate("() => { const t = document.getElementById('toast'); return t ? t.textContent : null; }")

def toast_visible(page):
    return page.evaluate("() => { const t = document.getElementById('toast'); return t ? t.classList.contains('visible') : null; }")

def add_two_objects(page):
    """Add two objects via REAL clicks on the catalog (.lib-item cards)."""
    n0 = page.evaluate("() => window._bydState ? window._bydState.objects.size : null")
    cards = page.query_selector_all(".lib-item")
    if len(cards) >= 2:
        cards[0].click(); settle(page, 300)
        cards[1].click(); settle(page, 300)
    n1 = page.evaluate("() => window._bydState.objects.size")
    return n0, n1

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        page = ctx.new_page()
        page.on("console", log_console)
        page.on("pageerror", lambda e: console_errors.append((current_flow[0], "pageerror", str(e)[:300])))

        # ---------------- F01 boot & console ----------------
        current_flow[0] = "F01"
        try:
            page.goto(BASE, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("#cmd-palette-input", state="attached", timeout=20000)
            settle(page, 2500)
            wizard_disp = page.evaluate("() => getComputedStyle(document.getElementById('wizard')).display")
            welcome_vis = page.evaluate("() => document.getElementById('welcome-prompt').classList.contains('visible')")
            has_continue = page.evaluate("() => !!document.getElementById('wizard-continue')")
            shot(page, "f01_boot.png")
            log_result("F01_boot", True, {
                "wizard_display": wizard_disp, "welcome_visible": welcome_vis,
                "autosave_continue_btn": has_continue,
                "pageerrors": [e for f, k, e in console_errors if k == "pageerror"]})
        except Exception:
            log_result("F01_boot", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F02 wizard complete (real clicks) ----------------
        current_flow[0] = "F02"
        try:
            page.evaluate("() => localStorage.clear()")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector("#cmd-palette-input", state="attached", timeout=20000)
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
            log_result("F02_wizard_complete", wd2 == "none" and isinstance(yard, dict), {
                "wizard_before": wd, "wizard_after": wd2, "yard_after": yard,
                "expected": "yard 60x80, wizard hidden"})
        except Exception:
            log_result("F02_wizard_complete", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F03 autosave -> reload -> Continue restores ----------------
        current_flow[0] = "F03"
        try:
            left = dismiss_overlays(page)
            n0, n1 = add_two_objects(page)
            settle(page, 2700)  # autosave debounce 2s
            autosave_raw = page.evaluate("() => localStorage.getItem('backyard-design-autosave')")
            autosave = json.loads(autosave_raw) if autosave_raw else None
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector("#cmd-palette-input", state="attached", timeout=20000)
            settle(page, 2000)
            wd = page.evaluate("() => getComputedStyle(document.getElementById('wizard')).display")
            has_continue = page.evaluate("() => !!document.getElementById('wizard-continue')")
            shot(page, "f03a_reload_wizard.png")
            if has_continue:
                page.click("#wizard-continue", timeout=4000)
                settle(page, 900)
            restored_n = page.evaluate("() => window._bydState.objects.size")
            toast = toast_text(page)
            shot(page, "f03b_after_continue.png")
            log_result("F03_autosave_restore", True, {
                "objects_added": (n0, n1), "autosave_objects": len((autosave or {}).get("objects", [])),
                "autosave_yard": (autosave or {}).get("yard"),
                "wizard_after_reload": wd, "continue_btn": has_continue,
                "restored_object_count": restored_n, "toast": toast,
                "expected": "wizard returns (mode persisted, not design); Continue restores 2 objects"})
        except Exception:
            log_result("F03_autosave_restore", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F04/F05 palette open + nav (quick re-verify) ----------------
        current_flow[0] = "F04"
        try:
            dismiss_overlays(page)
            page.keyboard.press("Control+k"); settle(page, 300)
            pal = page.evaluate("() => document.getElementById('cmd-palette-overlay').classList.contains('visible')")
            page.keyboard.press("Escape"); settle(page, 250)
            pal2 = page.evaluate("() => document.getElementById('cmd-palette-overlay').classList.contains('visible')")
            log_result("F04_palette_esc", pal and not pal2, {"open_after_ctrlk": pal, "open_after_esc": pal2})
        except Exception:
            log_result("F04_palette_esc", False, {"error": traceback.format_exc()[-400:]})

        current_flow[0] = "F05"
        try:
            page.keyboard.press("Control+k"); settle(page, 300)
            page.keyboard.type("view", delay=25); settle(page, 250)
            n1 = page.evaluate("() => document.querySelectorAll('#cmd-palette-results .cmd-item').length")
            page.keyboard.press("ArrowDown"); page.keyboard.press("ArrowDown"); settle(page, 150)
            sel_dn = page.evaluate("() => (document.querySelector('#cmd-palette-results .cmd-item.selected')||{}).textContent")
            page.keyboard.press("ArrowUp"); settle(page, 150)
            sel_up = page.evaluate("() => (document.querySelector('#cmd-palette-results .cmd-item.selected')||{}).textContent")
            page.keyboard.press("Enter"); settle(page, 500)
            closed = page.evaluate("() => !document.getElementById('cmd-palette-overlay').classList.contains('visible')")
            log_result("F05_palette_nav", n1 > 0 and closed, {
                "results_for_view": n1, "sel_down2": (sel_dn or "").strip()[:40],
                "sel_up": (sel_up or "").strip()[:40], "closed_after_enter": closed})
        except Exception:
            log_result("F05_palette_nav", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F06 F1 fires while typing in palette input ----------------
        current_flow[0] = "F06"
        try:
            dismiss_overlays(page)
            page.keyboard.press("Control+k"); settle(page, 300)
            focused = page.evaluate("() => document.activeElement && document.activeElement.id")
            page.keyboard.type("terrain", delay=25); settle(page, 200)
            page.keyboard.press("F1"); settle(page, 400)
            sc = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
            val = page.evaluate("() => document.getElementById('cmd-palette-input').value")
            shot(page, "f06_f1_during_typing.png")
            dismiss_overlays(page)
            log_result("F06_f1_during_typing", True, {
                "palette_focus": focused, "shortcuts_opened_while_typing": sc,
                "input_value_after_f1": val,
                "expected_if_bug": "guide opens over palette mid-typing; user's first Escape then only closes guide — flow interrupted"})
        except Exception:
            log_result("F06_f1_during_typing", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F07 wizard + shortcuts modal, single Escape ----------------
        current_flow[0] = "F07"
        try:
            page.evaluate("() => localStorage.clear()")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector("#cmd-palette-input", state="attached", timeout=20000)
            settle(page, 2000)
            page.keyboard.press("F1"); settle(page, 400)
            state_before = page.evaluate(VISIBLE_OVERLAYS)
            shot(page, "f07a_wizard_plus_shortcuts.png")
            page.keyboard.press("Escape"); settle(page, 500)
            state_after = page.evaluate(VISIBLE_OVERLAYS)
            yard = page.evaluate("() => { const s = window._bydState; return s ? {w: s.yard.width, d: s.yard.depth} : null; }")
            shot(page, "f07b_after_one_escape.png")
            log_result("F07_escape_stacking", True, {
                "before": state_before, "after_one_esc": state_after, "yard_after": yard,
                "expected_if_bug": "single Escape closes BOTH shortcuts guide and wizard; wizard Escape handler at index.html:8094 is unconditional"})
        except Exception:
            log_result("F07_escape_stacking", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F08 doc-drift: drive every documented key, real events ----------------
        current_flow[0] = "F08"
        try:
            page.keyboard.press("F1"); settle(page, 350)
            rows = page.evaluate("""() => Array.from(document.querySelectorAll('#shortcuts-modal .sc-row')).map(r => ({
                desc: r.querySelector('.sc-desc') ? r.querySelector('.sc-desc').textContent.trim() : '',
                keys: Array.from(r.querySelectorAll('.sc-keys kbd')).map(k => k.textContent.trim())
            }))""")
            shot(page, "f08a_guide_open.png")
            dismiss_overlays(page)
            n0, n1 = add_two_objects(page)
            def snap():
                return page.evaluate("""() => {
                    const s = window._bydState;
                    const canvas = document.querySelector('#viewport canvas');
                    const grid = window._bydScene ? window._bydScene.children.filter(c => c.type === 'GridHelper').map(c => c.visible) : null;
                    const activeBrush = document.querySelector('.terrain-mode-btn.active');
                    return {
                        grid: grid,
                        sel: s ? s.selectedId : null,
                        n: s ? s.objects.size : null,
                        objX: s && s.selectedId !== null && s.objects.get(s.selectedId) ? Math.round(s.objects.get(s.selectedId).position.x * 100) / 100 : null,
                        body: document.body.className,
                        terrainMode: document.getElementById('terrain-btn') ? document.getElementById('terrain-btn').getAttribute('aria-pressed') : null,
                        brush: (document.getElementById('terrain-brush-val') || {}).textContent || null,
                        activeBrush: activeBrush ? activeBrush.getAttribute('data-tmode') : null,
                        view2d: (document.querySelector('#view-toggle .active, #view-toggle [aria-pressed="true"]') || {}).textContent || null,
                        toast: (document.getElementById('toast') || {}).textContent || null,
                    };
                }""")
            probes = {}
            for key in ["g", "v", "b", "r", "t", "x", "1", "5", "[", "]", "ArrowLeft", "Delete", "m", "?"]:
                before = snap()
                page.keyboard.press(key); settle(page, 260)
                after = snap()
                probes[key] = {"before": before, "after": after}
            shot(page, "f08b_after_probes.png")
            changed_summary = {}
            for key, pv in probes.items():
                b, a = pv["before"], pv["after"]
                diffs = [k for k in b if json.dumps(b[k], default=str) != json.dumps(a[k], default=str)]
                changed_summary[key] = diffs
            log_result("F08_doc_drift", True, {
                "guide_rows": len(rows), "guide_rows_detail": rows,
                "changed_fields_per_key": changed_summary,
                "objects_added": (n0, n1),
                "note": "keys whose expected field shows NO change = doc-drift or dead handler candidates"})
        except Exception:
            log_result("F08_doc_drift", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F09 corrupt/truncated JSON via real Load flow ----------------
        current_flow[0] = "F09"
        try:
            left = dismiss_overlays(page)
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
            yard = page.evaluate("() => window._bydState.yard")
            shot(page, "f09_corrupt_json_toast.png")
            log_result("F09_corrupt_json", tv is not None, {
                "leftover_overlays": left, "toast_visible": tv, "toast_text": tt,
                "objects_after": objcount, "yard_after": yard,
                "expected": "clear error toast; yard+objects unchanged"})
        except Exception:
            log_result("F09_corrupt_json", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F10 labeled loadDesign probes (code-path only) ----------------
        current_flow[0] = "F10"
        try:
            dismiss_overlays(page)
            # probe A: duplicate + negative ids
            page.evaluate("() => window._bydLoadDesign({version:4, objects:[{id:7,type:'tree_deciduous',params:{height:20},position:{x:0,z:0},rotation:0,scale:1},{id:7,type:'bench',params:{length:6},position:{x:5,z:5},rotation:0,scale:1},{id:-3,type:'bench',params:{length:6},position:{x:-5,z:5},rotation:0,scale:1}], yard:{width:50,depth:100}, nextId:7, terrain:null})")
            settle(page, 900)
            afterA = page.evaluate("() => { const s = window._bydState; return {n: s.objects.size, ids: Array.from(s.objects.keys()), nextId: s.nextId}; }")
            toastA = toast_text(page)
            shot(page, "f10a_dup_ids.png")
            # probe B: bad params / unknown type / bogus terrain
            page.evaluate("() => window._bydLoadDesign({version:4, objects:[{id:1,type:'tree_deciduous',params:null,position:{x:1,z:1}},{id:2,type:'nope_unknown',params:{},position:{x:2,z:2}},{id:3,type:'bench',params:{length:'six'},position:{x:3,z:3}}], yard:{width:50,depth:100}, nextId:4, terrain:[1,2,3]})")
            settle(page, 900)
            afterB = page.evaluate("() => { const s = window._bydState; return {n: s.objects.size, segs: s.terrainSegs, tLen: s.terrain ? s.terrain.length : 0}; }")
            toastB = toast_text(page)
            shot(page, "f10b_bad_params.png")
            # probe C: non-numeric id (string) + missing id
            page.evaluate("() => window._bydLoadDesign({version:4, objects:[{id:'abc',type:'bench',params:{length:6},position:{x:1,z:1}},{type:'tree_deciduous',params:{height:10},position:{x:2,z:2}}], yard:{width:50,depth:100}, nextId:1, terrain:null})")
            settle(page, 900)
            afterC = page.evaluate("() => { const s = window._bydState; return {n: s.objects.size, ids: Array.from(s.objects.keys()), nextId: s.nextId}; }")
            toastC = toast_text(page)
            shot(page, "f10c_string_ids.png")
            log_result("F10_load_probes", True, {
                "probeA_dup_ids": afterA, "toastA": toastA,
                "probeB_bad_params": afterB, "toastB": toastB,
                "probeC_string_id": afterC, "toastC": toastC,
                "expected_A": "3 objects (dup id 7 must not silently overwrite)",
                "expected_B": "0 objects kept, segs reset to 200, no crash",
                "expected_C": "both objects get fresh numeric ids"})
        except Exception:
            log_result("F10_load_probes", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F11 help -> shortcuts link, single Escape ----------------
        current_flow[0] = "F11"
        try:
            dismiss_overlays(page)
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
                "expected_if_bug": "BOTH closed by one Escape (index.html:5411-5414 closes every visible layer, no topmost-only logic)"})
        except Exception:
            log_result("F11_escape_stacking_modals", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F12 rapid M x8 ----------------
        current_flow[0] = "F12"
        try:
            mode0 = page.evaluate("() => document.body.className")
            for _ in range(8):
                page.keyboard.press("m"); settle(page, 90)
            settle(page, 600)
            mode1 = page.evaluate("() => document.body.className")
            mode_cur = page.evaluate("() => window.getCurrentMode ? window.getCurrentMode() : null")
            ncls = len([c for c in mode1.split() if c.startswith("byd-")])
            log_result("F12_rapid_mode_toggle", ("byd-basic-mode" in mode0) == ("byd-basic-mode" in mode1) and ncls == 1, {
                "mode_before": mode0, "mode_after": mode1, "mode_classes_count": ncls,
                "getCurrentMode": mode_cur, "expected": "even toggles return to start; exactly one mode class"})
        except Exception:
            log_result("F12_rapid_mode_toggle", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F13 resize 1280x800 / 1920x1080 ----------------
        current_flow[0] = "F13"
        try:
            page.set_viewport_size({"width": 1280, "height": 800}); settle(page, 1000)
            cv1 = page.evaluate("() => { const c = document.querySelector('#viewport canvas'); return c ? {w: c.width, h: c.height} : null; }")
            shot(page, "f13a_1280x800.png")
            page.set_viewport_size({"width": 1920, "height": 1080}); settle(page, 1000)
            cv2 = page.evaluate("() => { const c = document.querySelector('#viewport canvas'); return c ? {w: c.width, h: c.height} : null; }")
            shot(page, "f13b_1920x1080.png")
            errs = [e for f, k, e in console_errors if k == "pageerror"]
            log_result("F13_resize", True, {
                "canvas_at_1280": cv1, "canvas_at_1920": cv2, "pageerrors": errs[-4:],
                "expected": "canvas backing store tracks viewport; no pageerrors"})
        except Exception:
            log_result("F13_resize", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F14 Ctrl+Shift+P perf panel ----------------
        current_flow[0] = "F14"
        try:
            d0 = page.evaluate("() => getComputedStyle(document.getElementById('perf-panel')).display")
            page.keyboard.press("Control+Shift+KeyP"); settle(page, 500)
            d1 = page.evaluate("() => getComputedStyle(document.getElementById('perf-panel')).display")
            page.keyboard.press("Control+Shift+KeyP"); settle(page, 500)
            d2 = page.evaluate("() => getComputedStyle(document.getElementById('perf-panel')).display")
            shot(page, "f14a_perf_panel.png")
            log_result("F14_ctrl_shift_p", d0 == "none" and d1 == "block" and d2 == "none", {
                "before": d0, "after_first": d1, "after_second": d2,
                "expected": "toggles open then closed; guide label 'Performance panel' correct"})
        except Exception:
            log_result("F14_ctrl_shift_p", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F15 tab order / focus management in help modal ----------------
        current_flow[0] = "F15"
        try:
            dismiss_overlays(page)
            page.click("#btn-help", timeout=4000); settle(page, 300)
            focus_seq = []
            for _ in range(8):
                page.keyboard.press("Tab"); settle(page, 80)
                focus_seq.append(page.evaluate("() => { const a = document.activeElement; return a ? (a.id || a.tagName + ':' + String(a.className).slice(0, 18)) : 'none'; }"))
            shot(page, "f15_tab_order_help.png")
            page.keyboard.press("Escape"); settle(page, 300)
            focus_back = page.evaluate("() => { const a = document.activeElement; return a ? (a.id || a.tagName) : 'none'; }")
            # focus while modal open: can user reach background topbar?
            page.click("#btn-help", timeout=4000); settle(page, 250)
            seq2 = []
            for _ in range(14):
                page.keyboard.press("Tab"); settle(page, 70)
                seq2.append(page.evaluate("() => { const a = document.activeElement; const inModal = a && a.closest && a.closest('#help-modal'); return (inModal ? 'IN:' : 'OUT:') + (a ? (a.id || a.tagName) : 'none'); }"))
            outs = [s for s in seq2 if s.startswith("OUT")]
            page.keyboard.press("Escape"); settle(page, 250)
            log_result("F15_tab_trap", True, {
                "focus_seq_first8": focus_seq, "focus_after_escape": focus_back,
                "tab_escape_modal_to_background_count": len(outs),
                "tab_seq_full": seq2,
                "expected_if_bug": "Tab cycles OUT of the open modal into background topbar (no focus trap)"})
        except Exception:
            log_result("F15_tab_trap", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F16 onboarding progressive hint delay ----------------
        current_flow[0] = "F16"
        try:
            page.evaluate("() => localStorage.clear()")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector("#cmd-palette-input", state="attached", timeout=20000)
            settle(page, 1500)
            page.click("#wizard-skip", timeout=4000); settle(page, 800)
            wp = page.evaluate("() => document.getElementById('welcome-prompt').classList.contains('visible')")
            if wp:
                page.click("#wp-scratch", timeout=4000); settle(page, 400)
            t0 = time.time()
            shown_at = None
            for _ in range(90):
                page.wait_for_timeout(500)
                if page.evaluate("() => document.getElementById('progressive-hint').classList.contains('visible')"):
                    shown_at = round(time.time() - t0, 1)
                    break
            hint_text = page.evaluate("() => { const el = document.getElementById('progressive-hint'); return el ? el.textContent : null; }")
            shot(page, "f16_progressive_hint.png")
            log_result("F16_hint_delay", True, {
                "welcome_prompt_seen": wp, "hint_shown_after_s": shown_at, "hint_text": hint_text,
                "expected": "~30s per HINT_DELAY (index.html:15370); 20-40s passes"})
        except Exception:
            log_result("F16_hint_delay", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F17 catalog inventory + empty-state check ----------------
        current_flow[0] = "F17"
        try:
            inv = page.evaluate("""() => {
                const secs = Array.from(document.querySelectorAll('.cat-title')).map(t => t.textContent.trim());
                const items = Array.from(document.querySelectorAll('.lib-item')).map(i => (i.textContent || '').trim().slice(0, 30));
                return {sections: secs, item_count: items.length, first_items: items.slice(0, 8)};
            }""")
            shot(page, "f17_left_panel.png")
            log_result("F17_catalog_scan", True, {
                **inv, "expected": "sections present, items > 0; empty-state path only when a category has zero items"})
        except Exception:
            log_result("F17_catalog_scan", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F18 Alt+Tab cycles objects ----------------
        current_flow[0] = "F18"
        try:
            dismiss_overlays(page)
            n0, n1 = add_two_objects(page)
            sel0 = page.evaluate("() => window._bydState.selectedId")
            page.keyboard.press("Alt+Tab"); settle(page, 250)
            sel1 = page.evaluate("() => window._bydState.selectedId")
            page.keyboard.press("Alt+Shift+Tab"); settle(page, 250)
            sel2 = page.evaluate("() => window._bydState.selectedId")
            shot(page, "f18_alttab_cycle.png")
            log_result("F18_alttab_cycle", n1 > n0, {
                "objects": (n0, n1), "sel0": sel0, "after_alttab": sel1, "after_shift_alttab": sel2,
                "expected": "Alt+Tab cycles to the other object; Shift reverses"})
        except Exception:
            log_result("F18_alttab_cycle", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F19 F1 while typing in wizard input ----------------
        current_flow[0] = "F19"
        try:
            page.evaluate("() => localStorage.clear()")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector("#cmd-palette-input", state="attached", timeout=20000)
            settle(page, 1800)
            page.click("#wizard-next", timeout=4000); settle(page, 300)
            page.click("#wiz-width", timeout=4000)
            page.keyboard.type("45", delay=40)
            page.keyboard.press("F1"); settle(page, 400)
            sc = page.evaluate("() => document.getElementById('shortcuts-modal').classList.contains('visible')")
            val = page.evaluate("() => document.getElementById('wiz-width').value")
            focus_after_f1 = page.evaluate("() => document.activeElement && document.activeElement.id")
            shot(page, "f19_f1_in_wizard_input.png")
            page.keyboard.press("Escape"); settle(page, 400)
            state_after = page.evaluate(VISIBLE_OVERLAYS)
            log_result("F19_f1_in_wizard_input", True, {
                "shortcuts_opened_while_typing": sc, "wiz_width_value": val,
                "focus_after_f1": focus_after_f1, "overlays_after_one_esc": state_after,
                "expected_if_bug": "F1 opens guide mid-typing (focus stolen from input); one Escape closes guide AND wizard"})
        except Exception:
            log_result("F19_f1_in_wizard_input", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F20 Ctrl+S real download ----------------
        current_flow[0] = "F20"
        try:
            dismiss_overlays(page)
            n1 = page.evaluate("() => window._bydState.objects.size")
            with page.expect_download(timeout=8000) as dl_info:
                page.keyboard.press("Control+s")
            dl = dl_info.value
            fname = dl.suggested_filename
            path = os.path.join(OUT, "saved_design_dl.json")
            dl.save_as(path)
            size = os.path.getsize(path)
            with open(path) as f:
                data = json.load(f)
            toast = toast_text(page)
            shot(page, "f20_ctrl_s_download.png")
            log_result("F20_ctrl_s_download", size > 0 and "objects" in data, {
                "filename": fname, "bytes": size, "objects_in_file": len(data.get("objects", [])),
                "version": data.get("version"), "toast": toast,
                "objects_in_state": n1,
                "expected": "download fires with valid JSON matching state"})
        except Exception:
            log_result("F20_ctrl_s_download", False, {"error": traceback.format_exc()[-400:]})

        # ---------------- F21 valid-but-tricky JSON via real Load flow ----------------
        current_flow[0] = "F21"
        try:
            dismiss_overlays(page)
            valid = os.path.join(OUT, "valid_design.json")
            design = {
                "version": 4,
                "yard": {"width": 40, "depth": 60, "shape": "rectangle"},
                "objects": [
                    {"id": 2, "type": "tree_deciduous", "params": {"height": 15}, "position": {"x": 3, "z": 3}, "rotation": 0, "scale": 1},
                    {"id": 9, "type": "bench", "params": {"length": 6}, "position": {"x": -3, "z": -3}, "rotation": 1.57, "scale": 1},
                    {"id": 3, "type": "tree", "params": {"height": 12}, "position": {"x": 1, "z": 1}, "rotation": 0, "scale": 1},
                ],
                "nextId": 10, "terrain": None,
            }
            with open(valid, "w") as f:
                json.dump(design, f)
            page.click("#btn-load", timeout=4000)
            settle(page, 400)
            page.set_input_files("#import-input", valid)
            settle(page, 900)
            st = page.evaluate("() => { const s = window._bydState; return {n: s.objects.size, ids: Array.from(s.objects.keys()), nextId: s.nextId, yard: s.yard}; }")
            toast = toast_text(page)
            shot(page, "f21_valid_load.png")
            log_result("F21_valid_load", st["n"] == 3, {
                "state": st, "toast": toast,
                "expected": "3 objects (legacy 'tree' migrated to tree_deciduous), nextId 10, yard 40x60"})
        except Exception:
            log_result("F21_valid_load", False, {"error": traceback.format_exc()[-400:]})

        browser.close()

    with open(os.path.join(OUT, "console_errors.json"), "w") as f:
        json.dump([{"flow": f, "kind": k, "text": t} for f, k, t in console_errors], f, indent=1)
    print("\n=== PAGE ERRORS ===")
    for f, k, t in console_errors:
        if k == "pageerror":
            print(f"[{f}] {t}")
    print("\nflows:", len(flows_run), flows_run)

if __name__ == "__main__":
    run()
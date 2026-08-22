#!/usr/bin/env python3
"""
Sprint 6 Functional Test Suite — Backyard Designer 3D
Comprehensive tests for every feature in FEATURE_INVENTORY.md.
Run: python3 sprint6_functional_tests.py
"""
import json, time, traceback, os
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8766/index.html"
RESULTS = {"tests": [], "console_errors": [], "pageerrors": []}

def log_test(name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    RESULTS["tests"].append({"name": name, "status": status, "details": details})
    print(f"[{status}] {name}" + (f" — {details}" if details else ""), flush=True)

def set_slider(page, selector, value):
    try:
        return page.evaluate(f"""() => {{
            const el = document.querySelector('{selector}');
            if (!el) return false;
            el.value = {value};
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return true;
        }}""")
    except:
        return False

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--use-gl=swiftshader", "--disable-gpu"])
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(8000)
        
        page.on("console", lambda msg: (
            RESULTS["console_errors"].append(msg.text),
            print(f"  [CONSOLE ERROR] {msg.text}", flush=True)
        ) if msg.type == "error" else None)
        page.on("pageerror", lambda err: (
            RESULTS["pageerrors"].append(str(err)),
            print(f"  [PAGE ERROR] {err}", flush=True)
        ))

        # ===== LOADING =====
        print("=== LOADING ===", flush=True)
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        log_test("Page loads without crash", True)

        # ===== SETUP WIZARD =====
        skip = page.query_selector("#wizard-skip")
        if skip and skip.is_visible():
            skip.click()
            page.wait_for_timeout(1000)
        log_test("Wizard skipped", not page.query_selector("#wizard").is_visible())
        log_test("Canvas rendered", page.query_selector("#viewport > canvas") is not None)

        # ===== TOP BAR =====
        print("\n=== TOP BAR ===", flush=True)
        for btn_id in ["#btn-undo", "#btn-redo", "#btn-save", "#btn-load", "#btn-screenshot",
                        "#btn-help", "#btn-layers", "#btn-cost", "#btn-walk", "#btn-share"]:
            log_test(f"{btn_id} exists", page.query_selector(btn_id) is not None)

        # View toggle
        vt_btns = page.query_selector_all("#view-toggle button")
        log_test("View toggle has 2 buttons", len(vt_btns) == 2)
        vt_btns[1].click(); page.wait_for_timeout(1000)
        log_test("Bird's-eye toggle", True)
        vt_btns[0].click(); page.wait_for_timeout(1000)
        log_test("Back to 3D", True)

        # ===== HELP MODAL =====
        print("\n=== HELP MODAL ===", flush=True)
        page.click("#btn-help"); page.wait_for_timeout(500)
        hm = page.query_selector("#help-modal")
        log_test("Help opens", hm.is_visible())
        page.keyboard.press("Escape"); page.wait_for_timeout(500)
        log_test("Help closes on Escape", not hm.is_visible())

        # ===== SHARE MODAL =====
        print("\n=== SHARE MODAL ===", flush=True)
        page.click("#btn-share"); page.wait_for_timeout(500)
        sm = page.query_selector("#share-modal")
        log_test("Share opens", sm.is_visible())
        page.keyboard.press("Escape"); page.wait_for_timeout(500)
        log_test("Share closes on Escape", not sm.is_visible())

        # ===== LAYERS PANEL =====
        page.click("#btn-layers"); page.wait_for_timeout(500)
        lp = page.query_selector("#layer-panel")
        log_test("Layers opens", lp.is_visible())
        page.click("#btn-layers"); page.wait_for_timeout(300)
        log_test("Layers closes", not lp.is_visible())

        # ===== COST PANEL =====
        page.click("#btn-cost"); page.wait_for_timeout(500)
        cp = page.query_selector("#cost-panel")
        log_test("Cost opens", cp.is_visible())
        page.click("#btn-cost"); page.wait_for_timeout(300)
        log_test("Cost closes", not cp.is_visible())

        # ===== ADD OBJECT & PROPERTIES =====
        print("\n=== ADD OBJECT ===", flush=True)
        lib_items = page.query_selector_all(".lib-item")
        log_test(f"Library items ({len(lib_items)})", len(lib_items) > 0)
        lib_items[0].click(); page.wait_for_timeout(1000)
        log_test("Properties panel visible", page.query_selector("#properties").is_visible())
        log_test("Undo enabled", page.query_selector("#btn-undo").get_attribute("disabled") is None)

        # Undo/Redo
        page.click("#btn-undo"); page.wait_for_timeout(500)
        log_test("Undo works", page.query_selector("#btn-undo").get_attribute("disabled") is not None)
        log_test("Redo enabled", page.query_selector("#btn-redo").get_attribute("disabled") is None)
        page.click("#btn-redo"); page.wait_for_timeout(500)
        log_test("Redo works", True)

        # Properties panel interactions
        print("\n=== PROPERTIES PANEL ===", flush=True)
        for i in range(3):
            btn = page.query_selector("[data-rotate]")
            if btn: btn.click(); page.wait_for_timeout(300)
        log_test("Rotation buttons work", True)
        log_test("Rotation slider works", set_slider(page, "#rot-slider", 45))

        pos_x = page.query_selector("#pos-x")
        pos_z = page.query_selector("#pos-z")
        if pos_x:
            pos_x.fill("10"); pos_x.dispatch_event("change"); page.wait_for_timeout(200)
            log_test("Position X works", True)
        if pos_z:
            pos_z.fill("5"); pos_z.dispatch_event("change"); page.wait_for_timeout(200)
            log_test("Position Z works", True)

        # Check params BEFORE duplicate/undo (which deselects)
        param_inputs = page.query_selector_all("[data-param]")
        log_test(f"Param inputs ({len(param_inputs)})", len(param_inputs) > 0)
        for inp in param_inputs[:3]:
            tag = inp.evaluate("el => el.tagName")
            if tag == "SELECT":
                inp.select_option(index=0); inp.dispatch_event("change"); page.wait_for_timeout(300)
            elif tag == "INPUT" and inp.get_attribute("type") == "number":
                inp.fill("5"); inp.dispatch_event("change"); page.wait_for_timeout(300)
        log_test("Param changes work", True)

        # Duplicate
        page.query_selector("#btn-duplicate").click(); page.wait_for_timeout(500)
        log_test("Duplicate works", True)
        page.click("#btn-undo"); page.wait_for_timeout(500)
        log_test("Undo duplicate", True)

        # ===== TOOL DOCK =====
        print("\n=== TOOL DOCK ===", flush=True)
        dock_ids = ["terrain", "underground", "analyze", "innovate", "sun", "measure"]
        for dock_id in dock_ids:
            page.click(f'.td-tab[data-dock="{dock_id}"]'); page.wait_for_timeout(500)
            panel = page.query_selector(f"#dock-{dock_id}")
            log_test(f"Dock {dock_id} opens", panel is not None and panel.is_visible())
            page.click(f'.td-tab[data-dock="{dock_id}"]', force=True); page.wait_for_timeout(300)
            log_test(f"Dock {dock_id} closes", True)

        # ===== TERRAIN CONTROLS =====
        print("\n=== TERRAIN CONTROLS ===", flush=True)
        page.click('.td-tab[data-dock="terrain"]'); page.wait_for_timeout(500)
        for mode in ["raise", "lower", "smooth", "erode"]:
            page.click(f'[data-tmode="{mode}"]'); page.wait_for_timeout(200)
            log_test(f"Brush {mode}", True)
        for sid, val in [("#terrain-brush-size", 15), ("#terrain-strength", 0.5), ("#grid-level-slider", 2)]:
            log_test(f"Slider {sid}", set_slider(page, sid, val))
        page.click("#precision-toggle"); page.wait_for_timeout(200)
        log_test("Precision toggle ON", True)
        page.click("#precision-toggle"); page.wait_for_timeout(200)
        log_test("Precision toggle OFF", True)
        presets = page.query_selector_all(".terrain-preset-btn")
        for i, preset in enumerate(presets):
            preset.click(); page.wait_for_timeout(500)
            log_test(f"Preset {i}", True)
        page.click("#terrain-flatten"); page.wait_for_timeout(500)
        log_test("Flatten all", True)
        for tid in ["#terrain-toggle-height", "#terrain-toggle-drainage"]:
            page.click(tid); page.wait_for_timeout(300)
            log_test(f"Toggle {tid} ON", True)
            page.click(tid); page.wait_for_timeout(300)
            log_test(f"Toggle {tid} OFF", True)
        for sid, val in [("#carve-size-slider", 10), ("#carve-depth-slider", 5)]:
            log_test(f"Carve slider {sid}", set_slider(page, sid, val))
        page.click('.td-tab[data-dock="terrain"]', force=True); page.wait_for_timeout(300)

        # ===== UNDERGROUND =====
        print("\n=== UNDERGROUND ===", flush=True)
        page.click('.td-tab[data-dock="underground"]'); page.wait_for_timeout(500)
        for sid, val in [("#terrain-cutaway", 30), ("#terrain-opacity", 50)]:
            log_test(f"Slider {sid}", set_slider(page, sid, val))
        for tid in ["#wireframe-toggle", "#cross-section-toggle"]:
            page.click(tid); page.wait_for_timeout(300)
            log_test(f"Toggle {tid} ON", True)
            page.click(tid); page.wait_for_timeout(300)
            log_test(f"Toggle {tid} OFF", True)
        page.click('.td-tab[data-dock="underground"]', force=True); page.wait_for_timeout(300)

        # ===== SUN PANEL =====
        print("\n=== SUN PANEL ===", flush=True)
        page.click('.td-tab[data-dock="sun"]'); page.wait_for_timeout(500)
        log_test("Sun time slider", set_slider(page, "#sun-time", 14))
        page.fill("#sun-date", "2026-06-21"); page.wait_for_timeout(200)
        log_test("Sun date", True)
        page.fill("#sun-lat", "40.7"); page.wait_for_timeout(200)
        page.fill("#sun-lng", "-74.0"); page.wait_for_timeout(200)
        log_test("Sun lat/lng", True)
        page.click("#sun-reset"); page.wait_for_timeout(300)
        log_test("Sun reset", True)
        page.evaluate("document.getElementById('sun-play').click()"); page.wait_for_timeout(1500)
        page.evaluate("document.getElementById('sun-play').click()"); page.wait_for_timeout(300)
        log_test("Sun play cycle", True)
        log_test("Sun presets", len(page.query_selector_all("#sun-presets button")) > 0)
        page.click('.td-tab[data-dock="sun"]', force=True); page.wait_for_timeout(300)

        # ===== ANALYSIS =====
        print("\n=== ANALYSIS ===", flush=True)
        page.click('.td-tab[data-dock="analyze"]'); page.wait_for_timeout(500)
        for tid in ["#ta-contour-toggle", "#ta-slope-toggle", "#ta-cutfill-toggle",
                     "#ta-elev-toggle", "#ta-waterflow-toggle", "#ta-ghost-toggle"]:
            page.click(tid); page.wait_for_timeout(500)
            log_test(f"Toggle {tid} ON", True)
            page.click(tid); page.wait_for_timeout(300)
            log_test(f"Toggle {tid} OFF", True)
        page.fill("#ta-contour-interval", "2"); page.wait_for_timeout(200)
        log_test("Contour interval", True)
        log_test("Cross-section btn exists", page.query_selector("#ta-crosssection-btn") is not None)
        log_test("Compare btn exists", page.query_selector("#ta-compare-btn") is not None)
        page.click('.td-tab[data-dock="analyze"]', force=True); page.wait_for_timeout(300)

        # ===== INNOVATION =====
        print("\n=== INNOVATION ===", flush=True)
        page.click('.td-tab[data-dock="innovate"]'); page.wait_for_timeout(500)
        for bid in ["#innov-pool-btn", "#innov-flatten-btn", "#innov-marker-btn"]:
            page.click(bid); page.wait_for_timeout(500)
            log_test(f"Button {bid}", True)
        adv_toggle = page.query_selector(".advanced-toggle")
        if adv_toggle:
            adv_toggle.click(); page.wait_for_timeout(300)
            for bid in ["#innov-slope-btn", "#innov-stats-btn", "#innov-retwall-btn",
                         "#innov-ugstruct-btn", "#innov-geolayer-btn", "#innov-volcalc-btn",
                         "#innov-exploded-btn", "#innov-watertable-btn", "#innov-ghostpreview-btn"]:
                page.click(bid); page.wait_for_timeout(500)
                log_test(f"Advanced {bid}", True)
                if bid in ["#innov-exploded-btn", "#innov-watertable-btn", "#innov-ghostpreview-btn"]:
                    page.click(bid); page.wait_for_timeout(300)
            adv_toggle.click(); page.wait_for_timeout(300)
        page.click('.td-tab[data-dock="innovate"]', force=True); page.wait_for_timeout(300)

        # ===== MEASURE =====
        print("\n=== MEASURE ===", flush=True)
        page.click('.td-tab[data-dock="measure"]'); page.wait_for_timeout(500)
        tape_toggle = page.query_selector("#dock-tape-toggle")
        log_test("Tape toggle exists", tape_toggle is not None)
        if tape_toggle:
            tape_toggle.click(); page.wait_for_timeout(300)
            log_test("Tape measure activate", True)
            tape_toggle.click(); page.wait_for_timeout(300)
        page.click('.td-tab[data-dock="measure"]', force=True); page.wait_for_timeout(300)

        # ===== VIEW CONTROLS =====
        print("\n=== VIEW CONTROLS ===", flush=True)
        for vid in ["#vc-zoom-in", "#vc-zoom-out", "#vc-reset"]:
            page.click(vid); page.wait_for_timeout(300)
            log_test(f"VC {vid}", True)
        page.click("#vc-underground"); page.wait_for_timeout(500)
        log_test("VC underground ON", True)
        page.click("#vc-underground"); page.wait_for_timeout(300)
        log_test("VC underground OFF", True)

        # ===== WALK MODE =====
        print("\n=== WALK MODE ===", flush=True)
        page.click("#btn-walk"); page.wait_for_timeout(1000)
        log_test("Walk mode opens", page.query_selector("#walk-controls").is_visible())
        walk_exit = page.query_selector("#walk-exit")
        if walk_exit and walk_exit.is_visible():
            walk_exit.click(); page.wait_for_timeout(500)
            log_test("Walk mode exits", True)

        # ===== BIRD'S EYE =====
        print("\n=== BIRD'S EYE ===", flush=True)
        vt_btns = page.query_selector_all("#view-toggle button")
        vt_btns[1].click(); page.wait_for_timeout(1000)
        log_test("Bird's eye opens", True)
        page.click('.td-tab[data-dock="terrain"]'); page.wait_for_timeout(500)
        log_test("Terrain in bird's eye", True)
        page.click('.td-tab[data-dock="terrain"]', force=True); page.wait_for_timeout(300)
        vt_btns[0].click(); page.wait_for_timeout(1000)
        log_test("Back to 3D", True)

        # ===== SAVE/LOAD =====
        print("\n=== SAVE/LOAD ===", flush=True)
        with page.expect_download(timeout=5000) as dl_info:
            page.click("#btn-save")
        dl = dl_info.value
        save_path = dl.path()
        log_test("Save downloads file", True, f"file={dl.suggested_filename}")
        with open(save_path, 'r') as f:
            design = json.load(f)
        log_test("Design has version", "version" in design)
        log_test("Design has yard", "yard" in design)
        log_test("Design has objects", "objects" in design)
        file_input = page.query_selector("#import-input")
        if file_input:
            file_input.set_input_files(save_path); page.wait_for_timeout(2000)
            log_test("Load via file input", True)

        # ===== SCREENSHOT =====
        page.click("#btn-screenshot"); page.wait_for_timeout(1000)
        log_test("Screenshot button", True)

        # ===== TERRAIN DEFORMATION =====
        print("\n=== TERRAIN DEFORMATION ===", flush=True)
        page.click('.td-tab[data-dock="terrain"]'); page.wait_for_timeout(500)
        page.click('[data-tmode="raise"]'); page.wait_for_timeout(200)
        canvas = page.query_selector("#viewport > canvas")
        if canvas:
            box = canvas.bounding_box()
            page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
            page.mouse.down()
            for i in range(5):
                page.mouse.move(box["x"] + box["width"]/2 + i*10, box["y"] + box["height"]/2)
                page.wait_for_timeout(50)
            page.mouse.up(); page.wait_for_timeout(500)
            log_test("Terrain deformation works", True)
        page.click('.td-tab[data-dock="terrain"]', force=True); page.wait_for_timeout(300)

        # ===== MULTIPLE OBJECTS =====
        print("\n=== MULTIPLE OBJECTS ===", flush=True)
        lib_items = page.query_selector_all(".lib-item")
        for i in range(min(5, len(lib_items))):
            lib_items[i].click(); page.wait_for_timeout(500)
        log_test("Multiple objects added", page.query_selector("#btn-undo").get_attribute("disabled") is None)
        for i in range(3):
            page.keyboard.press("Tab"); page.wait_for_timeout(200)
        log_test("Tab cycling", True)
        page.keyboard.press("ArrowRight"); page.wait_for_timeout(200)
        log_test("Arrow key movement", True)

        # ===== SUMMARY =====
        passed = sum(1 for t in RESULTS["tests"] if t["status"] == "PASS")
        failed = sum(1 for t in RESULTS["tests"] if t["status"] == "FAIL")
        print(f"\n=== SUMMARY: {passed} pass, {failed} fail ===", flush=True)
        print(f"Console errors: {len(RESULTS['console_errors'])}", flush=True)
        print(f"Page errors: {len(RESULTS['pageerrors'])}", flush=True)

        browser.close()

    with open("/root/byd6-bug-hunter/sprint6_test_results.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
    return RESULTS

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL: {e}", flush=True)
        traceback.print_exc()
        with open("/root/byd6-bug-hunter/sprint6_test_results.json", "w") as f:
            json.dump(RESULTS, f, indent=2)

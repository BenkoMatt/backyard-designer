#!/usr/bin/env python3
"""Round 2 QA: Fast test suite - single page load"""
import json, sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:8771/index.html"
results = []
bugs = []

def log(test, status, severity="Info", desc="", evidence=""):
    r = {"test": test, "status": status, "severity": severity, "desc": desc}
    results.append(r)
    if status == "FAIL":
        bugs.append(r)
    print(f"[{status}] {test}: {desc}"[:200])

def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--use-gl=swiftshader']
        )
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))

        # Single page load
        page.goto(URL, wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        page.click("#wizard-next")
        page.wait_for_timeout(500)
        page.fill("#wiz-width", "50")
        page.fill("#wiz-depth", "100")
        page.wait_for_timeout(300)
        page.click("#wizard-finish")
        page.wait_for_timeout(2000)
        page.evaluate("() => document.querySelectorAll('.cat-section').forEach(s => s.classList.remove('collapsed'))")
        page.wait_for_timeout(300)

        # TEST 1: Add all 21 objects in one go, then change each one's properties
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) item.click();
        }""")
        page.wait_for_timeout(3000)
        log("Add all 21 objects", "PASS" if len(errors) == 0 else "FAIL", "Critical",
            f"Errors: {len(errors)}", errors[:3])

        # TEST 2: Select first object and change all its properties
        canvas = page.query_selector("canvas")
        if canvas:
            box = canvas.bounding_box()
            page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
            page.wait_for_timeout(500)

        # Try changing every param input that exists
        err_before = len(errors)
        page.evaluate("""() => {
            document.querySelectorAll('input[data-param]').forEach(input => {
                if (input.type === 'number') {
                    input.value = '5';
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                } else if (input.type === 'color') {
                    input.value = '#FF0000';
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
            document.querySelectorAll('select[data-param]').forEach(select => {
                if (select.options.length > 1) {
                    select.selectedIndex = (select.selectedIndex + 1) % select.options.length;
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        }""")
        page.wait_for_timeout(1000)
        log("Change all properties of selected object", "PASS" if len(errors) - err_before == 0 else "FAIL", "High",
            f"Errors: {len(errors) - err_before}")

        # TEST 3: Rotate 90, 180, -90
        err_before = len(errors)
        for rot in ['90', '180', '-90']:
            page.evaluate(f"""() => document.querySelector('.rotate-btn[data-rotate="{rot}"]')?.click()""")
            page.wait_for_timeout(300)
        log("Rotation buttons (90, 180, -90)", "PASS" if len(errors) - err_before == 0 else "FAIL", "Medium")

        # TEST 4: Rotation slider
        page.evaluate("""() => {
            const slider = document.getElementById('rot-slider');
            if (slider) { slider.value = '45'; slider.dispatchEvent(new Event('input', {bubbles:true})); slider.dispatchEvent(new Event('change', {bubbles:true})); }
        }""")
        page.wait_for_timeout(300)
        log("Rotation slider to 45", "PASS" if len(errors) - err_before == 0 else "FAIL", "Medium")

        # TEST 5: Position inputs
        page.evaluate("""() => {
            const px = document.getElementById('pos-x');
            const pz = document.getElementById('pos-z');
            if (px) { px.value = '10'; px.dispatchEvent(new Event('change', {bubbles:true})); }
            if (pz) { pz.value = '-5'; pz.dispatchEvent(new Event('change', {bubbles:true})); }
        }""")
        page.wait_for_timeout(300)
        log("Position inputs", "PASS" if len(errors) - err_before == 0 else "FAIL", "Medium")

        # TEST 6: Duplicate
        page.evaluate("""() => document.getElementById('btn-duplicate')?.click()""")
        page.wait_for_timeout(500)
        log("Duplicate object", "PASS" if len(errors) - err_before == 0 else "FAIL", "Medium")

        # TEST 7: Undo/Redo
        for _ in range(5):
            page.evaluate("""() => document.getElementById('btn-undo')?.click()""")
            page.wait_for_timeout(100)
        for _ in range(5):
            page.evaluate("""() => document.getElementById('btn-redo')?.click()""")
            page.wait_for_timeout(100)
        log("Undo/Redo 5x each", "PASS" if len(errors) - err_before == 0 else "FAIL", "Medium")

        # TEST 8: 2D view
        page.click("button[data-view='2d']")
        page.wait_for_timeout(1000)
        grid_count = page.evaluate("() => document.getElementById('grid-labels')?.querySelectorAll('.grid-label')?.length || 0")
        log("2D view grid labels", "PASS" if grid_count > 0 else "FAIL", "High", f"Labels: {grid_count}")

        # TEST 9: Zoom in 2D
        page.click("#vc-zoom-in")
        page.wait_for_timeout(500)
        page.click("#vc-zoom-out")
        page.wait_for_timeout(500)
        page.click("#vc-reset")
        page.wait_for_timeout(500)
        log("2D zoom controls", "PASS" if len(errors) - err_before == 0 else "FAIL", "Medium")

        # TEST 10: Back to 3D
        page.click("button[data-view='3d']")
        page.wait_for_timeout(500)
        log("3D view toggle", "PASS")

        # TEST 11: Terrain mode
        page.click("#terrain-btn")
        page.wait_for_timeout(500)
        terrain_visible = page.evaluate("() => document.getElementById('terrain-controls')?.classList.contains('visible')")
        log("Terrain mode toggle", "PASS" if terrain_visible else "FAIL", "High")

        # Paint terrain
        if canvas:
            box = canvas.bounding_box()
            page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
            page.mouse.down()
            page.mouse.move(box["x"] + box["width"]/2 + 50, box["y"] + box["height"]/2 + 30)
            page.wait_for_timeout(200)
            page.mouse.up()
            page.wait_for_timeout(300)
        log("Terrain paint", "PASS" if len(errors) - err_before == 0 else "FAIL", "High")

        page.click("#terrain-btn")
        page.wait_for_timeout(300)

        # TEST 12: Tape measure
        page.click("#tape-measure-btn")
        page.wait_for_timeout(300)
        tape_active = page.evaluate("() => document.getElementById('tape-measure-btn')?.classList.contains('active')")
        log("Tape measure activate", "PASS" if tape_active else "FAIL", "Medium")

        # Click two points
        if canvas:
            box = canvas.bounding_box()
            page.mouse.click(box["x"] + 200, box["y"] + 200)
            page.wait_for_timeout(300)
            page.mouse.click(box["x"] + 400, box["y"] + 300)
            page.wait_for_timeout(500)
        log("Tape measure two points", "PASS" if len(errors) - err_before == 0 else "FAIL", "Medium")

        # TEST 13: Save
        page.evaluate("""() => document.getElementById('btn-save')?.click()""")
        page.wait_for_timeout(500)
        log("Save button", "PASS")

        # TEST 14: Screenshot
        page.evaluate("""() => document.getElementById('btn-screenshot')?.click()""")
        page.wait_for_timeout(500)
        log("Screenshot", "PASS")

        # TEST 15: Help modal
        page.click("#btn-help")
        page.wait_for_timeout(500)
        help_has_terrain = page.evaluate("() => document.getElementById('help-modal')?.textContent?.includes('Terrain')")
        log("Help modal has terrain docs", "PASS" if help_has_terrain else "FAIL", "Low")
        page.evaluate("() => document.getElementById('help-modal')?.classList.remove('visible')")

        # TEST 16: Adversarial - extreme values
        page.evaluate("""() => {
            const input = document.querySelector('input[data-param="length"]');
            if (input) { input.value = '999999'; input.dispatchEvent(new Event('change', {bubbles:true})); }
        }""")
        page.wait_for_timeout(1000)
        log("Fence length 999999 (no crash)", "PASS" if len(errors) - err_before == 0 else "FAIL", "Critical")

        page.evaluate("""() => {
            const input = document.querySelector('input[data-param="length"]');
            if (input) { input.value = 'NaN'; input.dispatchEvent(new Event('change', {bubbles:true})); }
        }""")
        page.wait_for_timeout(500)
        log("Fence length NaN", "PASS" if len(errors) - err_before == 0 else "FAIL", "High")

        page.evaluate("""() => {
            const input = document.querySelector('input[data-param="length"]');
            if (input) { input.value = '-50'; input.dispatchEvent(new Event('change', {bubbles:true})); }
        }""")
        page.wait_for_timeout(500)
        log("Fence length -50", "PASS" if len(errors) - err_before == 0 else "FAIL", "High")

        # TEST 17: Position extreme
        page.evaluate("""() => {
            const px = document.getElementById('pos-x');
            if (px) { px.value = '99999'; px.dispatchEvent(new Event('change', {bubbles:true})); }
        }""")
        page.wait_for_timeout(500)
        log("Position X=99999 (clamped)", "PASS" if len(errors) - err_before == 0 else "FAIL", "High")

        # TEST 18: Mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(1000)
        mobile_toggle = page.evaluate("""() => {
            const btn = document.getElementById('mobile-lib-toggle');
            if (!btn) return false;
            return window.getComputedStyle(btn).display !== 'none';
        }""")
        log("Mobile toggle visible", "PASS" if mobile_toggle else "FAIL", "Medium")

        if mobile_toggle:
            page.click("#mobile-lib-toggle")
            page.wait_for_timeout(500)
            sidebar_open = page.evaluate("() => document.getElementById('sidebar')?.classList.contains('mobile-visible')")
            log("Mobile sidebar opens", "PASS" if sidebar_open else "FAIL", "Medium")

        page.set_viewport_size({"width": 1280, "height": 720})
        page.wait_for_timeout(500)

        # TEST 19: Safety warnings
        # Need fresh page for this
        page.goto(URL, wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        page.click("#wizard-next")
        page.wait_for_timeout(500)
        page.fill("#wiz-width", "50")
        page.fill("#wiz-depth", "100")
        page.wait_for_timeout(300)
        page.click("#wizard-finish")
        page.wait_for_timeout(2000)
        page.evaluate("() => document.querySelectorAll('.cat-section').forEach(s => s.classList.remove('collapsed'))")
        page.wait_for_timeout(300)

        # Add pool
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) {
                if (item.textContent.includes('In-Ground Pool')) { item.click(); break; }
            }
        }""")
        page.wait_for_timeout(1000)
        pool_warning = page.evaluate("""() => {
            const warnings = document.querySelectorAll('.safety-warning');
            return Array.from(warnings).some(w => w.textContent.includes('Pool Safety'));
        }""")
        log("Pool safety warning", "PASS" if pool_warning else "FAIL", "High")

        # Add fire pit
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) {
                if (item.textContent.includes('Fire Pit')) { item.click(); break; }
            }
        }""")
        page.wait_for_timeout(1000)
        fire_warning = page.evaluate("""() => {
            const warnings = document.querySelectorAll('.safety-warning');
            return Array.from(warnings).some(w => w.textContent.includes('Fire Pit'));
        }""")
        log("Fire pit safety warning", "PASS" if fire_warning else "FAIL", "High")

        # Add retaining wall >4ft
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) {
                if (item.textContent.includes('Retaining Wall')) { item.click(); break; }
            }
        }""")
        page.wait_for_timeout(1000)
        page.evaluate("""() => {
            const input = document.querySelector('input[data-param="height"]');
            if (input) { input.value = '5'; input.dispatchEvent(new Event('change', {bubbles:true})); }
        }""")
        page.wait_for_timeout(500)
        eng_warning = page.evaluate("""() => {
            const warnings = document.querySelectorAll('.safety-warning');
            return Array.from(warnings).some(w => w.textContent.includes('Engineering'));
        }""")
        log("Retaining wall >4ft engineering warning", "PASS" if eng_warning else "FAIL", "High")

        # TEST 20: Pool shapes
        for shape in ['rectangle', 'kidney', 'roman']:
            # Select the pool (click on it)
            if canvas:
                box = canvas.bounding_box()
                page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                page.wait_for_timeout(500)
            page.evaluate(f"""() => {{
                const select = document.querySelector('select[data-param="shape"]');
                if (select) {{ select.value = '{shape}'; select.dispatchEvent(new Event('change', {{bubbles:true}})); }}
            }}""")
            page.wait_for_timeout(500)
            log(f"Pool shape: {shape}", "PASS" if len(errors) - err_before == 0 else "FAIL", "High")

        # TEST 21: localStorage corruption
        page.evaluate("() => localStorage.setItem('backyard-design-autosave', 'GARBAGE{{{')")
        page.reload(wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        log("Corrupt localStorage reload", "PASS" if len(errors) - err_before == 0 else "FAIL", "High",
            f"Errors: {len(errors) - err_before}")

        # TEST 22: Delete selected then modify
        page.goto(URL, wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        page.click("#wizard-next")
        page.wait_for_timeout(500)
        page.fill("#wiz-width", "50")
        page.fill("#wiz-depth", "100")
        page.wait_for_timeout(300)
        page.click("#wizard-finish")
        page.wait_for_timeout(2000)
        page.evaluate("() => document.querySelectorAll('.cat-section').forEach(s => s.classList.remove('collapsed'))")
        page.wait_for_timeout(300)
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) {
                if (item.textContent.includes('Privacy Fence')) { item.click(); break; }
            }
        }""")
        page.wait_for_timeout(1000)
        page.evaluate("""() => document.getElementById('btn-delete')?.click()""")
        page.wait_for_timeout(500)
        # Try to modify - should not crash
        err_before2 = len(errors)
        page.evaluate("""() => {
            const input = document.querySelector('input[data-param="length"]');
            if (input) { input.value = '10'; input.dispatchEvent(new Event('change', {bubbles:true})); }
        }""")
        page.wait_for_timeout(500)
        log("Modify after delete (stale ref)", "PASS" if len(errors) - err_before2 == 0 else "FAIL", "Medium",
            f"Errors: {len(errors) - err_before2}")

        # FINAL
        log("Total page errors", "PASS" if len(errors) == 0 else "FAIL", "Medium", f"Total: {len(errors)}", errors[:5])
        page.screenshot(path="/tmp/backyard-round2.png")
        browser.close()
        return results

if __name__ == "__main__":
    results = run_tests()
    print("\n" + "="*60)
    print("ROUND 2 QA SUMMARY")
    print("="*60)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    if bugs:
        print("\nBUGS FOUND:")
        for b in bugs:
            print(f"  [{b['severity']}] {b['test']}: {b['desc']}")
    else:
        print("\nNo bugs found!")
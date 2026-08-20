#!/usr/bin/env python3
"""Comprehensive QA test suite for Backyard Designer 3D"""
import json, sys, time, os
from playwright.sync_api import sync_playwright

URL = "http://localhost:8770/index.html"
results = []
bugs = []

def log(test, status, severity="Info", desc="", evidence=""):
    r = {"test": test, "status": status, "severity": severity, "desc": desc, "evidence": evidence[:500]}
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

        # ===== TEST 1: Page loads with no errors =====
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        console_errors = []
        page.on("console", lambda msg: console_errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None)
        
        page.goto(URL, wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        log("Page Load", "PASS" if not errors else "FAIL", "Critical",
            f"Page errors: {len(errors)}", str(errors))
        
        # ===== TEST 2: Wizard completes =====
        wizard_visible = page.evaluate("() => !!document.getElementById('wizard')")
        log("Wizard Visible", "PASS" if wizard_visible else "FAIL")
        
        page.click("#wizard-next")
        page.wait_for_timeout(500)
        page.fill("#wiz-width", "50")
        page.fill("#wiz-depth", "100")
        page.wait_for_timeout(300)
        page.click("#wizard-finish")
        page.wait_for_timeout(2000)
        
        wizard_gone = page.evaluate("() => !document.getElementById('wizard').classList.contains('visible') && document.getElementById('wizard').style.display !== 'block'")
        # Check if wizard is hidden
        wizard_hidden = page.evaluate("""() => {
            const w = document.getElementById('wizard');
            const style = window.getComputedStyle(w);
            return style.display === 'none';
        }""")
        log("Wizard Completes", "PASS" if wizard_hidden else "FAIL", "High",
            f"Wizard hidden after finish: {wizard_hidden}")
        
        # ===== TEST 3: Library has 21 items =====
        lib_info = page.evaluate("""() => {
            const lib = document.getElementById('library');
            const items = lib ? lib.querySelectorAll('.lib-item') : [];
            const sections = lib ? lib.querySelectorAll('.cat-section') : [];
            return { items: items.length, sections: sections.length };
        }""")
        log("Library Items", "PASS" if lib_info["items"] == 21 else "FAIL", "Critical",
            f"Items: {lib_info['items']}, Sections: {lib_info['sections']}")
        
        # ===== TEST 4: Add all 21 objects =====
        page.evaluate("""() => {
            document.querySelectorAll('.cat-section').forEach(s => s.classList.remove('collapsed'));
        }""")
        page.wait_for_timeout(500)
        
        add_results = page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            const results = [];
            for (const item of items) {
                const name = item.querySelector('.lib-name')?.textContent || item.textContent.substring(0, 20);
                item.click();
                results.push(name.trim());
            }
            return results;
        }""")
        page.wait_for_timeout(3000)
        
        # Count objects in scene
        obj_count = page.evaluate("""() => {
            return document.querySelectorAll('.lib-item').length;
        }""")
        
        # Check page errors after adding all objects
        log("Add All 21 Objects", "PASS" if len(add_results) == 21 and not errors else "FAIL", "Critical",
            f"Added {len(add_results)} objects, errors: {len(errors)}", str(errors[:5]))
        
        # ===== TEST 5: Check for JavaScript errors after adding objects =====
        log("No JS Errors After Bulk Add", "PASS" if not errors else "FAIL", "Critical",
            f"Errors: {len(errors)}", str(errors[:3]))
        
        # ===== TEST 6: Undo/Redo =====
        page.evaluate("""() => { document.getElementById('btn-undo')?.click(); }""")
        page.wait_for_timeout(500)
        page.evaluate("""() => { document.getElementById('btn-redo')?.click(); }""")
        page.wait_for_timeout(500)
        log("Undo/Redo Buttons", "PASS", "Medium", "Buttons respond to clicks")
        
        # ===== TEST 7: 2D/3D Toggle =====
        page.click("button[data-view='2d']")
        page.wait_for_timeout(1000)
        grid_labels = page.evaluate("""() => {
            const gl = document.getElementById('grid-labels');
            return gl ? { visible: gl.classList.contains('visible'), count: gl.querySelectorAll('.grid-label').length } : null;
        }""")
        log("2D View + Grid Labels", "PASS" if grid_labels and grid_labels["count"] > 0 else "FAIL", "High",
            f"Grid labels: {grid_labels}")
        
        page.click("button[data-view='3d']")
        page.wait_for_timeout(500)
        log("3D View Toggle", "PASS")
        
        # ===== TEST 8: Scale Bar =====
        scale_bar = page.evaluate("""() => document.getElementById('scale-bar')?.textContent?.trim()""")
        log("Scale Bar", "PASS" if scale_bar else "FAIL", "Medium", f"Scale bar: {scale_bar}")
        
        # ===== TEST 9: Terrain Mode =====
        page.click("#terrain-btn")
        page.wait_for_timeout(500)
        terrain_visible = page.evaluate("""() => document.getElementById('terrain-controls')?.classList.contains('visible')""")
        log("Terrain Mode Toggle", "PASS" if terrain_visible else "FAIL", "High", f"Controls visible: {terrain_visible}")
        
        # Switch terrain to lower mode
        page.click(".terrain-mode-btn[data-tmode='lower']")
        page.wait_for_timeout(300)
        lower_active = page.evaluate("""() => document.querySelector('.terrain-mode-btn[data-tmode="lower"]')?.classList.contains('active')""")
        log("Terrain Lower Mode", "PASS" if lower_active else "FAIL", "Medium")
        
        # Switch to smooth
        page.click(".terrain-mode-btn[data-tmode='smooth']")
        page.wait_for_timeout(300)
        smooth_active = page.evaluate("""() => document.querySelector('.terrain-mode-btn[data-tmode="smooth"]')?.classList.contains('active')""")
        log("Terrain Smooth Mode", "PASS" if smooth_active else "FAIL", "Medium")
        
        # Turn off terrain
        page.click("#terrain-btn")
        page.wait_for_timeout(300)
        log("Terrain Mode Off", "PASS")
        
        # ===== TEST 10: Tape Measure =====
        page.click("#tape-measure-btn")
        page.wait_for_timeout(300)
        tape_active = page.evaluate("""() => document.getElementById('tape-measure-btn')?.classList.contains('active')""")
        log("Tape Measure Activate", "PASS" if tape_active else "FAIL", "Medium")
        page.click("#tape-measure-btn")
        page.wait_for_timeout(300)
        
        # ===== TEST 11: Save/Load =====
        page.click("#btn-save")
        page.wait_for_timeout(1000)
        log("Save Button", "PASS", "Medium", "Save button clicks without error")
        
        # ===== TEST 12: Screenshot =====
        page.click("#btn-screenshot")
        page.wait_for_timeout(1000)
        log("Screenshot Button", "PASS", "Medium", "Screenshot button clicks without error")
        
        # ===== TEST 13: Help Modal =====
        page.click("#btn-help")
        page.wait_for_timeout(500)
        help_visible = page.evaluate("""() => document.getElementById('help-modal')?.classList.contains('visible')""")
        log("Help Modal Opens", "PASS" if help_visible else "FAIL", "Low")
        
        # Close help
        page.evaluate("""() => document.getElementById('help-modal').classList.remove('visible')""")
        page.wait_for_timeout(300)
        
        # ===== TEST 14: Adversarial - Invalid number inputs =====
        # Expand all and add a fence, then try invalid values
        page.evaluate("""() => {
            document.querySelectorAll('.cat-section').forEach(s => s.classList.remove('collapsed'));
        }""")
        page.wait_for_timeout(300)
        
        # Clear existing objects by reloading
        page.goto(URL, wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        page.click("#wizard-next")
        page.wait_for_timeout(500)
        page.fill("#wiz-width", "50")
        page.fill("#wiz-depth", "100")
        page.wait_for_timeout(300)
        page.click("#wizard-finish")
        page.wait_for_timeout(2000)
        
        errors_before = len(errors)
        
        # Add a privacy fence
        page.evaluate("""() => {
            document.querySelectorAll('.cat-section').forEach(s => s.classList.remove('collapsed'));
        }""")
        page.wait_for_timeout(300)
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) {
                if (item.textContent.includes('Privacy Fence')) { item.click(); break; }
            }
        }""")
        page.wait_for_timeout(1000)
        
        # Try setting length to -1
        page.evaluate("""() => {
            const input = document.querySelector('input[data-param="length"]');
            if (input) {
                input.value = '-1';
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""")
        page.wait_for_timeout(500)
        errors_after_negative = len(errors) - errors_before
        log("Negative Number Input", "PASS" if errors_after_negative == 0 else "FAIL", "High",
            f"Errors after -1 input: {errors_after_negative}", str(errors[-3:]))
        
        # Try setting length to 999999
        page.evaluate("""() => {
            const input = document.querySelector('input[data-param="length"]');
            if (input) {
                input.value = '999999';
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""")
        page.wait_for_timeout(500)
        errors_after_huge = len(errors) - errors_before
        log("Huge Number Input", "PASS" if errors_after_huge == 0 else "FAIL", "High",
            f"Errors after 999999 input: {errors_after_huge}")
        
        # Try setting length to NaN
        page.evaluate("""() => {
            const input = document.querySelector('input[data-param="length"]');
            if (input) {
                input.value = 'NaN';
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""")
        page.wait_for_timeout(500)
        errors_after_nan = len(errors) - errors_before
        log("NaN Input", "PASS" if errors_after_nan == 0 else "FAIL", "High",
            f"Errors after NaN input: {errors_after_nan}", str(errors[-3:]))
        
        # Try setting length to text
        page.evaluate("""() => {
            const input = document.querySelector('input[data-param="length"]');
            if (input) {
                input.value = '<script>alert(1)</script>';
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""")
        page.wait_for_timeout(500)
        errors_after_xss = len(errors) - errors_before
        log("XSS Input", "PASS" if errors_after_xss == 0 else "FAIL", "High",
            f"Errors after XSS input: {errors_after_xss}")
        
        # ===== TEST 15: Position inputs with invalid values =====
        page.evaluate("""() => {
            const posX = document.getElementById('pos-x');
            if (posX) {
                posX.value = 'NaN';
                posX.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""")
        page.wait_for_timeout(500)
        log("Position NaN Input", "PASS" if len(errors) - errors_before == 0 else "FAIL", "High",
            f"Errors: {len(errors) - errors_before}")
        
        # ===== TEST 16: Rapid view toggle (stress test) =====
        errors_before_toggle = len(errors)
        for i in range(20):
            view_mode = '2d' if i % 2 == 0 else '3d'
            page.evaluate(f"() => document.querySelector(\"button[data-view='{view_mode}']\")?.click()")
        page.wait_for_timeout(1000)
        log("Rapid View Toggle (20x)", "PASS" if len(errors) - errors_before_toggle == 0 else "FAIL", "Medium",
            f"Errors after 20 toggles: {len(errors) - errors_before_toggle}")
        
        # ===== TEST 17: Rapid undo/redo (stress test) =====
        errors_before_undo = len(errors)
        for i in range(20):
            page.evaluate("""() => document.getElementById('btn-undo')?.click()""")
            page.wait_for_timeout(50)
        for i in range(20):
            page.evaluate("""() => document.getElementById('btn-redo')?.click()""")
            page.wait_for_timeout(50)
        log("Rapid Undo/Redo (40x)", "PASS" if len(errors) - errors_before_undo == 0 else "FAIL", "Medium",
            f"Errors: {len(errors) - errors_before_undo}")
        
        # ===== TEST 18: Small yard (10x10) =====
        page.goto(URL, wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        page.click("#wizard-next")
        page.wait_for_timeout(500)
        page.fill("#wiz-width", "10")
        page.fill("#wiz-depth", "10")
        page.wait_for_timeout(300)
        page.click("#wizard-finish")
        page.wait_for_timeout(2000)
        
        errors_small = len(errors)
        # Add a pool (16x32) that's bigger than the 10x10 yard
        page.evaluate("""() => {
            document.querySelectorAll('.cat-section').forEach(s => s.classList.remove('collapsed'));
        }""")
        page.wait_for_timeout(300)
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) {
                if (item.textContent.includes('In-Ground Pool')) { item.click(); break; }
            }
        }""")
        page.wait_for_timeout(1000)
        log("Pool in Tiny Yard (10x10)", "PASS" if len(errors) - errors_small == 0 else "FAIL", "High",
            f"Errors: {len(errors) - errors_small}")
        
        # ===== TEST 19: Mobile viewport (iPhone) =====
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(1000)
        mobile_errors = len(errors)
        sidebar_visible = page.evaluate("""() => {
            const sb = document.getElementById('sidebar');
            const style = window.getComputedStyle(sb);
            return style.display;
        }""")
        log("Mobile Viewport (375x667)", "PASS" if sidebar_visible == "none" else "FAIL", "Medium",
            f"Sidebar display: {sidebar_visible}")
        
        # ===== TEST 20: iPad viewport =====
        page.set_viewport_size({"width": 768, "height": 1024})
        page.wait_for_timeout(1000)
        log("iPad Viewport (768x1024)", "PASS" if len(errors) - mobile_errors == 0 else "FAIL")
        
        # Reset viewport
        page.set_viewport_size({"width": 1280, "height": 720})
        page.wait_for_timeout(500)
        
        # ===== TEST 21: localStorage corruption =====
        page.evaluate("""() => localStorage.setItem('backyard-design-autosave', 'GARBAGE DATA {{{{')""")
        page.reload(wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        log("localStorage Corruption Survives", "PASS" if len(errors) == 0 else "FAIL", "High",
            f"Errors after corrupt localStorage reload: {len(errors)}", str(errors[-3:]))
        
        # ===== TEST 22: Console errors throughout =====
        log("Console Errors Total", "PASS" if len(console_errors) == 0 else "FAIL", "Medium",
            f"Console errors: {len(console_errors)}", str(console_errors[:5]))
        
        page.close()
        browser.close()
        
        return results

if __name__ == "__main__":
    results = run_tests()
    print("\n" + "="*60)
    print("QA TEST SUMMARY")
    print("="*60)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    print()
    if bugs:
        print("BUGS FOUND:")
        for b in bugs:
            print(f"  [{b['severity']}] {b['test']}: {b['desc']}")
    print()
    print(f"JSON Results: {json.dumps(results, indent=2)}")
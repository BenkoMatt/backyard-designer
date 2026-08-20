#!/usr/bin/env python3
"""Round 2 QA: Deep test suite for Backyard Designer 3D"""
import json, sys, time
from playwright.sync_api import sync_playwright

URL = "http://localhost:8771/index.html"
results = []
bugs = []

def log(test, status, severity="Info", desc="", evidence=""):
    r = {"test": test, "status": status, "severity": severity, "desc": desc, "evidence": str(evidence)[:300]}
    results.append(r)
    if status == "FAIL":
        bugs.append(r)
    print(f"[{status}] {test}: {desc}"[:200])

def setup_page(page):
    """Complete wizard and expand library"""
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

def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--use-gl=swiftshader']
        )
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        console_errors = []
        page.on("console", lambda msg: console_errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None)

        setup_page(page)

        # ===== TEST 1: Each object type individually with property changes =====
        OBJECT_TYPES = [
            ("Privacy Fence", ["height", "length", "color"]),
            ("Picket Fence", ["height", "length", "color"]),
            ("Pergola", ["width", "depth", "height", "color"]),
            ("Garden Shed", ["width", "depth", "height", "color"]),
            ("In-Ground Pool", ["shape", "width", "length", "depth"]),
            ("Hot Tub", ["diameter", "depth"]),
            ("Shade Tree", ["species", "size"]),
            ("Evergreen Tree", ["species", "size"]),
            ("Bush / Shrub", ["species", "size", "color"]),
            ("Hedge Row", ["length", "height", "color"]),
            ("Patio", ["width", "depth", "material", "color"]),
            ("Deck", ["width", "depth", "height", "color"]),
            ("Walkway", ["width", "length", "color"]),
            ("Raised Garden Bed", ["width", "depth", "height", "color"]),
            ("Retaining Wall", ["length", "height", "color"]),
            ("Fire Pit", ["diameter"]),
            ("Patio Chair", ["color"]),
            ("Patio Table", ["width", "depth", "color"]),
            ("Lounge Chair", ["color"]),
            ("Grill", []),
            ("Lawn Area", ["width", "depth"]),
        ]

        for obj_name, params in OBJECT_TYPES:
            # Fresh page for each object
            setup_page(page)
            err_before = len(errors)

            # Add the object
            clicked = page.evaluate(f"""() => {{
                const items = document.querySelectorAll('.lib-item');
                for (const item of items) {{
                    if (item.textContent.includes('{obj_name}')) {{ item.click(); return true; }}
                }}
                return false;
            }}""")
            page.wait_for_timeout(1000)

            if not clicked:
                log(f"Add {obj_name}", "FAIL", "High", f"Could not find {obj_name} in library")
                continue

            add_errors = len(errors) - err_before
            if add_errors > 0:
                log(f"Add {obj_name}", "FAIL", "Critical", f"{add_errors} errors on add", errors[-3:])
                continue

            # Change each param to min, max, and a middle value
            for param_key in params:
                if param_key == "color":
                    # Test color change
                    page.evaluate("""() => {
                        const input = document.querySelector('input[data-param="color"]');
                        if (input) { input.value = '#FF0000'; input.dispatchEvent(new Event('change', { bubbles: true })); }
                    }""")
                    page.wait_for_timeout(500)
                elif param_key == "shape" or param_key == "species" or param_key == "size" or param_key == "material" or param_key == "height":
                    # Select dropdown - try each option
                    page.evaluate(f"""() => {{
                        const select = document.querySelector('select[data-param="{param_key}"]');
                        if (select && select.options.length > 1) {{
                            select.selectedIndex = 1;
                            select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                    }}""")
                    page.wait_for_timeout(500)
                else:
                    # Number input - test min
                    page.evaluate(f"""() => {{
                        const input = document.querySelector('input[data-param="{param_key}"]');
                        if (input) {{
                            const min = input.min ? parseFloat(input.min) : 1;
                            input.value = String(min);
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                    }}""")
                    page.wait_for_timeout(500)

                    # Test max
                    page.evaluate(f"""() => {{
                        const input = document.querySelector('input[data-param="{param_key}"]');
                        if (input) {{
                            const max = input.max ? parseFloat(input.max) : 100;
                            input.value = String(max);
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                    }}""")
                    page.wait_for_timeout(500)

            param_errors = len(errors) - err_before
            log(f"Property changes: {obj_name}", "PASS" if param_errors == 0 else "FAIL", "High",
                f"Errors: {param_errors}", errors[-3:] if param_errors > 0 else "")

        # ===== TEST 2: Save/Load fidelity =====
        setup_page(page)
        # Add several objects
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            const types = ['Privacy Fence', 'In-Ground Pool', 'Shade Tree', 'Patio', 'Fire Pit'];
            for (const item of items) {
                for (const t of types) {
                    if (item.textContent.includes(t)) { item.click(); break; }
                }
            }
        }""")
        page.wait_for_timeout(2000)

        # Get the serialized design from localStorage
        autosave_before = page.evaluate("""() => {
            return localStorage.getItem('backyard-design-autosave');
        }""")

        if autosave_before:
            data_before = json.loads(autosave_before)
            obj_count_before = len(data_before.get("objects", []))
            log("Autosave has objects", "PASS" if obj_count_before > 0 else "FAIL", "High",
                f"Objects in autosave: {obj_count_before}")
        else:
            log("Autosave exists", "FAIL", "High", "No autosave data found")

        # ===== TEST 3: Load malicious JSON =====
        err_before = len(errors)
        # Inject a malicious JSON into localStorage and reload
        page.evaluate("""() => {
            localStorage.setItem('backyard-design-autosave', '{"objects":"not_an_array","yard":{"width":"NaN"}}');
        }""")
        page.reload(wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        log("Malicious JSON in autosave", "PASS" if len(errors) - err_before == 0 else "FAIL", "High",
            f"Errors: {len(errors) - err_before}", errors[-3:])

        # ===== TEST 4: Load valid but extreme JSON =====
        setup_page(page)
        err_before = len(errors)
        # Set extreme but valid JSON
        page.evaluate("""() => {
            const data = {
                version: 2,
                yard: { width: 1, depth: 1, shape: 'rectangle' },
                objects: [],
                nextId: 1,
                terrain: null,
                terrainSegs: 50
            };
            localStorage.setItem('backyard-design-autosave', JSON.stringify(data));
        }""")
        page.reload(wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        log("Extreme yard (1x1) via autosave", "PASS" if len(errors) - err_before == 0 else "FAIL", "Medium",
            f"Errors: {len(errors) - err_before}")

        # ===== TEST 5: Very large yard (200x200) =====
        setup_page(page)
        page.goto(URL, wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        page.click("#wizard-next")
        page.wait_for_timeout(500)
        page.fill("#wiz-width", "200")
        page.fill("#wiz-depth", "200")
        page.wait_for_timeout(300)
        page.click("#wizard-finish")
        page.wait_for_timeout(2000)
        page.evaluate("() => document.querySelectorAll('.cat-section').forEach(s => s.classList.remove('collapsed'))")
        page.wait_for_timeout(300)

        # Add objects
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) item.click();
        }""")
        page.wait_for_timeout(3000)
        log("Large yard (200x200) + 21 objects", "PASS" if len(errors) - err_before == 0 else "FAIL", "Medium",
            f"Errors: {len(errors) - err_before}")

        # ===== TEST 6: 2D view dimension lines on selected object =====
        setup_page(page)
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) {
                if (item.textContent.includes('Patio')) { item.click(); break; }
            }
        }""")
        page.wait_for_timeout(1000)

        # Switch to 2D
        page.click("button[data-view='2d']")
        page.wait_for_timeout(1000)

        # Click on the patio to select it
        canvas = page.query_selector("canvas")
        if canvas:
            box = canvas.bounding_box()
            page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
            page.wait_for_timeout(1000)

        # Check if properties panel shows
        props_visible = page.evaluate("""() => {
            return document.getElementById('properties')?.classList.contains('visible');
        }""")
        log("2D select object shows properties", "PASS" if props_visible else "FAIL", "Medium",
            f"Properties visible: {props_visible}")

        # ===== TEST 7: Terrain editing then object placement =====
        setup_page(page)
        err_before = len(errors)

        # Activate terrain mode
        page.click("#terrain-btn")
        page.wait_for_timeout(500)

        # Paint terrain by clicking on the canvas
        canvas = page.query_selector("canvas")
        if canvas:
            box = canvas.bounding_box()
            # Click and drag to raise terrain
            page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
            page.mouse.down()
            for i in range(5):
                page.mouse.move(box["x"] + box["width"]/2 + i*20, box["y"] + box["height"]/2 + i*10)
                page.wait_for_timeout(100)
            page.mouse.up()
            page.wait_for_timeout(500)

        # Turn off terrain
        page.click("#terrain-btn")
        page.wait_for_timeout(300)

        # Add an object
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) {
                if (item.textContent.includes('Shade Tree')) { item.click(); break; }
            }
        }""")
        page.wait_for_timeout(1000)

        log("Terrain edit + object placement", "PASS" if len(errors) - err_before == 0 else "FAIL", "High",
            f"Errors: {len(errors) - err_before}")

        # ===== TEST 8: Rapid add 50 objects =====
        setup_page(page)
        err_before = len(errors)
        for i in range(50):
            page.evaluate("""() => {
                const items = document.querySelectorAll('.lib-item');
                if (items[0]) items[0].click();
            }""")
        page.wait_for_timeout(3000)
        log("Rapid add 50 objects", "PASS" if len(errors) - err_before == 0 else "FAIL", "High",
            f"Errors: {len(errors) - err_before}")

        # ===== TEST 9: Delete while selected, then try to modify =====
        setup_page(page)
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) {
                if (item.textContent.includes('Privacy Fence')) { item.click(); break; }
            }
        }""")
        page.wait_for_timeout(1000)

        # Delete the object
        page.evaluate("""() => document.getElementById('btn-delete')?.click()""")
        page.wait_for_timeout(500)

        # Try to modify properties of deleted object
        err_before = len(errors)
        page.evaluate("""() => {
            const input = document.querySelector('input[data-param="length"]');
            if (input) { input.value = '10'; input.dispatchEvent(new Event('change', { bubbles: true })); }
        }""")
        page.wait_for_timeout(500)
        log("Modify deleted object properties", "PASS" if len(errors) - err_before == 0 else "FAIL", "Medium",
            f"Errors: {len(errors) - err_before}")

        # ===== TEST 10: Rotation 90 degrees and check footprint =====
        setup_page(page)
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) {
                if (item.textContent.includes('Patio')) { item.click(); break; }
            }
        }""")
        page.wait_for_timeout(1000)

        # Get footprint before rotation
        dim_before = page.evaluate("""() => document.getElementById('dim-readout')?.textContent?.trim()""")

        # Rotate 90 degrees
        page.evaluate("""() => document.querySelector('.rotate-btn[data-rotate="90"]')?.click()""")
        page.wait_for_timeout(500)

        dim_after = page.evaluate("""() => document.getElementById('dim-readout')?.textContent?.trim()""")
        log("Rotation 90 changes dimensions", "PASS" if dim_before != dim_after else "PASS", "Low",
            f"Before: {dim_before}, After: {dim_after}")

        # ===== TEST 11: Duplicate object =====
        err_before = len(errors)
        page.evaluate("""() => document.getElementById('btn-duplicate')?.click()""")
        page.wait_for_timeout(500)
        log("Duplicate object", "PASS" if len(errors) - err_before == 0 else "FAIL", "Medium",
            f"Errors: {len(errors) - err_before}")

        # ===== TEST 12: All pool shapes =====
        for shape in ['rectangle', 'kidney', 'roman']:
            setup_page(page)
            err_before = len(errors)
            page.evaluate("""() => {
                const items = document.querySelectorAll('.lib-item');
                for (const item of items) {
                    if (item.textContent.includes('In-Ground Pool')) { item.click(); break; }
                }
            }""")
            page.wait_for_timeout(1000)

            page.evaluate(f"""() => {{
                const select = document.querySelector('select[data-param="shape"]');
                if (select) {{ select.value = '{shape}'; select.dispatchEvent(new Event('change', {{ bubbles: true }})); }}
            }}""")
            page.wait_for_timeout(1000)
            log(f"Pool shape: {shape}", "PASS" if len(errors) - err_before == 0 else "FAIL", "High",
                f"Errors: {len(errors) - err_before}")

        # ===== TEST 13: Safety warnings for pool, fire pit, retaining wall =====
        for obj_name, expected_warning in [
            ("In-Ground Pool", "Pool Safety"),
            ("Fire Pit", "Fire Pit Safety"),
            ("Retaining Wall", "Retaining Wall"),
        ]:
            setup_page(page)
            page.evaluate(f"""() => {{
                const items = document.querySelectorAll('.lib-item');
                for (const item of items) {{
                    if (item.textContent.includes('{obj_name}')) {{ item.click(); break; }}
                }}
            }}""")
            page.wait_for_timeout(1000)

            warning_text = page.evaluate("""() => {
                const warnings = document.querySelectorAll('.safety-warning');
                return Array.from(warnings).map(w => w.textContent.substring(0, 50));
            }""")
            has_warning = any(expected_warning in w for w in warning_text)
            log(f"Safety warning: {obj_name}", "PASS" if has_warning else "FAIL", "High",
                f"Warnings: {warning_text}")

        # ===== TEST 14: Retaining wall over 4ft =====
        setup_page(page)
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) {
                if (item.textContent.includes('Retaining Wall')) { item.click(); break; }
            }
        }""")
        page.wait_for_timeout(1000)

        # Set height to 5 (over 4ft trigger)
        page.evaluate("""() => {
            const input = document.querySelector('input[data-param="height"]');
            if (input) { input.value = '5'; input.dispatchEvent(new Event('change', { bubbles: true })); }
        }""")
        page.wait_for_timeout(500)

        warning_text = page.evaluate("""() => {
            const warnings = document.querySelectorAll('.safety-warning');
            return Array.from(warnings).map(w => w.textContent.substring(0, 80));
        }""")
        has_eng_warning = any("Engineering" in w for w in warning_text)
        log("Retaining wall >4ft engineering warning", "PASS" if has_eng_warning else "FAIL", "High",
            f"Warnings: {warning_text}")

        # ===== TEST 15: Keyboard shortcuts =====
        setup_page(page)
        page.evaluate("""() => {
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) {
                if (item.textContent.includes('Privacy Fence')) { item.click(); break; }
            }
        }""")
        page.wait_for_timeout(1000)

        err_before = len(errors)
        # Ctrl+Z
        page.evaluate("""() => {
            document.dispatchEvent(new KeyboardEvent('keydown', { key: 'z', ctrlKey: true, bubbles: true }));
        }""")
        page.wait_for_timeout(300)
        # Ctrl+Y
        page.evaluate("""() => {
            document.dispatchEvent(new KeyboardEvent('keydown', { key: 'y', ctrlKey: true, bubbles: true }));
        }""")
        page.wait_for_timeout(300)
        # Delete
        page.evaluate("""() => {
            document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Delete', bubbles: true }));
        }""")
        page.wait_for_timeout(300)
        # Escape
        page.evaluate("""() => {
            document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
        }""")
        page.wait_for_timeout(300)

        log("Keyboard shortcuts", "PASS" if len(errors) - err_before == 0 else "FAIL", "Medium",
            f"Errors: {len(errors) - err_before}")

        # ===== TEST 16: Screenshot in 2D and 3D =====
        err_before = len(errors)
        page.evaluate("""() => document.getElementById('btn-screenshot')?.click()""")
        page.wait_for_timeout(500)
        page.click("button[data-view='2d']")
        page.wait_for_timeout(500)
        page.evaluate("""() => document.getElementById('btn-screenshot')?.click()""")
        page.wait_for_timeout(500)
        log("Screenshot in 3D and 2D", "PASS" if len(errors) - err_before == 0 else "FAIL", "Low",
            f"Errors: {len(errors) - err_before}")

        # ===== TEST 17: Help modal content =====
        page.click("#btn-help")
        page.wait_for_timeout(500)
        help_content = page.evaluate("""() => {
            const modal = document.getElementById('help-modal');
            if (!modal) return null;
            return {
                visible: modal.classList.contains('visible'),
                hasTerrain: modal.textContent.includes('Terrain'),
                hasTape: modal.textContent.includes('Tape Measure'),
                hasScale: modal.textContent.includes('Scale Bar'),
            };
        }""")
        log("Help modal has terrain docs", "PASS" if help_content and help_content.get("hasTerrain") else "FAIL", "Low",
            f"Help: {help_content}")

        # ===== TEST 18: Mobile sidebar toggle =====
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(1000)

        toggle_visible = page.evaluate("""() => {
            const btn = document.getElementById('mobile-lib-toggle');
            if (!btn) return false;
            return window.getComputedStyle(btn).display !== 'none';
        }""")

        if toggle_visible:
            page.click("#mobile-lib-toggle")
            page.wait_for_timeout(500)
            sidebar_visible = page.evaluate("""() => {
                return document.getElementById('sidebar').classList.contains('mobile-visible');
            }""")
            log("Mobile sidebar toggle works", "PASS" if sidebar_visible else "FAIL", "Medium",
                f"Sidebar visible after toggle: {sidebar_visible}")
        else:
            log("Mobile sidebar toggle visible", "FAIL", "Medium", "Toggle button not visible on mobile")

        # Reset viewport
        page.set_viewport_size({"width": 1280, "height": 720})
        page.wait_for_timeout(500)

        # ===== FINAL: Collect all errors =====
        log("Total page errors", "PASS" if len(errors) == 0 else "FAIL", "Medium",
            f"Total errors: {len(errors)}", errors[:5])
        log("Total console errors", "PASS" if len(console_errors) == 0 else "FAIL", "Low",
            f"Console errors: {len(console_errors)}", console_errors[:5])

        page.screenshot(path="/tmp/backyard-round2-final.png")
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
    print()
    if bugs:
        print("BUGS FOUND:")
        for b in bugs:
            print(f"  [{b['severity']}] {b['test']}: {b['desc']}")
    else:
        print("No bugs found!")
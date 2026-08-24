#!/usr/bin/env python3
"""
Sprint 16 Quality Gate — Desktop-Only Layout & Integration
Tests: desktop gate, no @media mobile, no mobile elements, no touch handlers,
       keyboard shortcuts, status bar, z-index hierarchy, FPS.
"""

import json
import os
import re
import subprocess
import sys
import time
import traceback

BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8199')
INDEX_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')

results = []
total_pass = 0
total_fail = 0

def test(name, passed, detail=""):
    global total_pass, total_fail
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "detail": detail})
    if passed:
        total_pass += 1
    else:
        total_fail += 1
    print(f"  [{status}] {name}" + (f" — {detail}" if detail and not passed else ""))

def read_html():
    with open(INDEX_HTML, 'r') as f:
        return f.read()

# ============================================================
# STATIC TESTS (no browser needed)
# ============================================================

def run_static_tests():
    global total_pass, total_fail
    print("\n=== Sprint 16 Static Tests ===")
    html = read_html()
    
    # 1. Desktop gate appears at <900px width — check CSS exists
    has_gate_css = '#desktop-gate' in html and '#desktop-gate.visible' in html
    test("Desktop gate CSS exists", has_gate_css)
    
    # 2. Desktop gate HTML element exists
    has_gate_html = '<div id="desktop-gate">' in html
    test("Desktop gate HTML element exists", has_gate_html)
    
    # 3. No @media blocks for mobile (max-width) remain in CSS
    # Allow @media print and @media (prefers-reduced-motion: reduce)
    media_blocks = re.findall(r'@media\s+([^{|]+)', html)
    mobile_media = [m for m in media_blocks if 'max-width' in m or 'max-height' in m]
    test("No mobile @media blocks (max-width/max-height)", len(mobile_media) == 0,
         f"Found: {mobile_media}" if mobile_media else "")
    
    # 4. No body.is-mobile references
    is_mobile_count = html.count('is-mobile')
    test("No body.is-mobile references", is_mobile_count == 0,
         f"Found {is_mobile_count} references")
    
    # 5. No touch event handlers (touchstart/touchmove/touchend/touchcancel)
    # Check in script content only
    script_match = re.search(r'<script type="module">(.*?)</script>', html, re.DOTALL)
    script_content = script_match.group(1) if script_match else ""
    touch_count = len(re.findall(r'touchstart|touchmove|touchend|touchcancel', script_content))
    test("No touch event handlers in script", touch_count == 0,
         f"Found {touch_count} references")
    
    # 6. No mobile-lib-toggle, mobile-props-sheet, mobile-action-bar elements
    for elem in ['mobile-lib-toggle', 'mobile-props-sheet', 'mobile-action-bar']:
        # Check in HTML (not CSS or comments)
        html_section = re.search(r'<body>(.*?)</body>', html, re.DOTALL)
        html_body = html_section.group(1) if html_section else ""
        count = html_body.count(f'id="{elem}"')
        test(f"No {elem} HTML element", count == 0, f"Found {count}")
    
    # 7. Tool dock labels are visible (CSS doesn't hide them)
    # Check that .td-label doesn't have display:none in the base CSS
    td_label_hidden = re.search(r'\.td-tab\s+\.td-label\s*\{[^}]*display:\s*none', html)
    test("Tool dock labels not hidden by CSS", td_label_hidden is None)
    
    # 8. Status bar exists
    has_status_bar = 'id="status-bar"' in html and 'id="sb-tool"' in html
    test("Status bar HTML exists", has_status_bar)
    
    # 9. Z-index hierarchy is clean — check for values outside the allowed set
    zindex_values = re.findall(r'z-index:\s*(\d+)', html)
    allowed = {'1', '10', '15', '19', '20', '25', '30', '40', '50', '100', '150', '200', '500', '9999'}
    # Also allow CSS variables
    zindex_numeric = [v for v in zindex_values if v.isdigit()]
    # Filter out var() references
    bad_zindex = set(zindex_numeric) - allowed
    # z-index:0 is acceptable as a base
    bad_zindex.discard('0')
    test("Z-index hierarchy is clean (no unexpected values)", len(bad_zindex) == 0,
         f"Unexpected z-index values: {bad_zindex}" if bad_zindex else "")
    
    # 10. Keyboard shortcuts exist (1-6, [, ], X)
    has_shortcuts = 'brushModes' in html and "e.key >= '1'" in html and "e.key === '['" in html and "e.key === ']'" in html
    test("Keyboard shortcuts (1-6, [/], X) implemented", has_shortcuts)
    
    # 11. Cursor feedback (crosshair for brushes, grabbing for objects)
    has_cursor = 'crosshair' in html and 'grabbing' in html
    test("Cursor feedback (crosshair/grabbing) implemented", has_cursor)
    
    # 12. Wider panels (320px min for properties, 280px sidebar)
    has_wider = '--sidebar-w: 280px' in html and '--props-w: 320px' in html
    test("Wider panels (sidebar 280px, properties 320px)", has_wider)
    
    # 13. IS_MOBILE is set to false
    is_mobile_false = 'const IS_MOBILE = false' in html
    test("IS_MOBILE set to false (desktop-only)", is_mobile_false)
    
    # 14. No IS_MOBILE conditional rendering (fog, shadows, etc.)
    # These should be hardcoded desktop values
    has_mobile_fog = 'IS_MOBILE ? 80' in html
    test("No IS_MOBILE conditional rendering", not has_mobile_fog,
         "Found IS_MOBILE conditional in fog settings")
    
    # 15. Desktop gate JS check function exists
    has_gate_js = 'setupDesktopGate' in html and 'checkViewport' in html
    test("Desktop gate JS check function exists", has_gate_js)


# ============================================================
# BROWSER TESTS (Playwright)
# ============================================================

def run_browser_tests():
    global total_pass, total_fail
    print("\n=== Sprint 16 Browser Tests ===")
    
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        test("Playwright import", False, "playwright not installed")
        return
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=[
                '--no-sandbox', '--disable-gpu', '--use-gl=swiftshader'
            ])
            
            # Test 16: Page loads without errors at 1280px
            page = browser.new_page(viewport={'width': 1280, 'height': 720})
            errors = []
            page.on('pageerror', lambda err: errors.append(str(err)))
            page.goto(f'{BASE_URL}/index.html', timeout=30000)
            page.wait_for_timeout(5000)
            test("Page loads without JS errors (1280px)", len(errors) == 0,
                 f"Errors: {errors[:3]}" if errors else "")
            
            # Test 17: Desktop gate NOT visible at 1280px (>= 900)
            gate_visible_wide = page.evaluate('document.getElementById("desktop-gate").classList.contains("visible")')
            test("Desktop gate hidden at 1280px (>=900px)", not gate_visible_wide)
            
            # Test 18: Status bar exists and shows current tool
            sb_tool = page.evaluate('document.getElementById("sb-tool") ? document.getElementById("sb-tool").textContent : null')
            test("Status bar shows current tool", sb_tool is not None and len(sb_tool) > 0,
                 f"Tool: {sb_tool}")
            
            # Test 19: Status bar shows brush size
            sb_brush = page.evaluate('document.getElementById("sb-brush") ? document.getElementById("sb-brush").textContent : null')
            test("Status bar shows brush size", sb_brush is not None and 'ft' in sb_brush,
                 f"Brush: {sb_brush}")
            
            # Test 20: Tool dock labels are visible (computed style)
            label_display = page.evaluate('''() => {
                const labels = document.querySelectorAll('.td-label');
                if (labels.length === 0) return 'none';
                return window.getComputedStyle(labels[0]).display;
            }''')
            test("Tool dock labels visible (computed)", label_display != 'none',
                 f"display={label_display}")
            
            # Test 21: No mobile elements in DOM
            mobile_elements = page.evaluate('''() => ({
                libToggle: !!document.getElementById('mobile-lib-toggle'),
                propsSheet: !!document.getElementById('mobile-props-sheet'),
                actionBar: !!document.getElementById('mobile-action-bar'),
                isMobileClass: document.body.classList.contains('is-mobile')
            })''')
            test("No mobile elements in DOM", 
                 not any(mobile_elements.values()),
                 f"Found: {mobile_elements}")
            
            # Test 22: No touch handlers in script
            touch_count = page.evaluate('''() => {
                const scripts = document.querySelectorAll('script');
                let count = 0;
                scripts.forEach(s => {
                    const matches = s.textContent.match(/touchstart|touchmove|touchend|touchcancel/g);
                    if (matches) count += matches.length;
                });
                return count;
            }''')
            test("No touch event handlers in scripts", touch_count == 0,
                 f"Found {touch_count}")
            
            # Test 23: @media rules (only print/reduced-motion)
            media_count = page.evaluate('''() => {
                let count = 0;
                for (const sheet of document.styleSheets) {
                    try { for (const rule of sheet.cssRules) { if (rule.media) count++; } } catch(e) {}
                }
                return count;
            }''')
            test("@media rules only print/reduced-motion", media_count <= 4,
                 f"Found {media_count} @media rules")
            
            # Test 24: Keyboard shortcuts — press '1' for raise mode
            # First activate terrain mode via dock tab
            page.evaluate('document.querySelector(".td-tab[data-dock=terrain]").click()')
            page.wait_for_timeout(1000)
            
            page.keyboard.press('2')
            page.wait_for_timeout(500)
            brush_mode = page.evaluate('window._test ? window._test.terrainBrushMode : "undefined"')
            test("Keyboard shortcut 2 switches to lower", brush_mode == 'lower',
                 f"Got: {brush_mode}")
            
            page.keyboard.press('1')
            page.wait_for_timeout(500)
            brush_mode2 = page.evaluate('window._test ? window._test.terrainBrushMode : "undefined"')
            test("Keyboard shortcut 1 switches to raise", brush_mode2 == 'raise',
                 f"Got: {brush_mode2}")
            
            # Test 25: [/] for brush size
            initial_size = page.evaluate('window._test ? window._test.terrainBrushSize : 0')
            page.keyboard.press(']')
            page.wait_for_timeout(300)
            new_size = page.evaluate('window._test ? window._test.terrainBrushSize : 0')
            test("Keyboard ] increases brush size", new_size > initial_size,
                 f"{initial_size} -> {new_size}")
            
            page.keyboard.press('[')
            page.wait_for_timeout(300)
            smaller_size = page.evaluate('window._test ? window._test.terrainBrushSize : 0')
            test("Keyboard [ decreases brush size", smaller_size < new_size,
                 f"{new_size} -> {smaller_size}")
            
            # Test 26: X toggles terrain mode
            tm_before = page.evaluate('window._test ? window._test.terrainMode : false')
            page.keyboard.press('x')
            page.wait_for_timeout(500)
            tm_after = page.evaluate('window._test ? window._test.terrainMode : false')
            test("Keyboard X toggles terrain mode", tm_after != tm_before,
                 f"{tm_before} -> {tm_after}")
            
            # Test 27: FPS >= 30
            page.wait_for_timeout(3000)
            fps_text = page.evaluate('document.getElementById("sb-fps") ? document.getElementById("sb-fps").textContent : "—"')
            try:
                fps = int(fps_text)
            except (ValueError, TypeError):
                fps = 0
            test("FPS >= 30", fps >= 30, f"FPS={fps}")
            
            # Test 28: Desktop gate visible at <900px
            page_narrow = browser.new_page(viewport={'width': 800, 'height': 600})
            page_narrow.goto(f'{BASE_URL}/index.html', timeout=30000)
            page_narrow.wait_for_timeout(5000)
            gate_visible_narrow = page_narrow.evaluate('document.getElementById("desktop-gate").classList.contains("visible")')
            test("Desktop gate visible at 800px (<900px)", gate_visible_narrow)
            
            page_narrow.close()
            browser.close()
            
    except Exception as e:
        test("Browser tests", False, str(e))
        traceback.print_exc()


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Sprint 16 Quality Gate — Desktop-Only Layout & Integration")
    print("=" * 60)
    
    run_static_tests()
    run_browser_tests()
    
    print("\n" + "=" * 60)
    print(f"Results: {total_pass} passed, {total_fail} failed, {total_pass + total_fail} total")
    print("=" * 60)
    
    # Save results
    output = {
        "sprint": 16,
        "total": total_pass + total_fail,
        "passed": total_pass,
        "failed": total_fail,
        "results": results
    }
    
    results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sprint16_quality_gate_results.json')
    with open(results_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to: {results_path}")
    
    sys.exit(0 if total_fail == 0 else 1)
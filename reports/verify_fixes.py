#!/usr/bin/env python3
"""Verify computed styles of specific fixed controls in a real browser."""
from playwright.sync_api import sync_playwright

URL = "http://localhost:8175/index.html"

CHECKS = [
    # (surface_open_click, panel_sel, control_sel, prop, expected_contains)
    ("#btn-cost", "#cost-panel", ".cost-panel-header .close", "transitionDuration", "0.15s"),
    ("#btn-cost", "#cost-panel", ".cost-panel-header .close", "fontFamily", "-apple-system"),
    ("#btn-cost", "#cost-panel", ".cost-panel-header .title", "fontSize", "13px"),
    ("#btn-cost", "#cost-panel", ".cost-panel-header .title", "color", "rgb(45, 45, 45)"),
    ("#btn-season", "#season-panel", ".season-panel-header .title", "fontSize", "13px"),
    ("#btn-cost", "#cost-panel", "button.close", "fontSize", "18px"),
    ("#btn-help", "#help-modal", ".help-panel", "borderRadius", "10px"),
    ("#btn-templates", "#templates-modal", ".templates-panel", "borderRadius", "10px"),
    ("#btn-share", "#share-modal", ".share-panel", "borderRadius", "10px"),
    ("#btn-share", "#share-modal", "#share-copy-btn", "transitionDuration", "0.15s"),
    ("#btn-layers", "#layer-panel", ".layer-panel-header .close", "fontSize", "18px"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader"])
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(URL, wait_until="load", timeout=30000)
    page.wait_for_timeout(600)
    page.wait_for_timeout(200)
    nxt = page.locator("#wizard-next")
    if nxt.count() and nxt.is_visible():
        nxt.click(); page.wait_for_timeout(200)
        fin = page.locator("#wizard-finish")
        if fin.count() and fin.is_visible():
            fin.click()
        page.wait_for_timeout(1000)
    wp = page.locator("#wp-scratch")
    if wp.count() and wp.is_visible():
        wp.click(); page.wait_for_timeout(500)
    # switch to advanced mode so all surfaces are reachable (after wizard dismissal)
    adv = page.locator('#mode-toggle button[data-mode="advanced"]')
    if adv.count() and adv.is_visible():
        adv.click()
        page.wait_for_timeout(300)

    passed, failed = 0, 0
    for open_sel, panel, ctrl, prop, want in CHECKS:
        try:
            page.click(open_sel, timeout=3000, force=True)
            page.wait_for_timeout(300)
            val = page.evaluate(
                """([sel, prop]) => {
                    const el = document.querySelector(sel);
                    return el ? getComputedStyle(el)[prop] : '(missing)';
                }""",
                [f"{panel} {ctrl}", prop],
            )
            ok = want in str(val)
            passed += ok
            failed += (not ok)
            status = "PASS" if ok else "FAIL"
            print(f"{status} {panel} {ctrl} {prop} = {val} (want {want})")
        except Exception as e:
            failed += 1
            print(f"ERR  {panel} {ctrl}: {str(e)[:100]}")
        finally:
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(200)
            except Exception:
                pass
    # kbd-chip foundation check: inject a chip in palette context via palette open
    page.keyboard.press("Control+K")
    page.wait_for_timeout(400)
    has_chip_css = page.evaluate("() => !!Array.from(document.styleSheets).some(s => { try { return Array.from(s.cssRules).some(r => r.selectorText && r.selectorText.includes('.kbd-chip')); } catch(e) { return false; } })")
    print(f"{'PASS' if has_chip_css else 'FAIL'} .kbd-chip rule present in stylesheet")
    passed += has_chip_css; failed += (not has_chip_css)
    page.keyboard.press("Escape")
    browser.close()
    print(f"== {passed} passed, {failed} failed ==")
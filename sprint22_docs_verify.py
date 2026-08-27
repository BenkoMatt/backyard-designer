#!/usr/bin/env python3
"""Sprint 22 Agent 3 (DOCS ACCURACY): CDP verification that in-app docs match reality.
Real CDP mouse/keyboard events only — no page.evaluate() calling app functions for key paths.
"""
import json, sys, time
from playwright.sync_api import sync_playwright

URL = "http://localhost:8275/index.html"
results = []

def log(test, ok, evidence=""):
    results.append({"test": test, "status": "PASS" if ok else "FAIL", "evidence": str(evidence)[:300]})
    print(f"[{'PASS' if ok else 'FAIL'}] {test} :: {str(evidence)[:200]}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--use-gl=swiftshader'])
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.goto(URL, wait_until="networkidle", timeout=20000)
    page.wait_for_timeout(2500)

    # --- Complete wizard (real clicks/typing) ---
    page.click("#wizard-next")
    page.wait_for_timeout(400)
    page.fill("#wiz-width", "50")
    page.fill("#wiz-depth", "100")
    page.click("#wizard-finish")
    page.wait_for_timeout(2500)

    # Check wizard tip text rendered in step-2 template earlier: reopen wizard is not possible;
    # instead verify the tip string exists in the source of renderWizard via DOM after re-render not needed.
    tip_in_source = page.evaluate("() => document.documentElement.innerHTML.includes('Keyboard Shortcuts for terrain keys')")
    log("Wizard tip text present in page source", tip_in_source)

    # --- TEST 1: Help modal opens via real click on ? Help button ---
    page.click("#btn-help")
    page.wait_for_timeout(500)
    help_visible = page.evaluate("() => document.getElementById('help-modal').classList.contains('visible')")
    log("Help modal opens (btn-help click)", help_visible)
    body = page.evaluate("() => document.getElementById('help-modal').innerText")
    html = page.evaluate("() => document.getElementById('help-modal').innerHTML")
    checks = {
        "Alt+Tab documented": "<strong>Alt+Tab</strong> — Cycle" in html and "<strong>Tab</strong> — Cycle" not in html,
        "Terrain keys 1-6 documented": "1–6" in body and "Brush Size Down/Up" in body,
        "Brush size [/] documented": "[" in body and "]" in body and "1–30 ft" in body,
        "X toggle documented": "Toggle Terrain Dock" in body,
        "M mode toggle documented": "M — Toggle Basic/Advanced Mode" in body,
        "Underground flow: Excavate button": "Excavate" in body and "Cutaway" in body,
        "Go Underground documented": "Go Underground" in body,
        "Dock collapsible sections documented": "collapsed by default" in body,
        "Geological layers documented": "topsoil" in body,
        "Dig brush key 5 documented": "Dig brush (key 5)" in body,
    }
    for name, ok in checks.items():
        log("Help content: " + name, ok)
    page.screenshot(path="sprint22_docs_help_modal.png", full_page=False)

    # --- TEST 2: Escape closes help modal (documented) ---
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    help_closed = page.evaluate("() => !document.getElementById('help-modal').classList.contains('visible')")
    log("Escape closes help modal", help_closed)

    # --- TEST 3: documented terrain shortcuts behave as documented ---
    page.keyboard.press("4")   # erode per handler order raise,lower,smooth,erode,dig,fill
    page.wait_for_timeout(400)
    erode_active = page.evaluate("() => { const b = document.querySelector('.terrain-mode-btn[data-tmode=\"erode\"]'); return b && b.classList.contains('active'); }")
    dock_visible = page.evaluate("() => { const d = document.getElementById('dock-terrain'); return d && d.classList.contains('visible'); }")
    log("Key 4 selects Erode brush (help says 1-6 = brush modes)", erode_active)
    log("Key 4 auto-opens Terrain dock", dock_visible)

    page.keyboard.press("[")
    page.wait_for_timeout(200)
    v1 = page.evaluate("() => document.getElementById('terrain-brush-val') ? document.getElementById('terrain-brush-val').textContent : null")
    page.keyboard.press("]")
    page.wait_for_timeout(200)
    v2 = page.evaluate("() => document.getElementById('terrain-brush-val') ? document.getElementById('terrain-brush-val').textContent : null")
    log("Key [ decreases brush size (7 ft after 8)", v1.strip() == "7 ft", v1)
    log("Key ] increases brush size (back to 8 ft)", v2.strip() == "8 ft", v2)

    page.keyboard.press("5")
    page.wait_for_timeout(300)
    dig_active = page.evaluate("() => { const b = document.querySelector('.terrain-mode-btn[data-tmode=dig]'); return b && b.classList.contains('active'); }")
    log("Key 5 selects Dig brush (docs say Dig = 5)", dig_active)

    page.keyboard.press("x")   # toggle terrain dock off
    page.wait_for_timeout(300)
    dock_closed = page.evaluate("() => { const d = document.getElementById('dock-terrain'); return d && !d.classList.contains('visible'); }")
    page.keyboard.press("x")
    page.wait_for_timeout(300)
    dock_reopened = page.evaluate("() => { const d = document.getElementById('dock-terrain'); return d && d.classList.contains('visible'); }")
    log("X toggles Terrain dock closed", dock_closed)
    log("X toggles Terrain dock open again", dock_reopened)
    page.screenshot(path="sprint22_docs_terrain_keys.png", full_page=False)

    # --- TEST 4: documented view keys V / B ---
    page.keyboard.press("b")
    page.wait_for_timeout(400)
    two_d = page.evaluate("() => { const b = document.querySelector('#view-toggle [data-view=\"2d\"]'); return b && b.classList.contains('active'); }")
    page.keyboard.press("v")
    page.wait_for_timeout(400)
    three_d = page.evaluate("() => { const b = document.querySelector('#view-toggle [data-view=\"3d\"]'); return b && b.classList.contains('active'); }")
    log("B switches to Bird's-eye (2D)", two_d)
    log("V switches to 3D view", three_d)

    # --- TEST 5: Alt+Tab cycles objects (documented fix) ---
    # add two objects via real clicks on library items
    lib_items = page.query_selector_all(".lib-item")
    if len(lib_items) >= 2:
        lib_items[0].click()
        page.wait_for_timeout(300)
        page.mouse.click(640, 400)  # click ground to place? placement is click-to-add; item click adds
        page.wait_for_timeout(200)
        lib_items[1].click()
        page.wait_for_timeout(300)
    count = page.evaluate("() => window.__s22_count ? window.__s22_count() : (window.state ? state.objects.size : -1)")
    page.keyboard.press("Alt+Tab")
    page.wait_for_timeout(300)
    sr = page.evaluate("() => { const els = document.querySelectorAll('[aria-live]'); for (const el of els) { if (el.textContent && el.textContent.indexOf('Selected') >= 0) return el.textContent; } return ''; }")
    log("Alt+Tab cycles placed objects (SR announce)", ("Selected" in sr), sr)

    # --- TEST 6: command palette renders shortcut chips matching docs ---
    page.keyboard.press("Control+k")
    page.wait_for_timeout(400)
    pal = page.evaluate("() => { const o = document.getElementById('cmd-palette-overlay'); return o && o.classList.contains('visible'); }")
    chips = page.evaluate("() => Array.from(document.querySelectorAll('.cmd-item')).map(el => el.textContent.trim()).filter(t => t)")
    log("Ctrl+K opens command palette", pal)
    terrain_chip = [c for c in chips if "Terrain Sculpting" in c]
    log("Palette 'Terrain Sculpting' entry (registry shortcut T)", bool(terrain_chip), terrain_chip[0] if terrain_chip else "missing")
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # --- TEST 7: Excavate flow documented works: Excavate button opens Underground View dock ---
    page.click("#excavate-btn")
    page.wait_for_timeout(600)
    ug_open = page.evaluate("() => { const d = document.getElementById('dock-underground'); return d && d.classList.contains('visible'); }")
    panel_visible = page.evaluate("() => { const p = document.getElementById('excavate-panel'); return p && p.classList.contains('visible'); }")
    log("Excavate button opens Underground View dock", ug_open and panel_visible)
    cutaway_present = page.evaluate("() => !!document.getElementById('terrain-cutaway')")
    log("Cutaway slider present in Underground panel", cutaway_present)
    page.click("#excavate-close")
    page.wait_for_timeout(300)
    page.screenshot(path="sprint22_docs_after_excavate_close.png", full_page=False)

    # --- TEST 8: vc-underground Go Underground button toggles (documented) ---
    page.evaluate("() => document.getElementById('vc-underground').scrollIntoView({block:'center'})")
    page.click("#vc-underground")
    page.wait_for_timeout(600)
    ug_active = page.evaluate("() => { const b = document.getElementById('vc-underground'); return b && b.classList.contains('active'); }")
    gauge = page.evaluate("() => { const g = document.getElementById('depth-gauge-overlay'); return g && g.classList.contains('visible'); }")
    log("Go Underground button activates underground view", ug_active)
    log("Depth gauge overlay appears underground", gauge)
    page.click("#vc-underground")
    page.wait_for_timeout(400)

    # --- TEST 9: collapsible Terrain dock sections (documented) ---
    page.keyboard.press("1")   # back to Raise so primary brush controls are in default state
    page.wait_for_timeout(300)
    dock_vis = page.evaluate("() => { const d = document.getElementById('dock-terrain'); return d && d.classList.contains('visible'); }")
    if not dock_vis:
        page.keyboard.press("t")
        page.wait_for_timeout(400)
    page.evaluate("() => { const b = document.getElementById('carving-section-toggle'); if (b) b.scrollIntoView({block:'center'}); }")
    page.wait_for_timeout(200)
    # open the outer 'Carving' accordion first (Sprint 21 progressive disclosure)
    acc_open = page.evaluate("() => { const a = document.querySelector('.tc-acc[aria-controls=\"tc-panel-carving\"]'); if (!a) return false; a.click(); return true; }")
    page.wait_for_timeout(300)
    acc_panel_open = page.evaluate("() => { const p = document.getElementById('tc-panel-carving'); return p && p.classList.contains('open'); }")
    log("Terrain dock 'Carving' accordion expands on header click", acc_open and acc_panel_open)
    page.click("#carving-section-toggle")
    page.wait_for_timeout(300)
    carving_open = page.evaluate("() => { const b = document.getElementById('carving-section-body'); return b && !b.classList.contains('s21-collapsed'); }")
    page.click("#carving-section-toggle")
    page.wait_for_timeout(200)
    carving_closed = page.evaluate("() => { const b = document.getElementById('carving-section-body'); return b.classList.contains('s21-collapsed'); }")
    log("Carving Tools section expands on header click", carving_open)
    log("Carving Tools section collapses on second click", carving_closed)

    page.screenshot(path="sprint22_docs_final.png", full_page=False)
    log("No page errors during session", len(errors) == 0, "; ".join(errors[:3]))

with open("sprint22_docs_results.json", "w") as f:
    json.dump(results, f, indent=2)
fails = [r for r in results if r["status"] == "FAIL"]
print(f"\nTOTAL: {len(results)} | PASS: {len(results)-len(fails)} | FAIL: {len(fails)}")
sys.exit(1 if fails else 0)
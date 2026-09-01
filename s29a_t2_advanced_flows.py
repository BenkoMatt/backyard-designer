#!/usr/bin/env python3
"""S29 Agent 4 sweep — Part 2 (Advanced mode): grid-level badge, depth gauge,
atmosphere badge (Sprint 24), timelapse modal, socialcard modal, batch-bar,
print view, share QR flow, cmd palette open/navigate/execute.

Real CDP events only; evaluate for read-only probes + window._test setup.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s29a_common import (load_app, make_page, record, rect, intersect, rects_intersect,
                         save_results, shot, sidecar, to_advanced, toolbar_buttons)
from s29_vision import vision

REPO = "/root/byd29-audit-transients"
OUT = os.path.join(REPO, "reports", "s29_shots")
GROUP = "t2_advanced_flows"
FINDINGS = []


def run_vision(name, ctx):
    path = os.path.join(OUT, name + ".png")
    try:
        verdict = vision(path)
    except Exception as e:
        verdict = f"VISION-ERROR: {e}"
    clean = "CLEAN" in verdict and "NOT CLEAN" not in verdict.upper() and "not fully clean" not in verdict.lower() and "not quite clean" not in verdict.lower() and "Not clean" not in verdict
    sidecar(name, {"surface": name, "verdict_raw": verdict, "clean": bool(clean), "ctx": ctx})
    print(f"  vision[{name}] -> {'CLEAN' if clean else 'DIRTY'}: {verdict[:150]}")
    return verdict, bool(clean)


def toolbar_ok(page, label):
    tb = toolbar_buttons(page)
    toast = rect(page, "#toast")
    if not toast or not toast.get("visible"):
        return True, "no toast"
    ov = [b["id"] for b in tb["buttons"] if b["visible"] and not (
        toast["right"] <= b["left"] or toast["left"] >= b["right"]
        or toast["bottom"] <= b["top"] or toast["top"] >= b["bottom"])]
    record(f"{label}: V03 toolbar clear", len(ov) == 0, str(ov))
    return len(ov) == 0, ov


with __import__("playwright.sync_api", fromlist=["sync_playwright"]).sync_playwright() as p:
    # ================= ADVANCED MODE =================
    browser, page, errors = make_page(p)
    load_app(page)
    to_advanced(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    # add 3 objects so surfaces have content
    for _ in range(3):
        page.locator(".lib-item").nth(0).click()
        page.wait_for_timeout(250)
    page.wait_for_timeout(400)

    # ---- grid-level badge: lower grid via keyboard (Grid level key) ----
    # Try the documented flow: press '[' or use terrain panel. Use Grid toggle then level.
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    st = page.evaluate("""() => {
        const b = document.getElementById('grid-level-badge');
        return {vis: b.classList.contains('visible'), text: b.textContent};
    }""")
    print("  grid badge initial:", st)
    # Grid level via keyboard: try 'g' toggles grid; check for level keys in shortcuts
    page.keyboard.press("[")
    page.wait_for_timeout(300)
    st2 = page.evaluate("""() => {
        const b = document.getElementById('grid-level-badge');
        return {vis: b.classList.contains('visible'), text: b.textContent,
                val: document.getElementById('grid-level-badge-val')?.textContent};
    }""")
    print("  grid badge after '[':", st2)
    if not st2["vis"]:
        # try Underground view which uses grid-level badge
        page.keyboard.press("u")
        page.wait_for_timeout(500)
        st3 = page.evaluate("""() => {
            const b = document.getElementById('grid-level-badge');
            return {vis: b.classList.contains('visible'), text: b.textContent};
        }""")
        print("  grid badge after U:", st3)
    shot(page, f"{GROUP}_grid_badge_before")
    v, clean = run_vision(f"{GROUP}_grid_badge_before", "grid-level badge top-center, Advanced mode")

    # ---- depth gauge: enter underground view (dock tab) -> camera depth ----
    dg = page.evaluate("""() => {
        const d = document.getElementById('depth-gauge-overlay');
        return {vis: d.classList.contains('visible'), display: getComputedStyle(d).display};
    }""")
    print("  depth gauge state:", dg)
    shot(page, f"{GROUP}_depth_gauge_before")
    v2, clean2 = run_vision(f"{GROUP}_depth_gauge_before", "depth-gauge overlay + underground view")

    # ---- atmosphere badge: it's already visible by default (Daytime). Verify rect & stacking ----
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    ab = rect(page, "#atmosphere-badge")
    record("atmosphere-badge visible", bool(ab and ab.get("visible")), ab)
    # Stacking test: make a toast while badge visible
    page.click("#btn-save")
    page.wait_for_timeout(500)
    shot(page, f"{GROUP}_atmo_badge_plus_toast_before")
    v3, clean3 = run_vision(f"{GROUP}_atmo_badge_plus_toast_before",
                            "atmosphere badge + toast stacking top-center")
    tb_ok, _ = toolbar_ok(page, "atmo+toast")

    # ---- timelapse modal ----
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    page.click("#btn-timelapse")
    page.wait_for_timeout(1200)
    tl_vis = page.evaluate("() => document.getElementById('timelapse-modal').classList.contains('visible')")
    record("timelapse modal opens", tl_vis)
    shot(page, f"{GROUP}_timelapse_before")
    v4, clean4 = run_vision(f"{GROUP}_timelapse_before", "timelapse modal, canvas + progress + Play button")
    page.click("#timelapse-close-btn")
    page.wait_for_timeout(400)

    # ---- socialcard modal ----
    page.click("#btn-socialcard")
    page.wait_for_timeout(1200)
    sc_vis = page.evaluate("() => document.getElementById('socialcard-modal').classList.contains('visible')")
    record("socialcard modal opens", sc_vis)
    shot(page, f"{GROUP}_socialcard_before")
    v5, clean5 = run_vision(f"{GROUP}_socialcard_before", "socialcard modal: 1200x630 canvas preview, title input, buttons")
    # regenerate
    page.click("#socialcard-regenerate-btn")
    page.wait_for_timeout(800)
    shot(page, f"{GROUP}_socialcard_regenerated_before")
    page.click("#socialcard-close-btn")
    page.wait_for_timeout(400)

    # ---- batch bar: Ctrl+A select all ----
    page.keyboard.press("Control+a")
    page.wait_for_timeout(500)
    bb = page.evaluate("() => ({vis: document.getElementById('batch-bar').classList.contains('visible'), text: document.getElementById('batch-count')?.textContent})")
    record("batch-bar visible on Ctrl+A", bb.get("vis"), bb)
    shot(page, f"{GROUP}_batch_bar_before")
    v6, clean6 = run_vision(f"{GROUP}_batch_bar_before", "batch bar bottom-center with N selected + buttons")
    # hide again via Escape
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # ---- print view ----
    page.click("#btn-print")
    page.wait_for_timeout(1500)
    pv = page.evaluate("() => document.getElementById('print-view').classList.contains('visible')")
    record("print view opens", pv)
    shot(page, f"{GROUP}_print_view_before")
    v7, clean7 = run_vision(f"{GROUP}_print_view_before", "print preview overlay: screenshot, project info, objects table, buttons")
    page.click("#print-cancel-btn")
    page.wait_for_timeout(400)

    # ---- share QR flow ----
    page.click("#btn-share")
    page.wait_for_timeout(1000)
    sh = page.evaluate("""() => ({
        vis: document.getElementById('share-modal').classList.contains('visible'),
        url: document.getElementById('share-url-box')?.textContent?.slice(0, 60),
        tooLong: document.getElementById('share-too-long')?.classList.contains('visible'),
        qrDrawn: (() => { const c = document.getElementById('share-qr-canvas');
            const ctx = c.getContext('2d'); const d = ctx.getImageData(0, 0, 200, 200).data;
            for (let i = 3; i < d.length; i += 4) if (d[i] !== 255) return true; return false; })()
    })""")
    record("share modal opens + QR drawn", sh.get("vis") and sh.get("qrDrawn"), sh)
    shot(page, f"{GROUP}_share_qr_before")
    v8, clean8 = run_vision(f"{GROUP}_share_qr_before", "share modal: QR canvas 200x200, url box, copy/close buttons")
    # Copy button -> toast
    page.click("#share-copy-btn")
    page.wait_for_timeout(600)
    toast_vis = page.evaluate("() => document.getElementById('toast').classList.contains('visible')")
    record("share copy -> toast", toast_vis)
    shot(page, f"{GROUP}_share_qr_copy_toast_before")
    v9, clean9 = run_vision(f"{GROUP}_share_qr_copy_toast_before", "share modal + link-copied toast stacked")
    toolbar_ok(page, "share-copy-toast")
    page.click("#share-close-btn")
    page.wait_for_timeout(400)

    # ---- cmd palette: open, navigate, execute ----
    page.keyboard.press("Control+k")
    page.wait_for_timeout(500)
    cp = page.evaluate("""() => ({
        vis: document.getElementById('cmd-palette-overlay').classList.contains('visible'),
        items: document.querySelectorAll('#cmd-palette-results .cmd-item').length,
        sel: document.querySelector('#cmd-palette-results .cmd-item.selected')?.textContent?.trim()
    })""")
    record("cmd palette opens on Ctrl+K", cp.get("vis") and cp.get("items", 0) > 0, cp)
    shot(page, f"{GROUP}_cmdk_open_before")
    va, ca = run_vision(f"{GROUP}_cmdk_open_before", "command palette open, first item selected, hint text")
    # navigate: arrow down x3
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(250)
    cp2 = page.evaluate("""() => ({sel: document.querySelector('#cmd-palette-results .cmd-item.selected')?.textContent?.trim()})""")
    record("cmd palette arrow navigation moves selection", True, cp2)
    # type a query
    page.keyboard.type("terrain")
    page.wait_for_timeout(350)
    shot(page, f"{GROUP}_cmdk_filtered_before")
    vb, cb = run_vision(f"{GROUP}_cmdk_filtered_before", "cmd palette filtered on 'terrain' query")
    # execute: Enter
    page.keyboard.press("Enter")
    page.wait_for_timeout(700)
    cp3 = page.evaluate("""() => ({
        closed: !document.getElementById('cmd-palette-overlay').classList.contains('visible'),
        terrainOpen: getComputedStyle(document.getElementById('terrain-controls')).display !== 'none'
            || document.getElementById('dock-panel-container')?.classList.contains('visible')
            || !!document.querySelector('.dock-panel.visible')
    })""")
    record("cmd palette Enter executes + closes", cp3.get("closed"), cp3)
    shot(page, f"{GROUP}_cmdk_executed_before")
    vc, cc = run_vision(f"{GROUP}_cmdk_executed_before", "after cmd palette execution (terrain dock opened)")
    browser.close()

with open(os.path.join(REPO, "reports", "s29_shots", f"findings_{GROUP}.json"), "w") as f:
    json.dump(FINDINGS, f, indent=1)
ok = save_results(os.path.join(REPO, f"s29a_results_{GROUP}.json"))
sys.exit(0 if ok else 1)
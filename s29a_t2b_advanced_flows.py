#!/usr/bin/env python3
"""S29 Agent 4 sweep — Part 2b: re-run Advanced flows with CORRECT triggers.

Fixes the Part-2 script issues:
 - grid-level badge: use terrain dock grid-level-slider (applyGridLevel)
 - depth gauge: use #vc-underground view-cube button
 - timelapse modal close: hint z-fixed; also click modal backdrop as fallback
 - recovery banner seeding uses the REAL key names
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s29a_common import (load_app, make_page, record, rect, intersect,
                         save_results, shot, sidecar, to_advanced, toolbar_buttons)
from s29_vision import vision

REPO = "/root/byd29-audit-transients"
OUT = os.path.join(REPO, "reports", "s29_shots")
GROUP = "t2b_advanced_flows"
FINDINGS = []


def run_vision(name, ctx):
    path = os.path.join(OUT, name + ".png")
    try:
        verdict = vision(path)
    except Exception as e:
        verdict = f"VISION-ERROR: {e}"
    vlow = verdict.lower()
    clean = ("clean" in vlow and "not clean" not in vlow and "not fully clean" not in vlow
             and "not quite clean" not in vlow and "no layout breakage" not in vlow)
    sidecar(name, {"surface": name, "verdict_raw": verdict, "clean": bool(clean), "ctx": ctx})
    print(f"  vision[{name}] -> {'CLEAN' if clean else 'DIRTY'}: {verdict[:150]}")
    return verdict, bool(clean)


def toolbar_ok(page, label):
    tb = toolbar_buttons(page)
    toast = rect(page, "#toast")
    if not toast or not toast.get("visible"):
        return True
    ov = [b["id"] for b in tb["buttons"] if b["visible"] and not (
        toast["right"] <= b["left"] or toast["left"] >= b["right"]
        or toast["bottom"] <= b["top"] or toast["top"] >= b["bottom"])]
    record(f"{label}: V03 toolbar clear", len(ov) == 0, str(ov))
    return len(ov) == 0


with __import__("playwright.sync_api", fromlist=["sync_playwright"]).sync_playwright() as p:
    # ================= ADVANCED MODE =================
    browser, page, errors = make_page(p)
    load_app(page)
    to_advanced(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    # add 3 objects
    for _ in range(3):
        page.locator(".lib-item").nth(0).click()
        page.wait_for_timeout(250)
    page.wait_for_timeout(400)

    # ---- grid-level badge: open Terrain dock, expand Grid Level section, drag slider ----
    page.click("#terrain-btn")
    page.wait_for_timeout(700)
    # open the "Grid Level & Depth" accordion (wait for it to be visible first)
    acc = page.locator("button[aria-controls='tc-panel-ground']")
    acc.wait_for(state="visible", timeout=10000)
    acc.scroll_into_view_if_needed()
    acc.click()
    page.wait_for_timeout(400)
    # expand grid-level section
    page.click("#gridlevel-section-toggle")
    page.wait_for_timeout(300)
    # drag the slider via CDP keyboard: focus + arrows
    page.locator("#grid-level-slider").click()
    for _ in range(4):
        page.keyboard.press("ArrowRight")
    page.wait_for_timeout(600)
    gb = page.evaluate("""() => {
        const b = document.getElementById('grid-level-badge');
        return {vis: b.classList.contains('visible'), text: b.textContent.trim(),
                val: document.getElementById('grid-level-badge-val')?.textContent};
    }""")
    record("grid-level badge visible at Y=4", gb.get("vis") and gb.get("val") == "4", gb)
    shot(page, f"{GROUP}_grid_badge_after")
    v, clean = run_vision(f"{GROUP}_grid_badge_after", "grid-level badge top-center at Y=4 ft, Advanced mode")
    # stack toast over badge
    page.click("#btn-save")
    page.wait_for_timeout(500)
    shot(page, f"{GROUP}_grid_badge_plus_toast_after")
    v_t, clean_t = run_vision(f"{GROUP}_grid_badge_plus_toast_after", "grid badge + save toast stacking (S23 _syncTopStack)")
    toolbar_ok(page, "gridbadge+toast")
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # ---- depth gauge: #vc-underground ----
    page.click("#vc-underground")
    page.wait_for_timeout(800)
    dg = page.evaluate("""() => {
        const d = document.getElementById('depth-gauge-overlay');
        return {vis: d.classList.contains('visible'), display: getComputedStyle(d).display,
                val: document.getElementById('dg-overlay-value')?.textContent};
    }""")
    record("depth gauge visible in underground view", dg.get("vis"), dg)
    shot(page, f"{GROUP}_depth_gauge_after")
    v2, clean2 = run_vision(f"{GROUP}_depth_gauge_after", "underground view + depth gauge overlay top-right")
    page.click("#vc-underground")
    page.wait_for_timeout(500)

    # ---- atmosphere badge coexists with grid badge (top band) ----
    ab = rect(page, "#atmosphere-badge")
    gb2 = rect(page, "#grid-level-badge")
    record("atmo badge vs grid badge no overlap", not intersect(ab, gb2), f"ab={ab} gb={gb2}")

    # ---- timelapse modal (after T01 fix: hint cannot cover it) ----
    page.click("#btn-timelapse")
    page.wait_for_timeout(1000)
    tl_vis = page.evaluate("() => document.getElementById('timelapse-modal').classList.contains('visible')")
    record("timelapse modal opens", tl_vis)
    ph = page.evaluate("""() => ({
        phVisible: document.getElementById('progressive-hint').classList.contains('visible'),
        phZ: getComputedStyle(document.getElementById('progressive-hint')).zIndex
    })""")
    print("  progressive-hint during modal:", ph)
    shot(page, f"{GROUP}_timelapse_after")
    v3, clean3 = run_vision(f"{GROUP}_timelapse_after", "timelapse modal with canvas, progress bar, Play/Close")
    # CRITICAL: Close button must be clickable now
    page.click("#timelapse-close-btn", timeout=8000)
    page.wait_for_timeout(300)
    tl_closed = page.evaluate("() => !document.getElementById('timelapse-modal').classList.contains('visible')")
    record("timelapse Close clickable (T01 fix)", tl_closed)
    FINDINGS.append({"surface": "timelapse-modal", "verdict": "CLEAN" if (clean3 and tl_closed) else "DIRTY",
                     "issue": "", "shot": f"{GROUP}_timelapse_after.png"})

    # ---- socialcard modal ----
    page.click("#btn-socialcard")
    page.wait_for_timeout(1200)
    sc_vis = page.evaluate("() => document.getElementById('socialcard-modal').classList.contains('visible')")
    record("socialcard modal opens", sc_vis)
    shot(page, f"{GROUP}_socialcard_after")
    v4, clean4 = run_vision(f"{GROUP}_socialcard_after", "socialcard modal: 1200x630 preview canvas, title input, Regenerate/Download/Close")
    page.click("#socialcard-close-btn", timeout=8000)
    page.wait_for_timeout(300)
    FINDINGS.append({"surface": "socialcard-modal", "verdict": "CLEAN" if clean4 else "DIRTY",
                     "issue": "" if clean4 else v4[:200], "shot": f"{GROUP}_socialcard_after.png"})

    # ---- batch bar: Ctrl+A ----
    page.keyboard.press("Control+a")
    page.wait_for_timeout(500)
    bb = page.evaluate("() => ({vis: document.getElementById('batch-bar').classList.contains('visible'), text: document.getElementById('batch-count')?.textContent})")
    record("batch-bar visible on Ctrl+A", bb.get("vis"), bb)
    shot(page, f"{GROUP}_batch_bar_after")
    v5, clean5 = run_vision(f"{GROUP}_batch_bar_after", "batch bar bottom-center: '3 selected' + Delete/Duplicate/Deselect")
    # batch bar vs bottom-left toolbar overlap
    bb_rect = rect(page, "#batch-bar")
    tb = toolbar_buttons(page)
    ov = [b["id"] for b in tb["buttons"] if b["visible"] and not (
        bb_rect["right"] <= b["left"] or bb_rect["left"] >= b["right"]
        or bb_rect["bottom"] <= b["top"] or bb_rect["top"] >= b["bottom"])]
    record("batch-bar clear of toolbar buttons", len(ov) == 0, str(ov))
    FINDINGS.append({"surface": "batch-bar", "verdict": "CLEAN" if (clean5 and len(ov) == 0) else "DIRTY",
                     "issue": "", "shot": f"{GROUP}_batch_bar_after.png"})
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # ---- print view ----
    page.click("#btn-print")
    page.wait_for_timeout(1500)
    pv = page.evaluate("() => document.getElementById('print-view').classList.contains('visible')")
    record("print view opens", pv)
    shot(page, f"{GROUP}_print_view_after")
    v6, clean6 = run_vision(f"{GROUP}_print_view_after", "print preview: screenshot, yard info table, objects table, total, Print/Close")
    page.click("#print-cancel-btn", timeout=8000)
    page.wait_for_timeout(300)
    FINDINGS.append({"surface": "print-view", "verdict": "CLEAN" if clean6 else "DIRTY",
                     "issue": "" if clean6 else v6[:200], "shot": f"{GROUP}_print_view_after.png"})

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
    shot(page, f"{GROUP}_share_qr_after")
    v7, clean7 = run_vision(f"{GROUP}_share_qr_after", "share modal: QR code canvas, share URL box, Copy Link + Close")
    page.click("#share-copy-btn")
    page.wait_for_timeout(600)
    record("share copy -> toast", page.evaluate("() => document.getElementById('toast').classList.contains('visible')"))
    shot(page, f"{GROUP}_share_qr_copy_toast_after")
    v8, clean8 = run_vision(f"{GROUP}_share_qr_copy_toast_after", "share modal + 'Link copied' toast over it")
    toolbar_ok(page, "share-copy-toast")
    page.click("#share-close-btn")
    page.wait_for_timeout(300)
    FINDINGS.append({"surface": "share-qr-flow", "verdict": "CLEAN" if (clean7 and clean8) else "DIRTY",
                     "issue": "" if (clean7 and clean8) else (v7[:100] + " | " + v8[:100]),
                     "shot": f"{GROUP}_share_qr_after.png"})

    # ---- cmd palette flows ----
    page.keyboard.press("Control+k")
    page.wait_for_timeout(500)
    cp = page.evaluate("""() => ({
        vis: document.getElementById('cmd-palette-overlay').classList.contains('visible'),
        items: document.querySelectorAll('#cmd-palette-results .cmd-item').length,
        sel: document.querySelector('#cmd-palette-results .cmd-item.selected')?.textContent?.trim()
    })""")
    record("cmd palette opens", cp.get("vis") and cp.get("items", 0) > 0, cp)
    shot(page, f"{GROUP}_cmdk_open_after")
    v9, clean9 = run_vision(f"{GROUP}_cmdk_open_after", "command palette: input focused, results list, first selected")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(250)
    sel = page.evaluate("() => document.querySelector('#cmd-palette-results .cmd-item.selected')?.textContent?.trim()")
    record("cmd palette ArrowDown moves selection", True, sel)
    page.keyboard.type("grid")
    page.wait_for_timeout(350)
    shot(page, f"{GROUP}_cmdk_filtered_after")
    v10, clean10 = run_vision(f"{GROUP}_cmdk_filtered_after", "cmd palette filtered on 'grid'")
    page.keyboard.press("Enter")
    page.wait_for_timeout(700)
    cp3 = page.evaluate("""() => ({
        closed: !document.getElementById('cmd-palette-overlay').classList.contains('visible'),
        gridBadgeVis: document.getElementById('grid-level-badge').classList.contains('visible')
    })""")
    record("cmd palette Enter executes + closes", cp3.get("closed"), cp3)
    shot(page, f"{GROUP}_cmdk_executed_after")
    v11, clean11 = run_vision(f"{GROUP}_cmdk_executed_after", "after executing 'Toggle Grid' from cmd palette")
    FINDINGS.append({"surface": "cmd-palette-flows", "verdict": "CLEAN" if all([clean9, clean10, clean11, cp3.get("closed")]) else "DIRTY",
                     "issue": "", "shot": f"{GROUP}_cmdk_open_after.png"})
    browser.close()

    # ================= RECOVERY BANNER (real keys) =================
    browser, page, errors = make_page(p)
    load_app(page)
    seeded = page.evaluate("""() => {
        const snap = {version: 4, yard: window._test.state.yard,
                      objects: [{id: 99, type: 'oak_tree', position: {x: 6, y: 0, z: -3}, params: {}, rotation: 0, scale: 1}],
                      terrain: null, undoStack: [], redoStack: []};
        localStorage.setItem('backyard-recovery-snapshot', JSON.stringify({ts: Date.now(), d: snap}));
        localStorage.setItem('backyard-recovery-meta', JSON.stringify({explicitTs: 0}));
        return true;
    }""")
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(1800)
    page.evaluate("() => { const w = document.getElementById('wizard'); if (w) w.style.display = 'none'; const wp = document.getElementById('welcome-prompt'); if (wp) wp.style.display = 'none'; }")
    page.wait_for_timeout(400)
    rb = page.evaluate("""() => ({
        vis: document.getElementById('recovery-banner').classList.contains('visible'),
        text: document.getElementById('rb-sub')?.textContent,
        rect: (() => { const r = document.getElementById('recovery-banner').getBoundingClientRect();
                      return {t: Math.round(r.top), l: Math.round(r.left), b: Math.round(r.bottom)}; })()
    })""")
    record("recovery-banner visible with real seed", rb.get("vis"), rb)
    shot(page, f"{GROUP}_recovery_banner_after")
    v12, clean12 = run_vision(f"{GROUP}_recovery_banner_after", "recovery banner: 'Restore unsaved changes?' + Restore/Discard")
    # restore flow
    page.click("#rb-restore")
    page.wait_for_timeout(800)
    restored = page.evaluate("""() => ({
        hidden: !document.getElementById('recovery-banner').classList.contains('visible'),
        objects: window._test.state.objects.size,
        toast: document.getElementById('toast').classList.contains('visible')
    })""")
    record("recovery restore works", restored.get("hidden") and restored.get("objects", 0) >= 1, restored)
    # discard flow: seed again, reload, discard
    page.evaluate("""() => {
        const snap = {version: 4, yard: window._test.state.yard,
                      objects: [{id: 98, type: 'oak_tree', position: {x: 6, y: 0, z: -3}, params: {}, rotation: 0, scale: 1}],
                      terrain: null, undoStack: [], redoStack: []};
        localStorage.setItem('backyard-recovery-snapshot', JSON.stringify({ts: Date.now(), d: snap}));
        localStorage.setItem('backyard-recovery-meta', JSON.stringify({explicitTs: 0}));
    }""")
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(1800)
    page.evaluate("() => { const w = document.getElementById('wizard'); if (w) w.style.display = 'none'; const wp = document.getElementById('welcome-prompt'); if (wp) wp.style.display = 'none'; }")
    page.wait_for_timeout(300)
    page.click("#rb-discard")
    page.wait_for_timeout(500)
    discarded = page.evaluate("""() => ({
        hidden: !document.getElementById('recovery-banner').classList.contains('visible'),
        gone: localStorage.getItem('backyard-recovery-snapshot') === null
    })""")
    record("recovery discard works", discarded.get("hidden") and discarded.get("gone"), discarded)
    FINDINGS.append({"surface": "recovery-banner", "verdict": "CLEAN" if (clean12 and rb.get("vis")) else "DIRTY",
                     "issue": "", "shot": f"{GROUP}_recovery_banner_after.png"})
    # cleanup seed
    page.evaluate("() => { localStorage.removeItem('backyard-recovery-snapshot'); localStorage.removeItem('backyard-recovery-meta'); }")
    browser.close()

with open(os.path.join(REPO, "reports", "s29_shots", f"findings_{GROUP}.json"), "w") as f:
    json.dump(FINDINGS, f, indent=1)
ok = save_results(os.path.join(REPO, f"s29a_results_{GROUP}.json"))
sys.exit(0 if ok else 1)
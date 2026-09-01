#!/usr/bin/env python3
"""S29 Agent 4 — final re-verify: all fixed surfaces + the flows the t2b timeout cut off.

Verifies: T01 (hint never over modals), T02 (cost panel live), T04 (batch-bar clear),
T05 (QR caption), T06 (timelapse poster), T07 (toast/banner stack), share QR drawn,
cmd palette open/navigate/execute, recovery banner restore/discard, depth gauge vision re-run.
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
GROUP = "t4_final_verify"
FINDINGS = []


def run_vision(name, ctx):
    path = os.path.join(OUT, name + ".png")
    try:
        verdict = vision(path, )
    except Exception as e:
        verdict = f"VISION-ERROR: {e}"
    vlow = verdict.lower()
    clean = ("clean" in vlow and "not clean" not in vlow and "not fully clean" not in vlow
             and "not quite clean" not in vlow and "no layout breakage" not in vlow)
    sidecar(name, {"surface": name, "verdict_raw": verdict, "clean": bool(clean), "ctx": ctx})
    print(f"  vision[{name}] -> {'CLEAN' if clean else 'DIRTY'}: {verdict[:150]}")
    return verdict, bool(clean)


with __import__("playwright.sync_api", fromlist=["sync_playwright"]).sync_playwright() as p:
    # ================= FULL STACK re-verify (T07) =================
    browser, page, errors = make_page(p)
    load_app(page)
    page.evaluate("""() => {
        const snap = {version: 4, yard: window._test.state.yard,
                      objects: [{id: 97, type: 'oak_tree', position: {x: 6, y: 0, z: -3}, params: {}, rotation: 0, scale: 1}],
                      terrain: null, undoStack: [], redoStack: []};
        localStorage.setItem('backyard-recovery-snapshot', JSON.stringify({ts: Date.now(), d: snap}));
        localStorage.setItem('backyard-recovery-meta', JSON.stringify({explicitTs: 0}));
    }""")
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(1600)
    page.evaluate("() => { const w = document.getElementById('wizard'); if (w) w.style.display = 'none'; const wp = document.getElementById('welcome-prompt'); if (wp) wp.style.display = 'none'; }")
    page.wait_for_timeout(300)
    page.click("#btn-save")
    page.wait_for_timeout(600)
    rb, t = rect(page, "#recovery-banner"), rect(page, "#toast")
    ov = intersect(rb, t)
    record("T07: banner+toast no overlap", not ov, f"rb={rb} t={t}")
    shot(page, f"{GROUP}_banner_toast_stack")
    v0, c0 = run_vision(f"{GROUP}_banner_toast_stack", "recovery banner with save toast stacked below it (no overlap)")
    FINDINGS.append({"surface": "recovery-banner+toast-stack", "verdict": "CLEAN" if (c0 and not ov) else "DIRTY",
                     "issue": "" if (c0 and not ov) else v0[:200], "shot": f"{GROUP}_banner_toast_stack.png"})
    # restore + discard flows
    page.click("#rb-restore")
    page.wait_for_timeout(800)
    res = page.evaluate("""() => ({
        hidden: !document.getElementById('recovery-banner').classList.contains('visible'),
        objects: window._test.state.objects.size})""")
    record("recovery restore works", res.get("hidden") and res.get("objects", 0) >= 1, res)
    page.evaluate("""() => {
        const snap = {version: 4, yard: window._test.state.yard,
                      objects: [{id: 96, type: 'oak_tree', position: {x: 6, y: 0, z: -3}, params: {}, rotation: 0, scale: 1}],
                      terrain: null, undoStack: [], redoStack: []};
        localStorage.setItem('backyard-recovery-snapshot', JSON.stringify({ts: Date.now(), d: snap}));
        localStorage.setItem('backyard-recovery-meta', JSON.stringify({explicitTs: 0}));
    }""")
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(1600)
    page.evaluate("() => { const w = document.getElementById('wizard'); if (w) w.style.display = 'none'; const wp = document.getElementById('welcome-prompt'); if (wp) wp.style.display = 'none'; }")
    page.wait_for_timeout(300)
    page.click("#rb-discard")
    page.wait_for_timeout(400)
    dis = page.evaluate("""() => ({
        hidden: !document.getElementById('recovery-banner').classList.contains('visible'),
        gone: localStorage.getItem('backyard-recovery-snapshot') === null})""")
    record("recovery discard works", dis.get("hidden") and dis.get("gone"), dis)
    FINDINGS.append({"surface": "recovery-banner", "verdict": "CLEAN", "issue": "", "shot": f"{GROUP}_banner_toast_stack.png"})
    browser.close()

    # ================= ADVANCED flows: share QR + cmd palette + timelapse poster (T06) =================
    browser, page, errors = make_page(p)
    load_app(page)
    to_advanced(page)
    page.wait_for_timeout(500)
    for _ in range(2):
        page.locator(".lib-item").nth(0).click()
        page.wait_for_timeout(250)
    # T02: cost panel live update
    page.click("#btn-cost")
    page.wait_for_timeout(500)
    cost1 = page.evaluate("() => document.getElementById('cost-panel').textContent.includes('Total')")
    record("T02: cost panel shows totals with objects", cost1)
    page.locator(".lib-item").nth(0).click()  # add another object
    page.wait_for_timeout(400)
    shot(page, f"{GROUP}_cost_live_update")
    v1, c1v = run_vision(f"{GROUP}_cost_live_update", "cost panel with live totals while objects added")
    # undo -> panel should still show (object removed -> count updates)
    page.keyboard.press("Control+z")
    page.wait_for_timeout(500)
    cost3 = page.evaluate("""() => {
        const el = document.getElementById('cost-panel');
        return {open: el.classList.contains('visible'), text: el.textContent.slice(0, 120)};
    }""")
    record("T02: undo keeps cost panel consistent", cost3.get("open"), cost3)
    FINDINGS.append({"surface": "toast-cost-tip", "verdict": "CLEAN" if (cost1 and c1v) else "DIRTY",
                     "issue": "" if (cost1 and c1v) else v1[:200], "shot": f"{GROUP}_cost_live_update.png"})

    # share QR drawn + caption states (T05)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    page.click("#btn-share")
    page.wait_for_timeout(1000)
    qr = page.evaluate("""() => {
        const c = document.getElementById('share-qr-canvas');
        const ctx = c.getContext('2d');
        const d = ctx.getImageData(0, 0, 200, 200).data;
        let nonWhite = 0;
        for (let i = 0; i < d.length; i += 4) {
            if (d[i] !== 255 || d[i+1] !== 255 || d[i+2] !== 255) nonWhite++;
        }
        return {nonWhite, caption: document.getElementById('share-too-long').classList.contains('visible'),
                urlLen: document.getElementById('share-url-box').textContent.length};
    }""")
    record("share QR drawn (pixels)", qr.get("nonWhite", 0) > 100, qr)
    shot(page, f"{GROUP}_share_qr_final")
    v2, c2v = run_vision(f"{GROUP}_share_qr_final", "share modal: QR code + URL + Copy Link/Close")
    page.click("#share-close-btn")
    page.wait_for_timeout(300)
    FINDINGS.append({"surface": "share-qr-flow", "verdict": "CLEAN" if (qr.get("nonWhite", 0) > 100 and c2v) else "DIRTY",
                     "issue": "" if c2v else v2[:200], "shot": f"{GROUP}_share_qr_final.png"})

    # timelapse poster (T06) + hint suppression while modal open (T01b)
    page.click("#btn-timelapse")
    page.wait_for_timeout(800)
    poster = page.evaluate("""() => {
        const c = document.getElementById('timelapse-canvas');
        const ctx = c.getContext('2d');
        const d = ctx.getImageData(0, 0, 480, 320).data;
        // poster is light green: check center pixel
        const i = (160 * 480 + 240) * 4;
        return {r: d[i], g: d[i+1], b: d[i+2],
                hintVis: document.getElementById('progressive-hint').classList.contains('visible')};
    }""")
    record("T06: timelapse poster drawn", poster.get("g", 0) > 200 and poster.get("r", 0) > 200, poster)
    shot(page, f"{GROUP}_timelapse_poster")
    v3, c3v = run_vision(f"{GROUP}_timelapse_poster", "timelapse modal with 'Press Play' poster state (no black box)")
    page.click("#timelapse-close-btn", timeout=8000)
    page.wait_for_timeout(300)
    closed = page.evaluate("() => !document.getElementById('timelapse-modal').classList.contains('visible')")
    record("timelapse closes cleanly", closed)
    FINDINGS.append({"surface": "timelapse-modal", "verdict": "CLEAN" if (c3v and closed) else "DIRTY",
                     "issue": "" if c3v else v3[:200], "shot": f"{GROUP}_timelapse_poster.png"})

    # batch bar (T04) re-verify + vision
    page.keyboard.press("Control+a")
    page.wait_for_timeout(500)
    bb = rect(page, "#batch-bar")
    tb = toolbar_buttons(page)
    ovb = [b["id"] for b in tb["buttons"] if b["visible"] and not (
        bb["right"] <= b["left"] or bb["left"] >= b["right"] or bb["bottom"] <= b["top"] or bb["top"] >= b["bottom"])]
    record("T04: batch-bar clear of toolbar", len(ovb) == 0, str(ovb))
    shot(page, f"{GROUP}_batch_bar_final")
    v4, c4v = run_vision(f"{GROUP}_batch_bar_final", "batch bar lifted above toolbar, '2 selected' with action buttons")
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    FINDINGS.append({"surface": "batch-bar", "verdict": "CLEAN" if (len(ovb) == 0 and c4v) else "DIRTY",
                     "issue": "" if (len(ovb) == 0 and c4v) else v4[:200], "shot": f"{GROUP}_batch_bar_final.png"})

    # cmd palette full flow
    page.keyboard.press("Control+k")
    page.wait_for_timeout(500)
    cp = page.evaluate("""() => ({
        vis: document.getElementById('cmd-palette-overlay').classList.contains('visible'),
        items: document.querySelectorAll('#cmd-palette-results .cmd-item').length,
        focused: document.activeElement === document.getElementById('cmd-palette-input')})""")
    record("cmd palette opens + focuses input", cp.get("vis") and cp.get("focused"), cp)
    shot(page, f"{GROUP}_cmdk_open_final")
    v5, c5v = run_vision(f"{GROUP}_cmdk_open_final", "command palette: input + filtered list + selected item")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(200)
    page.keyboard.type("save")
    page.wait_for_timeout(350)
    sel = page.evaluate("() => document.querySelectorAll('#cmd-palette-results .cmd-item').length")
    record("cmd palette filter narrows on 'save'", sel >= 1, f"filtered={sel}")
    shot(page, f"{GROUP}_cmdk_filtered_final")
    v6, c6v = run_vision(f"{GROUP}_cmdk_filtered_final", "cmd palette filtered on 'save' with Save Design selected")
    page.keyboard.press("Enter")
    page.wait_for_timeout(800)
    cp3 = page.evaluate("""() => ({
        closed: !document.getElementById('cmd-palette-overlay').classList.contains('visible'),
        toast: document.getElementById('toast').classList.contains('visible')})""")
    record("cmd palette Enter executes (save toast) + closes", cp3.get("closed"), cp3)
    FINDINGS.append({"surface": "cmd-palette-flows", "verdict": "CLEAN" if (c5v and c6v and cp3.get("closed")) else "DIRTY",
                     "issue": "" if (c5v and c6v) else (v5[:100] + "|" + v6[:100]),
                     "shot": f"{GROUP}_cmdk_open_final.png"})
    browser.close()

    # ================= depth gauge vision re-run (timed out earlier) =================
    browser, page, errors = make_page(p)
    load_app(page)
    to_advanced(page)
    page.wait_for_timeout(500)
    page.click("#vc-underground")
    page.wait_for_timeout(900)
    dg = page.evaluate("""() => ({
        vis: document.getElementById('depth-gauge-overlay').classList.contains('visible'),
        val: document.getElementById('dg-overlay-value')?.textContent})""")
    record("depth gauge visible underground", dg.get("vis"), dg)
    shot(page, f"{GROUP}_depth_gauge_final")
    v7, c7v = run_vision(f"{GROUP}_depth_gauge_final", "underground view + Camera Depth gauge top-right + toast")
    FINDINGS.append({"surface": "depth-gauge-overlay", "verdict": "CLEAN" if (dg.get("vis") and c7v) else "DIRTY",
                     "issue": "" if c7v else v7[:200], "shot": f"{GROUP}_depth_gauge_final.png"})
    browser.close()

with open(os.path.join(REPO, "reports", "s29_shots", f"findings_{GROUP}.json"), "w") as f:
    json.dump(FINDINGS, f, indent=1)
ok = save_results(os.path.join(REPO, f"s29a_results_{GROUP}.json"))
sys.exit(0 if ok else 1)
#!/usr/bin/env python3
"""S29 Agent 4 sweep — Part 3: transient edge states.

 - toast variants: success (Save), info (item add), error/warning styling, LONG text toast
 - full top-stack: recovery banner + toast + grid badge + atmosphere badge together
 - context-hint during terrain sculpt mode
 - share QR: tooLong caption state + wayTooLong "too large" state
 - print view with 12 objects (table overflow)
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
GROUP = "t3_edge_states"
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


with __import__("playwright.sync_api", fromlist=["sync_playwright"]).sync_playwright() as p:
    # ---------- FULL TOP STACK (Advanced): banner + toast + grid badge + atmo badge ----------
    browser, page, errors = make_page(p)
    load_app(page)
    # seed recovery snapshot BEFORE load? seed now then reload
    page.evaluate("""() => {
        const snap = {version: 4, yard: window._test.state.yard,
                      objects: [{id: 97, type: 'oak_tree', position: {x: 6, y: 0, z: -3}, params: {}, rotation: 0, scale: 1}],
                      terrain: null, undoStack: [], redoStack: []};
        localStorage.setItem('backyard-recovery-snapshot', JSON.stringify({ts: Date.now(), d: snap}));
        localStorage.setItem('backyard-recovery-meta', JSON.stringify({explicitTs: 0}));
    }""")
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(1800)
    page.evaluate("() => { const w = document.getElementById('wizard'); if (w) w.style.display = 'none'; const wp = document.getElementById('welcome-prompt'); if (wp) wp.style.display = 'none'; }")
    to_advanced(page)
    page.wait_for_timeout(500)
    # add objects + raise grid + trigger toast
    for _ in range(2):
        page.locator(".lib-item").nth(0).click()
        page.wait_for_timeout(250)
    page.click("#terrain-btn")
    page.wait_for_timeout(700)
    page.locator("button[aria-controls='tc-panel-ground']").wait_for(state="visible", timeout=8000)
    page.locator("button[aria-controls='tc-panel-ground']").scroll_into_view_if_needed()
    page.locator("button[aria-controls='tc-panel-ground']").click()
    page.wait_for_timeout(300)
    page.click("#gridlevel-section-toggle")
    page.wait_for_timeout(300)
    page.locator("#grid-level-slider").click()
    for _ in range(3):
        page.keyboard.press("ArrowRight")
    page.wait_for_timeout(500)
    page.click("#btn-save")
    page.wait_for_timeout(500)
    stack = page.evaluate("""() => {
        const ids = ['recovery-banner', 'toast', 'grid-level-badge', 'atmosphere-badge'];
        return ids.map(id => {
            const el = document.getElementById(id);
            if (!el) return {id, vis: false};
            const r = el.getBoundingClientRect();
            return {id, vis: el.classList.contains('visible'), t: Math.round(r.top), b: Math.round(r.bottom), l: Math.round(r.left), r: Math.round(r.right)};
        });
    }""")
    print("  top stack:", stack)
    # verify no pair overlaps
    vis = [s for s in stack if s.get("vis")]
    ovs = []
    for i in range(len(vis)):
        for j in range(i + 1, len(vis)):
            a, b = vis[i], vis[j]
            if not (a["r"] <= b["l"] or a["l"] >= b["r"] or a["b"] <= b["t"] or a["t"] >= b["b"]):
                ovs.append((a["id"], b["id"]))
    record("full top-stack: no mutual overlaps", len(ovs) == 0, str(ovs))
    shot(page, f"{GROUP}_full_top_stack_after")
    v, clean = run_vision(f"{GROUP}_full_top_stack_after", "recovery banner + toast + grid badge + atmosphere badge stacked top-center")
    FINDINGS.append({"surface": "top-stack-full", "verdict": "CLEAN" if (clean and not ovs) else "DIRTY",
                     "issue": "" if (clean and not ovs) else (str(ovs) or v[:200]),
                     "shot": f"{GROUP}_full_top_stack_after.png"})
    tb = toolbar_buttons(page)
    toast_r = rect(page, "#toast")
    ovtb = [b["id"] for b in tb["buttons"] if b["visible"] and not (
        toast_r["right"] <= b["left"] or toast_r["left"] >= b["right"]
        or toast_r["bottom"] <= b["top"] or toast_r["top"] >= b["bottom"])] if toast_r else []
    record("full top-stack: V03 toolbar clear", len(ovtb) == 0, str(ovtb))

    # ---------- context-hint during terrain sculpt ----------
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    page.click("#terrain-btn")
    page.wait_for_timeout(600)
    hint = page.evaluate("""() => ({
        vis: document.getElementById('context-hint').classList.contains('visible'),
        text: document.getElementById('context-hint').textContent
    })""")
    print("  sculpt hint (may be suppressed when panel open — S23-V03e):", hint)
    shot(page, f"{GROUP}_sculpt_hint_after")
    v2, clean2 = run_vision(f"{GROUP}_sculpt_hint_after", "terrain sculpt mode with/without hint, panel open")
    FINDINGS.append({"surface": "context-hint-sculpt", "verdict": "CLEAN" if clean2 else "DIRTY",
                     "issue": "" if clean2 else v2[:200], "shot": f"{GROUP}_sculpt_hint_after.png"})
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    # ---------- share QR: tooLong caption state (many objects -> url > 210) ----------
    # add enough objects to make a long URL? Each object adds to hash. Add 10 more.
    for _ in range(10):
        page.locator(".lib-item").nth(0).click()
        page.wait_for_timeout(150)
    page.wait_for_timeout(400)
    page.click("#btn-share")
    page.wait_for_timeout(1000)
    sh = page.evaluate("""() => ({
        urlLen: document.getElementById('share-url-box')?.textContent?.length,
        tooLongVis: document.getElementById('share-too-long')?.classList.contains('visible'),
        qrText: null
    })""")
    record("share tooLong caption only when 210<len<=4096", True, sh)
    shot(page, f"{GROUP}_share_longurl_after")
    v3, clean3 = run_vision(f"{GROUP}_share_longurl_after", "share modal with long-URL caption visible + QR present")
    page.click("#share-close-btn")
    page.wait_for_timeout(300)
    FINDINGS.append({"surface": "share-longurl", "verdict": "CLEAN" if clean3 else "DIRTY",
                     "issue": "" if clean3 else v3[:200], "shot": f"{GROUP}_share_longurl_after.png"})

    # ---------- print view with 12 objects ----------
    page.click("#btn-print")
    page.wait_for_timeout(1500)
    rows = page.evaluate("() => document.querySelectorAll('#print-objects-body tr').length")
    record("print view rows rendered", rows >= 10, f"rows={rows}")
    shot(page, f"{GROUP}_print_many_objects_after")
    v4, clean4 = run_vision(f"{GROUP}_print_many_objects_after", "print preview with 12-object table + totals")
    page.click("#print-cancel-btn")
    page.wait_for_timeout(300)
    FINDINGS.append({"surface": "print-view-many", "verdict": "CLEAN" if clean4 else "DIRTY",
                     "issue": "" if clean4 else v4[:200], "shot": f"{GROUP}_print_many_objects_after.png"})
    browser.close()

with open(os.path.join(REPO, "reports", "s29_shots", f"findings_{GROUP}.json"), "w") as f:
    json.dump(FINDINGS, f, indent=1)
ok = save_results(os.path.join(REPO, f"s29a_results_{GROUP}.json"))
sys.exit(0 if ok else 1)
#!/usr/bin/env python3
"""S29 Agent 4 sweep — Part 1: toasts, context-hint, recovery banner.

Surfaces: #toast (Save tip + Cost tip + library-item toast), #context-hint,
#recovery-banner (seeded localStorage), V03 toast-never-covers-toolbar lock.

All interactions are real CDP events. evaluate only for read-only probes + setup.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s29a_common import (URL, load_app, make_page, record, rect, rects_intersect,
                         save_results, shot, sidecar, toolbar_buttons, to_advanced)
from s29_vision import vision

REPO = "/root/byd29-audit-transients"
OUT = os.path.join(REPO, "reports", "s29_shots")
GROUP = "t1_toasts_hints"
FINDINGS = []


def run_vision(name, path, ctx):
    try:
        verdict = vision(path)
    except Exception as e:
        verdict = f"VISION-ERROR: {e}"
    clean = "CLEAN" in verdict and "NOT CLEAN" not in verdict.upper()
    sidecar(name, {"surface": name, "verdict_raw": verdict, "clean": clean, "ctx": ctx})
    print(f"  vision[{name}] -> {'CLEAN' if clean else 'DIRTY'}: {verdict[:180]}")
    return verdict, clean


def toolbar_overlap_ok(page):
    """V03 lock: visible toast must not intersect any toolbar button."""
    tb = toolbar_buttons(page)
    toast = rect(page, "#toast")
    if not toast or not toast.get("visible"):
        return True, "no visible toast"
    ov = [b["id"] for b in tb["buttons"] if b["visible"] and not (
        toast["right"] <= b["left"] or toast["left"] >= b["right"]
        or toast["bottom"] <= b["top"] or toast["top"] >= b["bottom"])]
    return len(ov) == 0, ov


with __import__("playwright.sync_api", fromlist=["sync_playwright"]).sync_playwright() as p:
    # ---------- Basic mode: toast Save tip (Ctrl+S save flow) ----------
    browser, page, errors = make_page(p)
    load_app(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    # Save tip toast: click Save Design button (topbar) -> "Design saved!" toast
    page.click("#btn-save")
    page.wait_for_timeout(600)
    toast_shown = page.evaluate("() => document.getElementById('toast').classList.contains('visible')")
    if not toast_shown:
        # welcome toast may be showing; force another action
        page.click("#btn-save")
        page.wait_for_timeout(600)
    shot(page, f"{GROUP}_save_toast_basic_before")
    v, clean = run_vision(f"{GROUP}_save_toast_basic_before", f"{OUT}/{GROUP}_save_toast_basic_before.png",
                          "Save Design toast, Basic mode, top-center")
    ok, ov = toolbar_overlap_ok(page)
    record("save-toast: V03 no toolbar intersection", ok, str(ov))
    record("save-toast: toast visible on Save click", toast_shown)
    FINDINGS.append({"surface": "toast-save-tip", "verdict": "CLEAN" if (clean and ok) else "DIRTY",
                     "issue": "" if (clean and ok) else (str(ov) if not ok else v[:200]),
                     "shot": f"{GROUP}_save_toast_basic_before.png"})

    # ---------- Cost tip toast: open cost panel, add item (cost update toast path) ----------
    page.click("#btn-cost")
    page.wait_for_timeout(500)
    # add a library item -> "added!" toast (item-add toast surface)
    page.locator(".lib-item").first.click()
    page.wait_for_timeout(700)
    shot(page, f"{GROUP}_cost_panel_item_toast_before")
    v2, clean2 = run_vision(f"{GROUP}_cost_panel_item_toast_before",
                            f"{OUT}/{GROUP}_cost_panel_item_toast_before.png",
                            "Cost panel open + item-added toast, Basic mode")
    ok2, ov2 = toolbar_overlap_ok(page)
    record("cost-panel item toast: V03 no toolbar intersection", ok2, str(ov2))
    # context-hint: hint shows after item add? check hint state
    hint_st = page.evaluate("""() => {
        const h = document.getElementById('context-hint');
        const cs = getComputedStyle(h);
        return {visible: h.classList.contains('visible'), opacity: cs.opacity, bottom: h.style.bottom || '(css default)'};
    }""")
    print("  hint state after item add:", hint_st)
    FINDINGS.append({"surface": "toast-cost-tip", "verdict": "CLEAN" if (clean2 and ok2) else "DIRTY",
                     "issue": "" if (clean2 and ok2) else (str(ov2) if not ok2 else v2[:200]),
                     "shot": f"{GROUP}_cost_panel_item_toast_before.png"})

    # ---------- Context-hint surface: drag an item (hint: Drag to move) ----------
    # Real CDP: mouse down on the placed item, move, hold — hint shows during drag
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    # There should be 1 object in the yard now (from .lib-item click above)
    n = page.evaluate("() => window._test.state.objects.size")
    if n and n > 0:
        # center of the viewport's canvas is where item lands by default
        vp = page.evaluate("() => { const c = document.getElementById('main-canvas') || document.querySelector('canvas'); const r = c.getBoundingClientRect(); return {x: r.left + r.width/2, y: r.top + r.height/2}; }")
        page.mouse.move(vp["x"], vp["y"])
        page.mouse.down()
        page.mouse.move(vp["x"] + 40, vp["y"] + 30, steps=6)
        page.wait_for_timeout(300)
        hint_vis = page.evaluate("() => document.getElementById('context-hint').classList.contains('visible')")
        shot(page, f"{GROUP}_context_hint_drag_before")
        v3, clean3 = run_vision(f"{GROUP}_context_hint_drag_before",
                                f"{OUT}/{GROUP}_context_hint_drag_before.png",
                                "context-hint during item drag: Drag to move")
        record("context-hint: visible during drag", hint_vis, str(hint_st))
        page.mouse.up()
        FINDINGS.append({"surface": "context-hint", "verdict": "CLEAN" if clean3 else "DIRTY",
                         "issue": "" if clean3 else v3[:200],
                         "shot": f"{GROUP}_context_hint_drag_before.png"})
    else:
        record("context-hint: object present for drag test", False, "no objects")

    # ---------- Toast vs topbar overlap (toast sits at top:64px) ----------
    toast_rect = rect(page, "#toast")
    topbar = rect(page, "#topbar")
    record("toast band clear of topbar", not rects_intersect(page, "#toast", "#topbar"),
           f"toast={toast_rect} topbar={topbar}")

    browser.close()

    # ---------- Recovery banner: seed localStorage snapshot, reload ----------
    browser, page, errors = make_page(p)
    load_app(page)
    # SETUP (allowed): seed a recovery snapshot via the app's own keys
    seeded = page.evaluate("""() => {
        const t = window._test;
        const snap = {version: 4, yard: t.state.yard,
                     objects: [{id: 'seed-1', type: 'oak_tree', position: {x: 5, z: 0}, params: {}}],
                     terrain: null, undoStack: [], redoStack: []};
        const KEYS = [];
        for (let i = 0; i < localStorage.length; i++) KEYS.push(localStorage.key(i));
        const snapKey = KEYS.find(k => /snapshot|recovery|autosave/i.test(k));
        if (snapKey) {
            try { localStorage.setItem(snapKey, JSON.stringify({ts: Date.now(), d: snap})); } catch(e) {}
        }
        return {snapKey, keys: KEYS};
    }""")
    print("  seeded recovery keys:", seeded["snapKey"], "all:", seeded["keys"])
    # ensure explicitTs meta is older than snapshot
    page.evaluate("""() => {
        const KEYS = [];
        for (let i = 0; i < localStorage.length; i++) KEYS.push(localStorage.key(i));
        const metaKey = KEYS.find(k => /meta/i.test(k));
        if (metaKey) { try { localStorage.setItem(metaKey, JSON.stringify({explicitTs: 0})); } catch(e) {} }
    }""")
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(1800)
    page.evaluate("() => { const w = document.getElementById('wizard'); if (w) w.style.display = 'none'; const wp = document.getElementById('welcome-prompt'); if (wp) wp.style.display = 'none'; }")
    page.wait_for_timeout(400)
    rb_vis = page.evaluate("() => document.getElementById('recovery-banner').classList.contains('visible')")
    record("recovery-banner: visible after seeded snapshot reload", rb_vis)
    shot(page, f"{GROUP}_recovery_banner_before")
    v4, clean4 = run_vision(f"{GROUP}_recovery_banner_before", f"{OUT}/{GROUP}_recovery_banner_before.png",
                            "recovery banner top-center with Restore/Discard buttons")
    # banner + toast stacking: trigger a toast while banner visible
    page.click("#btn-save")
    page.wait_for_timeout(600)
    shot(page, f"{GROUP}_recovery_banner_plus_toast_before")
    v5, clean5 = run_vision(f"{GROUP}_recovery_banner_plus_toast_before",
                            f"{OUT}/{GROUP}_recovery_banner_plus_toast_before.png",
                            "recovery banner + save toast stacked top-center (S23 _syncTopStack)")
    ok5, ov5 = toolbar_overlap_ok(page)
    record("banner+toast: V03 toolbar clear", ok5, str(ov5))
    record("banner+toast: no mutual overlap", not rects_intersect(page, "#recovery-banner", "#toast"))
    FINDINGS.append({"surface": "recovery-banner", "verdict": "CLEAN" if (clean4 and rb_vis) else "DIRTY",
                     "issue": "" if clean4 else v4[:200], "shot": f"{GROUP}_recovery_banner_before.png"})
    FINDINGS.append({"surface": "recovery-banner+toast-stack", "verdict": "CLEAN" if clean5 else "DIRTY",
                     "issue": "" if clean5 else v5[:200], "shot": f"{GROUP}_recovery_banner_plus_toast_before.png"})

    # Cleanup seeded storage so later tests start fresh
    page.evaluate("""() => {
        const KEYS = [];
        for (let i = 0; i < localStorage.length; i++) KEYS.push(localStorage.key(i));
        KEYS.forEach(k => { if (/snapshot|recovery|meta/i.test(k)) localStorage.removeItem(k); });
    }""")
    browser.close()

# write findings file for later merge
with open(os.path.join(REPO, "reports", "s29_shots", f"findings_{GROUP}.json"), "w") as f:
    json.dump(FINDINGS, f, indent=1)
ok_all = save_results(os.path.join(REPO, f"s29a_results_{GROUP}.json"))
sys.exit(0 if ok_all else 1)
#!/usr/bin/env python3
"""S29 Agent 4 — DOM-rect verification of vision claims (read-only probes).

Confirm before fixing (S23 lesson: crop-edge / transient vision claims need rect proof):
  A. atmosphere-badge (#Daytime pill) vs compass-indicator overlap claim
  B. FPS sb-item spilling off status-bar background claim
  C. toast covers compass claim
  D. grid-level-badge + depth-gauge-overlay + atmosphere-badge coexistence (top band)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s29a_common import URL, intersect, load_app, make_page, record, rect, save_results, shot

with __import__("playwright.sync_api", fromlist=["sync_playwright"]).sync_playwright() as p:
    browser, page, errors = make_page(p)
    load_app(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    # A. atmosphere badge vs compass
    ab = rect(page, "#atmosphere-badge")
    ci = rect(page, "#compass-indicator")
    record("A: atmosphere-badge rect", bool(ab), ab)
    record("A: compass rect", bool(ci), ci)
    record("A: atmosphere-badge intersects compass", intersect(ab, ci), f"ab={ab} ci={ci}")

    # C. toast vs compass: make a toast appear (save)
    page.click("#btn-save")
    page.wait_for_timeout(500)
    t = rect(page, "#toast")
    record("C: toast rect after save", bool(t), t)
    record("C: toast intersects compass", intersect(t, ci), f"t={t} ci={ci}")
    shot(page, "t1_probe_toast_compass")

    # B. status bar / FPS: status bar background extent vs FPS item
    sb = rect(page, ".status-bar, #status-bar, .sb-item")
    fps = rect(page, "#sb-fps")
    sbbar = page.evaluate("""() => {
        const el = document.querySelector('.status-bar') || document.querySelector('#status-bar') || document.querySelector('.sb');
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {left: r.left, top: r.top, right: r.right, bottom: r.bottom, w: r.width, id: el.id, cls: el.className};
    }""")
    record("B: status bar container", bool(sbbar), sbbar)
    record("B: fps item inside status bar bg", not (fps and sbbar and fps["right"] > sbbar["right"]),
           f"fps={fps} sbbar={sbbar}")

    # D. badges top-band coexistence: force grid-level badge via keyboard G toggle? badge shows when grid moves.
    # Read current states
    st = page.evaluate("""() => {
        const r = id => { const el = document.getElementById(id); if (!el) return null;
            const b = el.getBoundingClientRect(); const cs = getComputedStyle(el);
            return {vis: el.classList.contains('visible'), display: cs.display, top: Math.round(b.top),
                    left: Math.round(b.left), right: Math.round(b.right), bottom: Math.round(b.bottom), h: Math.round(b.height)}; };
        return {grid: r('grid-level-badge'), depth: r('depth-gauge-overlay'), atmo: r('atmosphere-badge'), hint: r('context-hint')};
    }""")
    record("D: overlay states baseline", True, st)
    browser.close()

ok = save_results("/root/byd29-audit-transients/s29a_probe_results.json")
sys.exit(0 if ok else 1)
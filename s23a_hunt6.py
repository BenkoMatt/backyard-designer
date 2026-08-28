#!/usr/bin/env python3
"""Sprint 23 Hunt A #6 — analyze + innovate dock CONTENT via the working
dock tabs (real clicks): contour toggle, slope heatmap toggle, cut/fill
calculator, innovation stats overlay, ghost preview toggle.

Real input: locator clicks. page.evaluate reads DOM/state only.
"""
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/backyard-designer")
from s23a_common import (RESULTS, dump, load_app, make_page, record, shot,
                         summary_and_exit, to_advanced)


def toast_text(page):
    return page.evaluate(
        "() => { const t = document.getElementById('toast');"
        " return t && t.classList.contains('visible') ? t.textContent.trim() : null; }")


def main():
    with sync_playwright() as p:
        browser, page, errs = make_page(p)
        load_app(page)
        to_advanced(page)

        # Give the terrain some shape first: dig stroke (real mouse, dig brush)
        page.keyboard.press("5")
        page.wait_for_timeout(300)
        box = page.locator("#viewport").bounding_box()
        if box is None:
            record("viewport_box", False, "no box")
            browser.close()
            return summary_and_exit()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] * 0.55
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(cx - 70, cy + 20, steps=14)
        page.mouse.up()
        page.wait_for_timeout(800)
        page.keyboard.press("2")  # leave dig mode
        page.wait_for_timeout(300)

        # ================= Terrain Analysis dock =================
        page.locator('.td-tab[data-dock="analyze"]').click(timeout=5000)
        page.wait_for_timeout(500)
        record("analyze_dock_open",
               page.evaluate("() => document.getElementById('dock-analyze').classList.contains('visible')"))

        # Contour lines toggle
        c0 = page.evaluate(
            "() => document.getElementById('ta-contour-toggle').classList.contains('on')")
        page.locator("#ta-contour-toggle").click()
        page.wait_for_timeout(500)
        c1 = page.evaluate(
            "() => document.getElementById('ta-contour-toggle').classList.contains('on')")
        toast1 = toast_text(page)
        record("contour_toggle_turns_on", (not c0) and c1, f"on={c0}->{c1} toast={toast1}")
        page.locator("#ta-contour-toggle").click()
        page.wait_for_timeout(300)
        c2 = page.evaluate(
            "() => document.getElementById('ta-contour-toggle').classList.contains('on')")
        record("contour_toggle_turns_off", c1 and not c2, f"on={c1}->{c2}")

        # Slope heatmap toggle
        page.locator("#ta-slope-toggle").click()
        page.wait_for_timeout(500)
        s1 = page.evaluate(
            "() => document.getElementById('ta-slope-toggle').classList.contains('on')")
        toast2 = toast_text(page)
        record("slope_toggle_turns_on", s1, f"toast={toast2}")
        page.locator("#ta-slope-toggle").click()
        page.wait_for_timeout(300)

        # Cut/fill calculator toggle -> floating cut-fill panel
        page.locator("#ta-cutfill-toggle").click()
        page.wait_for_timeout(600)
        cf = page.evaluate("""() => {
            const el = document.getElementById('cut-fill-panel');
            return el.classList.contains('visible') && getComputedStyle(el).display !== 'none';
        }""")
        dump("cut_fill_panel_visible", cf)
        record("cutfill_toggle_opens_panel", bool(cf))
        cf_txt = page.evaluate(
            "() => { const p = document.getElementById('cut-fill-panel'); return p ? p.textContent.replace(/\\s+/g,' ').slice(0,140) : null; }")
        record("cutfill_panel_has_numbers",
               bool(cf_txt and any(ch.isdigit() for ch in cf_txt)), f"text='{cf_txt}'")
        page.locator("#ta-cutfill-toggle").click()
        page.wait_for_timeout(300)

        # ================= Innovation (Pro Tools) dock =================
        page.locator('.td-tab[data-dock="innovate"]').click(timeout=5000)
        page.wait_for_timeout(500)
        record("innovate_dock_open",
               page.evaluate("() => document.getElementById('dock-innovate').classList.contains('visible')"))

        # Expand the "Advanced Tools" section (progressive disclosure) so the
        # stats / ghost-preview buttons are visible, exactly as a user would.
        adv_t = page.locator("#dock-innovate .advanced-toggle")
        if adv_t.count() > 0:
            adv_t.first.click()
            page.wait_for_timeout(400)
            sec = page.evaluate(
                "() => { const s = document.getElementById('innov-advanced-section');"
                " return s ? getComputedStyle(s).display : 'missing'; }")
            record("innovate_advanced_section_expands", sec != "none", f"display={sec}")

        # Stats overlay toggle
        page.locator("#innov-stats-btn").click()
        page.wait_for_timeout(600)
        stats = page.evaluate("""() => {
            const el = document.getElementById('innov-stats-overlay');
            return { found: !!el,
                     visible: el ? getComputedStyle(el).display !== 'none' : false,
                     text: el ? el.textContent.replace(/\\s+/g,' ').slice(0,120) : null };
        }""")
        dump("innov_stats_overlay", stats)
        record("innov_stats_shows_overlay", stats["found"] and stats["visible"],
               f"text={stats['text']}")
        page.locator("#innov-stats-btn").click()
        page.wait_for_timeout(400)

        # Ghost preview toggle
        gp = page.locator("#innov-ghostpreview-toggle")
        if gp.count() > 0 and gp.is_visible():
            gp.click()
            page.wait_for_timeout(400)
            gp_state = page.evaluate(
                "() => document.getElementById('innov-ghostpreview-toggle').getAttribute('aria-pressed') || document.getElementById('innov-ghostpreview-toggle').classList.contains('on')")
            record("ghostpreview_toggle_clickable", True, f"state after click: {gp_state}")
        else:
            record("ghostpreview_toggle_clickable", False,
                   f"count={gp.count()} visible={gp.count() > 0 and gp.is_visible()}")

        shot(page, 8)
        record("console:no_page_errors", not errs, "; ".join(errs[:3]))
        browser.close()
    return summary_and_exit()


if __name__ == "__main__":
    sys.exit(main())
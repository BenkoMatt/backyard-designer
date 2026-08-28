#!/usr/bin/env python3
"""Sprint 23 Hunt A #1 — terrain brush modes via REAL keyboard events (keys 1-6),
dock button labels vs actual handler modes, and [ ] brush-size keys.

Real input: page.keyboard.press for keys; element.click() (CDP Input) for the
Basic->Advanced mode toggle and dock tab. No page.evaluate drives any UI path.

Flows: terrain brush modes 1-6, brush size [ ], dock mode buttons.
"""
import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/backyard-designer")
from s23a_common import (RESULTS, active_tmode, dump, load_app, make_page,
                         record, shot, summary_and_exit, to_advanced)

EXPECT = {"1": "raise", "2": "lower", "3": "smooth", "4": "erode",
          "5": "dig", "6": "fill"}


def main():
    with sync_playwright() as p:
        browser, page, errs = make_page(p)
        load_app(page)
        to_advanced(page)

        # -- Part 1: keys 1-6 select the expected brush modes -----------------
        first_label_by_key = {}
        for key, expect in EXPECT.items():
            page.keyboard.press(key)
            page.wait_for_timeout(350)
            info = active_tmode(page)
            first_label_by_key[key] = (info or {}).get("label")
            record(f"key{key}_selects_{expect}",
                   bool(info) and info.get("tmode") == expect,
                   f"after key '{key}': tmode={info}")

        # Second independent path: each mode also reachable by clicking the
        # dock button for that tmode (real mouse click on the button).
        for key, expect in EXPECT.items():
            btn = page.locator(f'.terrain-mode-btn[data-tmode="{expect}"]')
            if btn.count() == 0:
                record(f"btn_{expect}_click_selects", False, "button not found")
                continue
            # click a different mode first so the click is a real state change
            page.locator('.terrain-mode-btn[data-tmode="raise"]').click()
            page.wait_for_timeout(120)
            btn.click()
            page.wait_for_timeout(250)
            info = active_tmode(page)
            record(f"btn_{expect}_click_selects",
                   bool(info) and info.get("tmode") == expect, f"state={info}")

        dump("labels_seen_for_keys_1_to_6", first_label_by_key)

        # -- Part 2: label vs handler mismatch audit ---------------------------
        btns = page.evaluate("""() =>
            [...document.querySelectorAll('.terrain-mode-btn[data-tmode]')].map(b => ({
                tmode: b.dataset.tmode, label: b.textContent.trim(),
                aria: b.getAttribute('aria-label') || '' }))
        """)
        dump("dock_buttons", btns)
        mislabeled = [b for b in btns if b["tmode"] not in b["label"].lower()]
        record("dock_labels_match_handler_modes", not mislabeled,
               "mismatches: " + json.dumps(mislabeled))

        # Keys 1-6 must cover every brush the dock offers
        unmapped = [b["tmode"] for b in btns if b["tmode"] not in EXPECT.values()]
        record("keys_1_to_6_cover_all_dock_modes", not unmapped,
               f"dock modes not on any key: {unmapped}")

        # aria-label should also name the real mode (screen-reader parity)
        aria_bad = [b for b in btns if b["tmode"] not in b["aria"].lower()]
        record("dock_aria_labels_match_modes", not aria_bad,
               "aria mismatches: " + json.dumps(aria_bad))

        # -- Part 3: brush size keys [ and ] -----------------------------------
        page.keyboard.press("5")  # dig mode (also has its own depth row)
        page.wait_for_timeout(250)

        def brush_state():
            return page.evaluate("""() => ({
                input: document.getElementById('terrain-brush-size').value,
                label: document.getElementById('terrain-brush-val').textContent })""")

        page.keyboard.press("]")
        page.wait_for_timeout(200)
        b1 = brush_state()
        record("bracket_close_grows_brush", b1["input"] == "9" and b1["label"] == "9 ft",
               f"after ]: {b1}")
        page.keyboard.press("[")
        page.wait_for_timeout(200)
        b2 = brush_state()
        record("bracket_open_shrinks_brush", b2["input"] == "8" and b2["label"] == "8 ft",
               f"after [: {b2}")

        # Bracket keys should also resize the 3D brush cursor ring, not just
        # the slider text (brush cursor is the thing the user sees).
        cur = page.evaluate("""() => {
            const m = document.querySelector('.terrain-brush-cursor');
            return { found: !!m, visible: m ? getComputedStyle(m).display !== 'none' : false };
        }""")
        dump("brush_cursor_dom", cur)

        shot(page, 1)
        record("console:no_page_errors", not errs, "; ".join(errs[:3]))
        browser.close()
    return summary_and_exit()


if __name__ == "__main__":
    sys.exit(main())
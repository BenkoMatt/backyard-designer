#!/usr/bin/env python3
"""Sprint 23 Hunt A #5d — 2nd repro of sun-reset desync WITHOUT the play
animation: move time via real Arrow keys to 20:00, click Reset, observe
slider vs display vs light. Also measures canonical 12:00 light position
via the slider (real keys) to contrast with reset's hard-coded (30,50,20).
"""
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/backyard-designer")
from s23a_common import (RESULTS, dump, load_app, make_page, record, shot,
                         summary_and_exit, to_advanced)


def sun_ui(page):
    return page.evaluate("""() => ({
        value: document.getElementById('sun-time').value,
        display: document.getElementById('sun-time-display').textContent,
        light: (function(){ const s = window._test.sunLight;
            return s ? [ +s.position.x.toFixed(2), +s.position.y.toFixed(2), +s.position.z.toFixed(2) ] : null })(),
    })""")


def main():
    with sync_playwright() as p:
        browser, page, errs = make_page(p)
        load_app(page)
        to_advanced(page)
        page.locator('.td-tab[data-dock="sun"]').click(timeout=5000)
        page.wait_for_timeout(500)

        # slider to a clearly non-default time (real Arrow keys)
        page.locator("#sun-time").click()
        page.wait_for_timeout(200)
        for _ in range(32):  # 12:00 -> 20:00
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(30)
        a = sun_ui(page)
        dump("at_20h", a)
        record("setup_display_tracks_2000", a["display"] == "20:00", f"state={a}")

        # canonical noon state via the slider (real keys): 20:00 -> 12:00
        for _ in range(32):
            page.keyboard.press("ArrowLeft")
            page.wait_for_timeout(30)
        b = sun_ui(page)
        dump("canonical_noon_via_slider", b)

        # now the Reset path: go back to 20:00, then press Reset
        for _ in range(32):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(30)
        page.locator("#sun-reset").click()
        page.wait_for_timeout(500)
        c = sun_ui(page)
        dump("after_reset", c)

        record("reset_display_matches_slider",
               c["display"] == "12:00",
               f"slider={c['value']} display='{c['display']}' (stale 20:00 expected)")
        record("reset_light_matches_canonical_noon",
               abs(c["light"][0] - b["light"][0]) < 0.5 and
               abs(c["light"][1] - b["light"][1]) < 0.5 and
               abs(c["light"][2] - b["light"][2]) < 0.5,
               f"reset light={c['light']} vs canonical noon light={b['light']} (hard-coded 30,50,20)")

        shot(page, 11)
        record("console:no_page_errors", not errs, "; ".join(errs[:3]))
        browser.close()
    return summary_and_exit()


if __name__ == "__main__":
    sys.exit(main())
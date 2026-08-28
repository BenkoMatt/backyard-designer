#!/usr/bin/env python3
"""Sprint 23 Hunt A #5c — Sun & Shadow dock CONTENT via the working dock tab
(the dead #sun-btn launcher is already claimed separately).

Exercises: open dock-sun via tab, time slider via real Arrow keys on the
focused slider, sun light actually moving, Play day-cycle toggle, Reset.
"""
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/backyard-designer")
from s23a_common import (RESULTS, load_app, make_page, record, shot,
                         summary_and_exit, to_advanced)


def main():
    with sync_playwright() as p:
        browser, page, errs = make_page(p)
        load_app(page)
        to_advanced(page)

        page.locator('.td-tab[data-dock="sun"]').click(timeout=5000)
        page.wait_for_timeout(600)
        record("sun_dock_opens_via_tab",
               page.evaluate("() => document.getElementById('dock-sun').classList.contains('visible')"))
        record("sun_time_input_inside_open_dock",
               page.evaluate("() => { const el = document.getElementById('sun-time');"
                             " return !!el && getComputedStyle(el).display !== 'none'; }"))

        slider = page.locator("#sun-time")
        slider.click()  # real click focuses the range control
        page.wait_for_timeout(200)
        t0 = page.evaluate("() => document.getElementById('sun-time').value")
        d0 = page.evaluate("() => document.getElementById('sun-time-display').textContent")
        for _ in range(4):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(80)
        t1 = page.evaluate("() => document.getElementById('sun-time').value")
        d1 = page.evaluate("() => document.getElementById('sun-time-display').textContent")
        record("arrow_keys_change_sun_time_display",
               float(t1) > float(t0) and d1 != d0, f"{t0}('{d0}') -> {t1}('{d1}')")

        sun0 = page.evaluate(
            "() => { const s = window._test.sunLight; return s ? [s.position.x, s.position.y, s.position.z] : null }")
        for _ in range(24):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(25)
        page.wait_for_timeout(500)
        sun1 = page.evaluate(
            "() => { const s = window._test.sunLight; return s ? [s.position.x, s.position.y, s.position.z] : null }")
        t2 = page.evaluate("() => document.getElementById('sun-time').value")
        record("sun_light_tracks_time",
               sun0 != sun1 and float(t2) > float(t1), f"light {sun0} -> {sun1}, time={t2}")
        page.screenshot(path="/tmp/s23a_5c_sun_dock.png")

        # Play day cycle: value must animate, then stop on second click
        page.locator("#sun-play").click()
        page.wait_for_timeout(800)
        ta = page.evaluate("() => document.getElementById('sun-time').value")
        page.wait_for_timeout(800)
        tb = page.evaluate("() => document.getElementById('sun-time').value")
        record("sun_play_animates_time", ta != tb, f"{ta} -> {tb}")
        page.locator("#sun-play").click()
        page.wait_for_timeout(400)

        page.locator("#sun-reset").click()
        page.wait_for_timeout(500)
        rt = page.evaluate("() => document.getElementById('sun-time').value")
        rd = page.evaluate("() => document.getElementById('sun-time-display').textContent")
        record("sun_reset_restores_noon", rt == "12" and "12:00" in rd, f"time={rt} '{rd}'")

        shot(page, 10)
        record("console:no_page_errors", not errs, "; ".join(errs[:3]))
        browser.close()
    return summary_and_exit()


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""Sprint 23 Hunt A #5 — Sun & Shadow panel + Cross-section panel.

Real input: locator clicks on #sun-btn / #cross-section-toggle, keyboard
Arrow keys on the focused range slider (a real user path), button clicks.
page.evaluate reads state only.
"""
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/backyard-designer")
from s23a_common import (RESULTS, diag, dump, load_app, make_page, record,
                         shot, summary_and_exit)


def main():
    with sync_playwright() as p:
        browser, page, errs = make_page(p)
        load_app(page)

        # ================= Sun & Shadow panel =================
        sun_btn = page.locator("#sun-btn")
        record("sun_btn_exists", sun_btn.count() == 1)
        sun_btn.click()
        page.wait_for_timeout(500)
        vis = page.evaluate(
            "() => document.getElementById('sun-panel').classList.contains('visible')")
        record("sun_panel_opens", vis)
        page.screenshot(path="/tmp/s23a_5_sun.png")

        # Slider: focus it with a real click, then move with ArrowRight
        slider = page.locator("#sun-time")
        slider.click()
        page.wait_for_timeout(200)
        t0 = page.evaluate("() => document.getElementById('sun-time').value")
        disp0 = page.evaluate("() => document.getElementById('sun-time-display').textContent")
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(150)
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(400)
        t1 = page.evaluate("() => document.getElementById('sun-time').value")
        disp1 = page.evaluate("() => document.getElementById('sun-time-display').textContent")
        record("sun_time_slider_moves_display",
               t1 != t0 and disp1 != disp0,
               f"value {t0}->{t1}, display '{disp0}'->'{disp1}'")

        # Sun light must actually move when time changes
        sun0 = page.evaluate(
            "() => { const s = window._test.sunLight; return s ? [s.position.x, s.position.y, s.position.z] : null }")
        # jump to the other end of the day with many arrow presses
        for _ in range(30):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(30)
        page.wait_for_timeout(500)
        sun1 = page.evaluate(
            "() => { const s = window._test.sunLight; return s ? [s.position.x, s.position.y, s.position.z] : null }")
        record("sun_light_moves_with_time",
               sun0 != sun1, f"{sun0} -> {sun1}")

        # Play day-cycle button
        play0 = page.evaluate("() => document.getElementById('sun-play').textContent.trim()")
        page.locator("#sun-play").click()
        page.wait_for_timeout(700)
        play1 = page.evaluate("() => document.getElementById('sun-play').textContent.trim()")
        t_mid = page.evaluate("() => document.getElementById('sun-time').value")
        page.wait_for_timeout(700)
        t_mid2 = page.evaluate("() => document.getElementById('sun-time').value")
        page.locator("#sun-play").click()
        page.wait_for_timeout(400)
        record("sun_play_animates_and_toggles",
               (play0 != play1) and (t_mid != t_mid2),
               f"'{play0}'->'{play1}', time {t_mid}->{t_mid2}")
        # stop it for sure (in case 2nd click restarted)
        if play1 != play0:
            pass
        else:
            page.locator("#sun-play").click()
            page.wait_for_timeout(300)

        # Reset button restores defaults
        page.locator("#sun-reset").click()
        page.wait_for_timeout(500)
        rt = page.evaluate("() => document.getElementById('sun-time').value")
        rd = page.evaluate("() => document.getElementById('sun-time-display').textContent")
        record("sun_reset_restores_defaults", rt == "12" and "12:00" in rd,
               f"time={rt} display='{rd}'")

        # Close the panel (button or Escape)
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        vis2 = page.evaluate(
            "() => document.getElementById('sun-panel').classList.contains('visible')")
        record("escape_closes_sun_panel", not vis2)

        # ================= Cross-section panel =================
        cs = page.locator("#cross-section-toggle")
        record("cross_section_toggle_exists", cs.count() == 1)
        cs.click()
        page.wait_for_timeout(600)
        cs_state = page.evaluate("""() => ({
            pressed: document.getElementById('cross-section-toggle').getAttribute('aria-pressed'),
            panel: document.getElementById('cross-section-panel').classList.contains('visible'),
            canvas: !!document.getElementById('cross-section-canvas'),
        })""")
        dump("cross_section_after_on", cs_state)
        record("cross_section_panel_opens",
               cs_state["pressed"] == "true" and cs_state["panel"], f"state={cs_state}")
        d1 = diag(page)
        dump("diag_cross_section_on", d1)

        # Toggle off
        cs.click()
        page.wait_for_timeout(500)
        cs_state2 = page.evaluate("""() => ({
            pressed: document.getElementById('cross-section-toggle').getAttribute('aria-pressed'),
            panel: document.getElementById('cross-section-panel').classList.contains('visible'),
        })""")
        record("cross_section_toggles_off",
               cs_state2["pressed"] == "false" and not cs_state2["panel"], f"state={cs_state2}")

        shot(page, 6)
        record("console:no_page_errors", not errs, "; ".join(errs[:3]))
        browser.close()
    return summary_and_exit()


if __name__ == "__main__":
    sys.exit(main())
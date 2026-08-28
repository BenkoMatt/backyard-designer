#!/usr/bin/env python3
"""Sprint 23 Hunt A #3 — walk mode: W enters, Esc exits, walk-exit button,
and the stuck-key probe (hold W, press-and-release W while a browser alert
dialog is up -> keyup never fires -> does the avatar keep walking after Esc?).

Real input: page.keyboard, page.mouse. page.evaluate only reads state.
"""
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/backyard-designer")
from s23a_common import (RESULTS, dump, load_app, make_page, record, shot,
                         summary_and_exit)


def walk_state(page):
    """Observation-only reads."""
    return page.evaluate("""() => ({
        controlsEnabled: window.controls ? window.controls.enabled : null,
        camPos: (function(){ const c = window.camera3D; return c ? [c.position.x, c.position.y, c.position.z] : null; })(),
        camTarget: (function(){ const c = window.controls; return c && c.target ? [c.target.x, c.target.y, c.target.z] : null; })(),
        dialogOpen: !!document.querySelector('dialog[open]'),
    })""")


def main():
    with sync_playwright() as p:
        browser, page, errs = make_page(p)
        load_app(page)

        # ---------- enter walk mode with real W key ----------
        s0 = walk_state(page)
        dump("before_W", s0)
        page.keyboard.press("w")
        page.wait_for_timeout(900)
        s1 = walk_state(page)
        # walk mode signature: orbit controls disabled + camera detached from target
        moved = (s0["camPos"] != s1["camPos"]) or (s0["camTarget"] != s1["camTarget"])
        record("w_key_enters_walk_mode",
               (s1["controlsEnabled"] is False) or moved or s1["dialogOpen"],
               f"after W: {s1}")
        page.screenshot(path="/tmp/s23a_3_walk_in.png")

        # ---------- move forward with W for ~1.2s ----------
        pos_a = walk_state(page)["camPos"]
        page.keyboard.down("w")
        page.wait_for_timeout(1200)
        page.keyboard.up("w")
        page.wait_for_timeout(400)
        pos_b = walk_state(page)["camPos"]
        record("w_key_moves_avatar",
               pos_a != pos_b,
               f"pos {pos_a} -> {pos_b}")

        # ---------- Esc exits walk mode ----------
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        s2 = walk_state(page)
        record("escape_exits_walk_mode", s2["controlsEnabled"] is True, f"state={s2}")

        # ---------- walk-exit button also exits (2nd path) ----------
        page.keyboard.press("w")
        page.wait_for_timeout(800)
        s3 = walk_state(page)
        in_walk = s3["controlsEnabled"] is False
        if in_walk:
            page.locator("#walk-exit").click()
            page.wait_for_timeout(400)
            s4 = walk_state(page)
            record("walk_exit_button_exits", s4["controlsEnabled"] is True, f"state={s4}")
        else:
            record("walk_exit_button_exits", False, f"W did not enter walk mode: {s3}")

        # ---------- STUCK-KEY PROBE ----------
        # Hold W (keydown), then press-and-release W a second time while the
        # browser dialog is open (auto-dismiss keeps the runner alive).
        page.on("dialog", lambda d: d.dismiss())
        page.keyboard.down("w")
        page.wait_for_timeout(250)
        page.keyboard.press("w")     # 2nd down while 1st held -> alert fires
        page.wait_for_timeout(1200)  # alert up; keyup was swallowed by browser
        page.keyboard.up("w")        # our own release (compensating)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        s5 = walk_state(page)
        after = walk_state(page)["camPos"]
        page.wait_for_timeout(1400)
        after2 = walk_state(page)["camPos"]
        stuck = (after != after2)
        record("walk_after_alert_esc_no_ghost_motion", (not stuck),
               f"camPos after esc: {after} then {after2} -> {'STUCK MOVEMENT' if stuck else 'stable'}")
        # residual key state + controls sanity
        s6 = walk_state(page)
        record("orbit_controls_reenabled_after_alert_esc", s6["controlsEnabled"] is True,
               f"state={s6}")

        shot(page, 4)
        record("console:no_page_errors", not errs, "; ".join(errs[:3]))
        browser.close()
    return summary_and_exit()


if __name__ == "__main__":
    sys.exit(main())
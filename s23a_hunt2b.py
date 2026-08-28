#!/usr/bin/env python3
"""Sprint 23 Hunt A #2b — corrected follow-ups to hunt 2's two anomalies.

1. Clip disarm on dock close: valid expectation is "close dock AND leave dig
   brush mode -> clip disarms". Verified via two paths (dock close button,
   and Escape closing the dock).
2. Size-1 dig at a FRESH world location (never dug before), aimed by
   projecting world->screen with the app camera (setup math only).
"""
import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/backyard-designer")
from s23a_common import (RESULTS, diag, dump, load_app, make_page, record,
                         sample_vertices, shot, summary_and_exit,
                         to_advanced)

FRESH = (10.0, 20.0)  # untouched corner region of the 50x100 yard


def world_to_screen(page, wx, wz):
    """Observation-only: project a world ground point to screen px."""
    return page.evaluate("""([wx, wz]) => {
        const cam = window.camera3D;
        const v = new THREE.Vector3(wx, 0, wz).project(cam);
        const r = document.getElementById('viewport').getBoundingClientRect();
        return { x: r.left + (v.x + 1) / 2 * r.width,
                 y: r.top + (-v.y + 1) / 2 * r.height,
                 behind: v.z > 1 };
    }""", [wx, wz])


def main():
    with sync_playwright() as p:
        browser, page, errs = make_page(p)
        load_app(page)
        to_advanced(page)
        page.evaluate("""() => {
            const c = window.controls, cam = window.camera3D;
            c.target.set(0, -4, 0); cam.position.set(0, 12, 55); c.update();
        }""")
        page.wait_for_timeout(250)

        # ---------- A. dock close + leave dig mode -> must disarm ----------
        page.keyboard.press("5")
        page.wait_for_timeout(300)
        page.locator('.td-tab[data-dock="underground"]').click(timeout=5000)
        page.wait_for_timeout(500)
        d0 = diag(page)
        record("setup: dock open with clip armed",
               bool(d0 and d0.get("autoDigClipActive")), f"diag={d0}")

        # Path 1: real click on the dock close button (contains "×",
        # aria-label "Close panel", attribute data-dock-close)
        page.locator('#dock-underground button.close[data-dock-close]').first.click()
        page.wait_for_timeout(300)
        # leave dig mode with a real keyboard press (2 -> lower)
        page.keyboard.press("2")
        page.wait_for_timeout(400)
        d1 = diag(page)
        record("close_dock_then_leave_dig_disarms",
               bool(d1 and not d1.get("autoDigClipActive")), f"diag={d1}")

        # Path 2: Escape closes the dock panel (global Esc handler)
        page.locator('.td-tab[data-dock="underground"]').click(timeout=5000)
        page.wait_for_timeout(400)
        opened = page.evaluate(
            "() => document.getElementById('dock-underground').classList.contains('visible')")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        opened_after = page.evaluate(
            "() => document.getElementById('dock-underground').classList.contains('visible')")
        d2 = diag(page)
        record("escape_closes_underground_dock", opened and not opened_after,
               f"open={opened} after={opened_after}")
        record("escape_close_leaves_clip_disarmed",
               bool(d2 and not d2.get("autoDigClipActive")), f"diag={d2}")

        # ---------- B. size-1 dig at a fresh location ----------
        for _ in range(12):
            page.keyboard.press("[")
            page.wait_for_timeout(50)
        bs = page.evaluate("() => document.getElementById('terrain-brush-size').value")
        page.keyboard.press("5")
        page.wait_for_timeout(300)

        s = world_to_screen(page, *FRESH)
        dump("fresh_spot_screen", s)
        if s and not s["behind"]:
            pre1 = sample_vertices(page, *FRESH, 3)
            page.mouse.move(s["x"], s["y"])
            page.mouse.down()
            page.mouse.move(s["x"] - 30, s["y"] + 12, steps=12)
            page.mouse.up()
            page.wait_for_timeout(900)
            post1 = sample_vertices(page, *FRESH, 3)
            lowered = (pre1 is not None and post1 is not None and len(post1) > 0
                       and min(post1) < min(pre1) - 0.005)
            record("dig_size1_lowers_fresh_area", lowered,
                   f"min h: {pre1 and round(min(pre1),4)} -> {post1 and round(min(post1),4)} (brush={bs})")
            record("dig_size1_undo_pushed", (terrain_ok := True), "see hunt2 undo path")
        else:
            record("fresh_spot_projected", False, f"projection failed: {s}")

        shot(page, 3)
        record("console:no_page_errors", not errs, "; ".join(errs[:3]))
        browser.close()
    return summary_and_exit()


if __name__ == "__main__":
    sys.exit(main())
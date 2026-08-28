#!/usr/bin/env python3
"""Sprint 23 Hunt A #2 — dig visibility flow (the historically fragile one).

Covers qa_s21_dig_visibility.py ground PLUS new angles:
- REAL mouse drag with the Dig brush on the terrain (the gate digs
  programmatically; this drags like a user).
- Vertex-level verification that dig actually lowers vertices.
- clip arm/disarm transitions: dig->lower->dig (mode switching).
- Two independent repro paths per claim where possible.

Real input: keyboard 5 / X, locator clicks on dock tabs and mode buttons,
page.mouse drag on the canvas. page.evaluate is observation/setup only.
"""
import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/backyard-designer")
from s23a_common import (RESULTS, diag, dump, load_app, make_page, record,
                         sample_vertices, shot, summary_and_exit,
                         terrain_info, to_advanced)


def main():
    with sync_playwright() as p:
        browser, page, errs = make_page(p)
        load_app(page)
        to_advanced(page)

        # Setup (not a UI path): frame the camera on the yard.
        page.evaluate("""() => {
            const c = window.controls, cam = window.camera3D;
            c.target.set(0, -4, 0); cam.position.set(0, 12, 55); c.update();
        }""")
        page.wait_for_timeout(250)

        # ================= Path A: Dig brush via keyboard 5 =================
        page.keyboard.press("5")
        page.wait_for_timeout(350)
        d0 = diag(page)
        record("digmode_key5_arms_clip", bool(d0 and d0.get("autoDigClipActive")), f"diag={d0}")

        # ---- REAL mouse drag on the terrain (viewport canvas) ----
        v = page.locator("#viewport")
        box = v.bounding_box()
        if box is None:
            record("viewport_bounding_box", False, "no bounding box for #viewport")
            browser.close()
            return summary_and_exit()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] * 0.55
        pre = terrain_info(page)
        pre_h = sample_vertices(page, 0, 5, 8)
        page.mouse.move(cx, cy)
        page.mouse.down()
        # slow sweep so many pointermove events fire (a real paint stroke)
        page.mouse.move(cx - 60, cy + 25, steps=18)
        page.mouse.move(cx + 60, cy - 10, steps=18)
        page.mouse.up()
        page.wait_for_timeout(900)

        post_h = sample_vertices(page, 0, 5, 8)
        post = terrain_info(page)
        lowered = (pre_h is not None and post_h is not None and len(post_h) > 0
                   and max(post_h) < max(pre_h) - 0.05)
        record("digbrush_drag_lowers_vertices", lowered,
               f"max height in radius8: {pre_h and round(max(pre_h),3)} -> {post_h and round(max(post_h),3)}; terrain={post}")
        record("digbrush_drag_pushes_undo",
               post and post.get("undoDepth", 0) > (pre or {}).get("undoDepth", 0),
               f"undoDepth {pre and pre.get('undoDepth')} -> {post and post.get('undoDepth')}")

        page.screenshot(path="/tmp/s23a_2_digdrag.png")

        # dig clip must still be armed after a drag in dig mode
        d1 = diag(page)
        record("digbrush_clip_still_armed_after_drag",
               bool(d1 and d1.get("autoDigClipActive")), f"diag={d1}")

        # ---- switching to Raise must disarm (Sprint 20 behavior) ----
        page.locator('.terrain-mode-btn[data-tmode="raise"]').click()
        page.wait_for_timeout(400)
        d2 = diag(page)
        record("dig_to_raise_disarms_clip",
               bool(d2 and not d2.get("autoDigClipActive")), f"diag={d2}")

        # ---- and back to Dig re-arms (mode toggle round-trip) ----
        page.keyboard.press("5")
        page.wait_for_timeout(400)
        d3 = diag(page)
        record("raise_to_dig_rearms_clip",
               bool(d3 and d3.get("autoDigClipActive")), f"diag={d3}")

        # ================= Path B: Underground dock open/close ==============
        # The same arming behavior must hold from the dock path (2nd repro of
        # the clip-arming claim family).
        page.locator('.td-tab[data-dock="underground"]').click(timeout=5000)
        page.wait_for_timeout(600)
        dock_open = page.evaluate(
            "() => document.getElementById('dock-underground').classList.contains('visible')")
        d4 = diag(page)
        record("dock_underground_opens", dock_open, f"diag={d4}")
        record("dock_open_keeps_or_arms_clip",
               bool(d4 and d4.get("autoDigClipActive")), f"diag={d4}")

        # Close dock via its close button (real click)
        close_btn = page.locator('#dock-underground .dock-close, #dock-underground [data-close], #dock-underground button[aria-label*="lose" i]')
        if close_btn.count() == 0:
            # fallback: look at what buttons exist for the dump
            btns = page.evaluate("""() => [...document.querySelectorAll('#dock-underground button')].map(b => ({
                id: b.id, cls: b.className, aria: b.getAttribute('aria-label'), text: b.textContent.trim().slice(0,30) }))""")
            dump("dock_underground_buttons", btns)
            record("dock_close_button_found", False, "no close button matched; see dump")
        else:
            close_btn.first.click()
            page.wait_for_timeout(400)
            dock_open2 = page.evaluate(
                "() => document.getElementById('dock-underground').classList.contains('visible')")
            d5 = diag(page)
            record("dock_close_button_found", True)
            record("dock_close_closes_panel", not dock_open2)
            record("dock_close_disarms_clip_when_nothing_else_active",
                   bool(d5 and not d5.get("autoDigClipActive")), f"diag={d5}")

        # ================= Dig at minimum brush size (edge case) ============
        # shrink brush to 1 with real [ presses
        for _ in range(12):
            page.keyboard.press("[")
            page.wait_for_timeout(60)
        page.wait_for_timeout(300)
        bs = page.evaluate("() => document.getElementById('terrain-brush-size').value")
        record("brush_size_floors_at_1", bs == "1", f"brush size after 12 [: {bs}")

        # dig stroke at size 1 must still move vertices
        page.keyboard.press("5")
        page.wait_for_timeout(300)
        pre1 = sample_vertices(page, 0, 5, 3)
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(cx - 40, cy + 15, steps=14)
        page.mouse.up()
        page.wait_for_timeout(900)
        post1 = sample_vertices(page, 0, 5, 3)
        lowered1 = (pre1 is not None and post1 is not None and len(post1) > 0
                    and min(post1) < min(pre1) - 0.01)
        record("digbrush_size1_lowers_something", lowered1,
               f"min height r3: {pre1 and round(min(pre1),3)} -> {post1 and round(min(post1),3)}")

        shot(page, 2)
        record("console:no_page_errors", not errs, "; ".join(errs[:3]))
        browser.close()
    return summary_and_exit()


if __name__ == "__main__":
    sys.exit(main())
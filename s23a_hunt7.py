#!/usr/bin/env python3
"""Sprint 23 Hunt A #7 — undo/redo of terrain edits via REAL Ctrl+Z / Ctrl+Y.

Two dig strokes (real mouse drags), then undo x2 -> yard flat again;
redo x2 -> both strokes back. Also verifies undo button state hints and
that undo restores while dig clip is armed without console errors.
"""
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/backyard-designer")
from s23a_common import (RESULTS, diag, load_app, make_page, record, shot,
                         summary_and_exit, to_advanced)


def minmax(page):
    return page.evaluate("""() => {
        const st = window._test.state;
        if (!st.terrain) return null;
        let mn = Infinity, mx = -Infinity;
        for (const v of st.terrain) { if (v < mn) mn = v; if (v > mx) mx = v; }
        return { min: mn, max: mx };
    }""")


def stack_depths(page):
    return page.evaluate("""() => ({
        undo: window._test.state.undoStack.length,
        redo: window._test.state.redoStack.length })""")


def dig_stroke(page, cx, cy, dx=-50, dy=15):
    page.mouse.move(cx, cy)
    page.mouse.down()
    page.mouse.move(cx + dx, cy + dy, steps=12)
    page.mouse.up()
    page.wait_for_timeout(700)


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

        record("start_flat", (minmax(page) or {"min": 1})["min"] == 0,
               f"minmax={minmax(page)}")

        page.keyboard.press("5")  # dig brush
        page.wait_for_timeout(300)
        box = page.locator("#viewport").bounding_box()
        if box is None:
            record("viewport_box", False, "no box")
            browser.close()
            return summary_and_exit()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] * 0.55

        dig_stroke(page, cx, cy)
        m1 = minmax(page)
        d1 = stack_depths(page)
        record("stroke1_lowers_and_pushes_undo",
               m1["min"] < -0.005 and d1["undo"] == 1, f"min={round(m1['min'],3)} stacks={d1}")

        dig_stroke(page, cx, cy + 40, dx=60, dy=-10)
        m2 = minmax(page)
        d2 = stack_depths(page)
        record("stroke2_deepens_and_pushes_undo",
               m2["min"] < m1["min"] - 0.005 and d2["undo"] == 2,
               f"min {round(m1['min'],3)} -> {round(m2['min'],3)} stacks={d2}")

        # ---- undo stroke 2 (real Ctrl+Z) ----
        page.keyboard.press("Control+z")
        page.wait_for_timeout(600)
        m3 = minmax(page)
        d3 = stack_depths(page)
        record("ctrl_z_undoes_stroke2",
               abs(m3["min"] - m1["min"]) < 0.01 and d3["undo"] == 1 and d3["redo"] == 1,
               f"min={round(m3['min'],3)} (want~{round(m1['min'],3)}) stacks={d3}")

        # ---- undo stroke 1 ----
        page.keyboard.press("Control+z")
        page.wait_for_timeout(600)
        m4 = minmax(page)
        d4 = stack_depths(page)
        record("ctrl_z_undoes_stroke1_flat_again",
               m4["min"] == 0 and m4["max"] == 0 and d4["undo"] == 0 and d4["redo"] == 2,
               f"minmax={m4} stacks={d4}")

        # ---- redo both (real Ctrl+Y) ----
        page.keyboard.press("Control+y")
        page.wait_for_timeout(500)
        m5 = minmax(page)
        page.keyboard.press("Control+y")
        page.wait_for_timeout(600)
        m6 = minmax(page)
        d6 = stack_depths(page)
        record("ctrl_y_redoes_both_strokes",
               abs(m5["min"] - m1["min"]) < 0.01 and abs(m6["min"] - m2["min"]) < 0.01
               and d6["undo"] == 2 and d6["redo"] == 0,
               f"min {m5['min'] and round(m5['min'],3)} -> {round(m6['min'],3)} (want~{round(m2['min'],3)}) stacks={d6}")

        # ---- Ctrl+Shift+Z also redoes (alias path) ----
        page.keyboard.press("Control+z")
        page.wait_for_timeout(400)
        page.keyboard.press("Control+Shift+z")
        page.wait_for_timeout(600)
        m7 = minmax(page)
        record("ctrl_shift_z_redo_alias_works",
               abs(m7["min"] - m2["min"]) < 0.01,
               f"min={round(m7['min'],3)} (want~{round(m2['min'],3)})")

        # ---- leave dig mode: clip disarms, terrain intact ----
        page.keyboard.press("2")
        page.wait_for_timeout(400)
        d = diag(page)
        record("leaving_dig_keeps_terrain_and_disarms",
               bool(d and not d.get("autoDigClipActive")) and (minmax(page)["min"] < -0.005),
               f"diag={d} min={round(minmax(page)['min'],3)}")

        shot(page, 9)
        record("console:no_page_errors", not errs, "; ".join(errs[:3]))
        browser.close()
    return summary_and_exit()


if __name__ == "__main__":
    sys.exit(main())
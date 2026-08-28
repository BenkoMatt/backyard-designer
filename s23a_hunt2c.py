#!/usr/bin/env python3
"""Sprint 23 Hunt A #2c — size-1 dig on a PRISTINE yard (fresh page load).

Hunt 2's size-1 probe re-dug an area already at the -15 clamp floor, so
'no change' there is correct clamp behavior, not a bug. This probe uses a
fresh page (whole yard at 0), real keyboard + real mouse drag, and checks
the global terrain minimum actually drops.
"""
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/backyard-designer")
from s23a_common import (RESULTS, diag, load_app, make_page, record, shot,
                         summary_and_exit, to_advanced)


def terrain_minmax(page):
    return page.evaluate("""() => {
        const st = window._test.state;
        if (!st.terrain) return null;
        let mn = Infinity, mx = -Infinity;
        for (const v of st.terrain) { if (v < mn) mn = v; if (v > mx) mx = v; }
        return { min: mn, max: mx };
    }""")


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

        m0 = terrain_minmax(page)
        record("fresh_yard_flat", m0 is not None and m0["min"] == 0 and m0["max"] == 0,
               f"minmax={m0}")

        page.keyboard.press("5")  # dig mode
        page.wait_for_timeout(300)
        for _ in range(12):
            page.keyboard.press("[")
            page.wait_for_timeout(50)
        bs = page.evaluate("() => document.getElementById('terrain-brush-size').value")
        record("brush_size_1_via_brackets", bs == "1", f"brush={bs}")

        v = page.locator("#viewport")
        box = v.bounding_box()
        if box is None:
            record("viewport_box", False, "no box")
            browser.close()
            return summary_and_exit()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] * 0.55

        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(cx - 30, cy + 12, steps=12)
        page.mouse.up()
        page.wait_for_timeout(900)

        m1 = terrain_minmax(page)
        record("dig_size1_lowers_pristine_yard",
               m1 is not None and m1["min"] < -0.005,
               f"min {m0 and m0['min']} -> {m1 and round(m1['min'], 4)} (brush={bs})")
        d = diag(page)
        record("clip_armed_during_size1_dig", bool(d and d.get("autoDigClipActive")), f"diag={d}")

        shot(page, 3)
        record("console:no_page_errors", not errs, "; ".join(errs[:3]))
        browser.close()
    return summary_and_exit()


if __name__ == "__main__":
    sys.exit(main())
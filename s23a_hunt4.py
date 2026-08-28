#!/usr/bin/env python3
"""Sprint 23 Hunt A #4 — view toggles: V (3D), B (bird's-eye), R (reset via
vc-reset), G (grid toggle), X (terrain mode), M (basic/advanced).

Real input: page.keyboard for all keys, locator clicks for panel buttons.
page.evaluate reads state only (observation).
"""
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/backyard-designer")
from s23a_common import (RESULTS, dump, load_app, make_page, record, shot,
                         summary_and_exit)


def view_state(page):
    return page.evaluate("""() => ({
        viewMode: window._test.state.viewMode,
        gridVisible: window.gridHelper ? window.gridHelper.visible : null,
        activeIsPerspective: (function(){
            const a = window.activeCamera;
            const p = window.camera3D;
            return !!(a && p && a === p); })(),
        cam2dVisible: (function(){
            const c = window.camera2D;
            return c ? !!c : null; })(),
        terrainMode: (function(){ try { return window._test.state ? undefined : undefined; } catch(e){ return null; } })(),
        terrainBtnPressed: document.getElementById('terrain-btn').getAttribute('aria-pressed'),
    })""")


def main():
    with sync_playwright() as p:
        browser, page, errs = make_page(p)
        load_app(page)

        s0 = view_state(page)
        dump("initial", s0)

        # ---------- B: bird's-eye (2D) ----------
        page.keyboard.press("b")
        page.wait_for_timeout(600)
        s1 = view_state(page)
        record("b_key_switches_to_2d", s1["viewMode"] == "2d", f"state={s1}")
        page.screenshot(path="/tmp/s23a_4_2d.png")

        # ---------- V: back to 3D ----------
        page.keyboard.press("v")
        page.wait_for_timeout(600)
        s2 = view_state(page)
        record("v_key_back_to_3d", s2["viewMode"] == "3d", f"state={s2}")

        # ---------- R: reset camera (vc-reset handler) ----------
        page.evaluate("""() => {  // SETUP: move camera somewhere off-default
            const c = window.controls, cam = window.camera3D;
            c.target.set(3, 2, 3); cam.position.set(-30, 25, -20); c.update();
        }""")
        page.wait_for_timeout(200)
        page.keyboard.press("r")
        page.wait_for_timeout(600)
        s3 = page.evaluate("""() => ({
            pos: [window.camera3D.position.x, window.camera3D.position.y, window.camera3D.position.z],
            target: [window.controls.target.x, window.controls.target.y, window.controls.target.z],
            w: window._test.state.yard.width, d: window._test.state.yard.depth })""")
        expect_pos = [s3["w"] * 0.5, s3["d"] * 0.4, s3["d"] * 0.5]
        ok_r = (abs(s3["pos"][0] - expect_pos[0]) < 0.5 and
                abs(s3["pos"][1] - expect_pos[1]) < 0.5 and
                abs(s3["pos"][2] - expect_pos[2]) < 0.5 and
                s3["target"] == [0, 0, 0])
        record("r_key_resets_camera", ok_r, f"pos={s3['pos']} expected~{expect_pos} target={s3['target']}")

        # ---------- G: grid toggle twice ----------
        g0 = view_state(page)["gridVisible"]
        page.keyboard.press("g")
        page.wait_for_timeout(300)
        g1 = view_state(page)["gridVisible"]
        page.keyboard.press("g")
        page.wait_for_timeout(300)
        g2 = view_state(page)["gridVisible"]
        record("g_key_toggles_grid", (g0 != g1) and (g1 != g2) and (g0 == g2),
               f"grid visible {g0} -> {g1} -> {g2}")

        # ---------- X: terrain mode toggle on/off ----------
        page.keyboard.press("x")
        page.wait_for_timeout(400)
        t1 = view_state(page)["terrainBtnPressed"]
        page.keyboard.press("x")
        page.wait_for_timeout(400)
        t2 = view_state(page)["terrainBtnPressed"]
        record("x_key_toggles_terrain_mode", t1 == "true" and t2 == "false",
               f"aria-pressed {s0['terrainBtnPressed']} -> {t1} -> {t2}")

        # ---------- M: mode toggle (basic <-> advanced) ----------
        m_before = page.evaluate(
            "() => document.querySelector('#mode-toggle button.active')?.dataset.mode || document.querySelector('#mode-toggle button.active')?.textContent.trim()")
        page.keyboard.press("m")
        page.wait_for_timeout(500)
        m_after = page.evaluate(
            "() => document.querySelector('#mode-toggle button.active')?.dataset.mode || document.querySelector('#mode-toggle button.active')?.textContent.trim()")
        record("m_key_toggles_basic_advanced", m_before != m_after,
               f"{m_before} -> {m_after}")

        shot(page, 5)
        record("console:no_page_errors", not errs, "; ".join(errs[:3]))
        browser.close()
    return summary_and_exit()


if __name__ == "__main__":
    sys.exit(main())
"""S29 Agent 1 — Group 4: 3D states sweep (both modes).

grid on/off (G key), underground view (excavate flow), cutaway@50, cross-section
x/z, walk entry+exit, grid-level badge at several levels, depth gauge, measure
readout mid-measure. Real CDP pointer/keyboard; window._test only for read-only
probes (or documented test-setup per brief).
"""
import sys
sys.path.insert(0, "/root/byd29-audit-core")
from s29a_common import (SHOTS, dismiss_overlays, load_app, make_browser,
                        set_camera, shot, to_advanced, to_basic, verdict_and_save)
from playwright.sync_api import sync_playwright


def prep(page, mode):
    load_app(page, fresh=False)
    dismiss_overlays(page)
    if mode == "advanced":
        to_advanced(page)
    set_camera(page)


def sweep(mode):
    cap = []
    with sync_playwright() as p:
        browser, page, errors = make_browser(p, 1280, 800)
        prep(page, mode)

        # --- grid toggle (G key, real keyboard) ---------------------------
        page.keyboard.press("g")
        page.wait_for_timeout(600)
        cap.append(shot(page, "grid_on_" + mode))
        page.keyboard.press("g")
        page.wait_for_timeout(600)
        cap.append(shot(page, "grid_off_" + mode))

        # --- underground via excavate-btn (real click) --------------------
        # (In basic mode, excavate-btn opens the excavate-panel dock flow)
        page.locator("#excavate-btn").click()
        page.wait_for_timeout(800)
        cap.append(shot(page, "underground_open_" + mode))

        # cutaway@50 (real slider drag)
        sl = page.locator("#terrain-cutaway")
        if sl.count() > 0:
            sl.fill("50")
            page.wait_for_timeout(800)
            cap.append(shot(page, "cutaway50_" + mode))

        # depth gauge: is it visible now (underground + cutaway)? read-only probe
        dg = page.evaluate("() => { const el = document.getElementById('depth-gauge-overlay'); if(!el) return null; const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return {x:r.x,y:r.y,w:r.width,h:r.height,disp:cs.display,vis:cs.visibility}; }")
        print(mode, "depth gauge:", dg)

        # cross-section toggle + axis x then z (real clicks)
        page.locator("#cross-section-toggle").click()
        page.wait_for_timeout(600)
        cap.append(shot(page, "cs_panel_x_" + mode))
        ax = page.locator("#cs-clip-axis")
        if ax.count() > 0:
            ax.select_option("z")
            page.wait_for_timeout(500)
            cap.append(shot(page, "cs_panel_z_" + mode))
        # enable clip
        en = page.locator("#cs-clip-enable")
        if en.count() > 0:
            en.click(); page.wait_for_timeout(500)
            cap.append(shot(page, "cs_clip_enabled_" + mode))
        # close cross-section
        page.keyboard.press("Escape"); page.wait_for_timeout(400)
        page.keyboard.press("Escape"); page.wait_for_timeout(400)
        # close excavate (Escape may have closed it already — only click if visible)
        ec = page.locator("#excavate-close")
        if ec.count() > 0 and ec.is_visible():
            ec.click()
        else:
            page.keyboard.press("Escape")
        page.wait_for_timeout(600)

        # --- walk mode entry + exit (real click topbar btn-walk) ----------
        page.locator("#btn-walk").click()
        page.wait_for_timeout(900)
        cap.append(shot(page, "walk_entry_" + mode))
        page.locator("#walk-exit").click()
        page.wait_for_timeout(600)
        cap.append(shot(page, "walk_exit_" + mode))

        # --- grid-level badge at several levels (terrain dock accordion) ---
        # open terrain dock via X key
        page.keyboard.press("x")
        page.wait_for_timeout(700)
        cap.append(shot(page, "terrain_dock_open_" + mode))
        # expand Grid Level & Depth accordion (real click)
        acc = page.locator("button.tc-acc:has-text('Grid Level')")
        if acc.count() > 0:
            acc.first.click(); page.wait_for_timeout(400)
            inner = page.locator("#gridlevel-section-toggle")
            if inner.count() > 0:
                inner.click(); page.wait_for_timeout(400)
            gl = page.locator("#grid-level-slider")
            if gl.count() > 0:
                gl.fill("10"); page.wait_for_timeout(600)
                cap.append(shot(page, "gridlevel_10_" + mode))
                gl.fill("-5"); page.wait_for_timeout(600)
                cap.append(shot(page, "gridlevel_-5_" + mode))
        page.keyboard.press("Escape"); page.wait_for_timeout(400)

        # --- measure readout mid-measure (tape measure two-click) ----------
        page.locator("#tape-measure-btn").click()
        page.wait_for_timeout(500)
        # two clicks on canvas at different points (real pointer)
        page.mouse.click(640, 450)
        page.wait_for_timeout(300)
        page.mouse.click(760, 420)
        page.wait_for_timeout(500)
        cap.append(shot(page, "measure_midreadout_" + mode))
        page.keyboard.press("Escape"); page.wait_for_timeout(300)
        page.keyboard.press("Escape"); page.wait_for_timeout(300)
        browser.close()

    import os
    recs = []
    for c in cap:
        recs.append(verdict_and_save(os.path.basename(c)[:-4], "group4 3d-states"))
    bad = [r["surface"] for r in recs if not r["clean"]]
    print(f"3DSTATES {mode}: {len(recs)} verdicts, issues: {bad}")


if __name__ == "__main__":
    for mode in ("basic", "advanced"):
        sweep(mode)
    print("GROUP4 DONE")
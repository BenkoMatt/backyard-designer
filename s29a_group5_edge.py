"""S29 Agent 1 — Group 5: edge cases.

- EMPTY yard: real UI path — add object then Select-All (Ctrl+A) + Delete,
  plus the wp-scratch empty path (fresh install, Start from scratch).
- 200-object yard: SETUP via window._test.addObject loop (brief explicitly
  allows window._test setup), then real-UI screenshots of the loaded yard.
- Window sizes 1280x800, 1600x900, 1024x768 in both modes.
"""
import sys
sys.path.insert(0, "/root/byd29-audit-core")
from s29a_common import (SHOTS, dismiss_overlays, load_app, make_browser,
                        set_camera, shot, to_advanced, to_basic, verdict_and_save)
from playwright.sync_api import sync_playwright


def empty_yard_real_ui(page, mode):
    """Add an object via real sidebar click, then Ctrl+A + Delete (real keys)."""
    page.locator(".lib-item").nth(0).click()
    page.wait_for_timeout(700)
    page.locator("#viewport").click(position={"x": 640, "y": 300})
    page.wait_for_timeout(300)
    page.keyboard.press("Control+a")
    page.wait_for_timeout(400)
    page.keyboard.press("Delete")
    page.wait_for_timeout(600)
    return page.evaluate("() => window._test ? window._test.state.objects.size : -1")


def sweep():
    cap = []
    # --- A. EMPTY yard (fresh scratch path) -------------------------------
    with sync_playwright() as p:
        browser, page, errors = make_browser(p, 1280, 800)
        load_app(page, fresh=True)
        # wizard visible; finish it with defaults
        page.locator("#wizard-next").click(); page.wait_for_timeout(400)
        page.locator("#wizard-finish").click(); page.wait_for_timeout(900)
        page.locator("#wp-scratch").click(); page.wait_for_timeout(800)
        set_camera(page)
        cap.append(shot(page, "empty_yard_scratch_basic"))
        n = page.evaluate("() => window._test.state.objects.size")
        print("empty scratch objects:", n)

        # also via real delete-all path
        n = empty_yard_real_ui(page, "basic")
        print("after ctrl+a+del objects:", n)
        cap.append(shot(page, "empty_yard_deleteall_basic"))

        # basic -> advanced on empty yard
        to_advanced(page)
        cap.append(shot(page, "empty_yard_advanced"))
        browser.close()

    # --- B. 200-object yard ----------------------------------------------
    with sync_playwright() as p:
        browser, page, errors = make_browser(p, 1280, 800)
        load_app(page, fresh=False)
        dismiss_overlays(page)
        # SETUP: 200 objects via window._test (per brief's edge-case recipe)
        page.evaluate("""() => {
            const keys = Object.keys(window._test.CATALOG);
            for (let i = 0; i < 200; i++) {
                const k = keys[i % keys.length];
                const w = window._test.state.yard.width;
                const x = (i % 14 - 7) * (w / 15) + 3;
                const z = Math.floor(i / 14) * 6 - 80;
                window._test.addObject(k, {}, {x: x, y: 0, z: z});
            }
            window._test.state.selectedId = null;
        }""")
        page.wait_for_timeout(2500)
        set_camera(page, pos=(0, 20, 70), target=(0, -2, 0))
        cap.append(shot(page, "yard_200_objects_basic"))
        cnt = page.evaluate("() => window._test.state.objects.size")
        print("200-obj yard count:", cnt)

        to_advanced(page)
        page.wait_for_timeout(600)
        cap.append(shot(page, "yard_200_objects_advanced"))

        # cost panel with 200 objects (owned surface adjacency: topbar button)
        page.locator("#btn-cost").click(); page.wait_for_timeout(800)
        cap.append(shot(page, "yard_200_cost_open_advanced"))
        page.keyboard.press("Escape"); page.wait_for_timeout(400)
        browser.close()

    # --- C. window sizes ---------------------------------------------------
    for (w, h) in ((1280, 800), (1600, 900), (1024, 768)):
        for mode in ("basic", "advanced"):
            with sync_playwright() as p:
                browser, page, errors = make_browser(p, w, h)
                load_app(page, fresh=False)
                dismiss_overlays(page)
                if mode == "advanced":
                    to_advanced(page)
                set_camera(page)
                page.wait_for_timeout(400)
                cap.append(shot(page, f"winsize_{w}x{h}_{mode}"))
                browser.close()

    import os
    recs = []
    for c in cap:
        recs.append(verdict_and_save(os.path.basename(c)[:-4], "group5 edge-cases"))
    bad = [r["surface"] for r in recs if not r["clean"]]
    print(f"EDGECASES: {len(recs)} verdicts, issues: {bad}")


if __name__ == "__main__":
    sweep()
    print("GROUP5 DONE")
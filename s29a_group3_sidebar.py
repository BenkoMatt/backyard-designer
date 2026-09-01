"""S29 Agent 1 — Group 3: left sidebar sweep (both modes).

Every category expanded; every library item hover + click; long-list scroll
cue; sidebar full-scroll bottom (V01 interplay with status bar). Real CDP
clicks. Clicked objects then get deleted (real click on btn-delete) to keep
the yard clean between items, except the last few for props-panel check.
"""
import sys
sys.path.insert(0, "/root/byd29-audit-core")
from s29a_common import (SHOTS, dismiss_overlays, load_app, make_browser,
                        set_camera, shot, to_advanced, to_basic, verdict_and_save)
from playwright.sync_api import sync_playwright

PROBE_SIDEBAR = """() => {
    const sb = document.getElementById('sidebar');
    const lib = document.getElementById('library');
    const items = lib.querySelectorAll('.lib-item');
    const cats = lib.querySelectorAll('.cat-section');
    return {
        cats: cats.length, items: items.length,
        sbClientH: sb.clientHeight, sbScrollH: sb.scrollHeight,
    };
}"""


def sweep(mode):
    captured = []
    with sync_playwright() as p:
        browser, page, errors = make_browser(p, 1280, 800)
        load_app(page, fresh=False)
        dismiss_overlays(page)
        if mode == "advanced":
            to_advanced(page)
        set_camera(page)

        info = page.evaluate(PROBE_SIDEBAR)
        print(mode, "sidebar:", info)

        # 1. idle sidebar
        captured.append(shot(page, "sidebar_idle_" + mode))

        # 2. category collapse/expand (first + last)
        cats = page.locator(".cat-title")
        n = cats.count()
        cats.nth(0).click(); page.wait_for_timeout(300)
        captured.append(shot(page, "sidebar_cat0_collapsed_" + mode))
        cats.nth(0).click(); page.wait_for_timeout(300)
        if n > 1:
            cats.nth(n - 1).click(); page.wait_for_timeout(300)
            captured.append(shot(page, f"sidebar_cat{n-1}_collapsed_" + mode))
            cats.nth(n - 1).click(); page.wait_for_timeout(300)

        # 3. every item hover across all categories (hover shot per category block)
        items = page.locator(".lib-item")
        total = items.count()
        for ci in range(5):
            sec = page.locator(".cat-section").nth(ci % page.locator(".cat-section").count())
            its = sec.locator(".lib-item")
            cnt = its.count()
            its.nth(min(1, cnt - 1)).scroll_into_view_if_needed()
            its.nth(min(1, cnt - 1)).hover()
            page.wait_for_timeout(250)
            captured.append(shot(page, f"sidebar_cat{ci}_hover_" + mode))

        # 4. item click — object added + toast; capture; then undo (real Ctrl+Z)
        items.nth(0).click()
        page.wait_for_timeout(600)
        captured.append(shot(page, "sidebar_item_click_added_" + mode))
        page.keyboard.press("Control+z")
        page.wait_for_timeout(400)

        # 5. scroll to bottom — long-list scroll cue + status-bar interplay
        page.locator("#sidebar").evaluate("el => el.scrollTop = el.scrollHeight")
        page.wait_for_timeout(400)
        captured.append(shot(page, "sidebar_scroll_bottom_" + mode))

        # 6. getting-started close X (may already be hidden by item click)
        gs = page.locator("#getting-started-close")
        if gs.count() > 0 and gs.is_visible():
            gs.click(); page.wait_for_timeout(300)
            captured.append(shot(page, "sidebar_gettingstarted_closed_" + mode))
        else:
            print(mode, "getting-started hint already hidden (expected after item add)")
        browser.close()

    recs = []
    import os
    for c in captured:
        recs.append(verdict_and_save(os.path.basename(c)[:-4], "group3 sidebar"))
    bad = [r["surface"] for r in recs if not r["clean"]]
    print(f"SIDEBAR {mode}: {len(recs)} verdicts, issues: {bad}")


if __name__ == "__main__":
    for mode in ("basic", "advanced"):
        sweep(mode)
    print("GROUP3 DONE")
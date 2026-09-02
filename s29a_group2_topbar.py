"""S29 Agent 1 — Group 2: topbar sweep (mode-aware).

Basic mode shows a subset of tb-btns (Export/Season/Growth/Permit/Templates/
Label/Print/Gallery/Timelapse/Socialcard are Advanced-only). We click what
exists in each mode, capture every topbar opener result + mode toggle both
ways + view toggle both ways. Resumable via existing shots.
"""
import sys
sys.path.insert(0, "/root/byd29-audit-core")
from s29a_common import (SHOTS, dismiss_overlays, load_app, make_browser,
                        set_camera, shot, to_advanced, to_basic, verdict_and_save)
from playwright.sync_api import sync_playwright

BASIC_OPENERS = [
    ("btn-undo", "topbar_undo_disabled"),
    ("btn-save", "topbar_save_open"),
    ("btn-load", "topbar_load_open"),
    ("btn-screenshot", "topbar_screenshot_toast"),
    ("btn-shortcuts", "topbar_shortcuts_open"),
    ("btn-help", "topbar_help_open"),
    ("btn-layers", "topbar_layers_open"),
    ("btn-cost", "topbar_cost_open"),
    ("btn-walk", "topbar_walk_entry"),
    ("btn-gallery", "topbar_gallery_open"),
    ("btn-timelapse", "topbar_timelapse_open"),
    ("btn-socialcard", "topbar_socialcard_open"),
    ("btn-share", "topbar_share_open"),
    ("btn-label", "topbar_label_open"),
    ("btn-print", "topbar_print_open"),
]
ADV_OPENERS = [
    ("btn-export", "topbar_export_open"),
    ("btn-season", "topbar_season_open"),
    ("btn-growth", "topbar_growth_open"),
    ("btn-permit", "topbar_permit_open"),
    ("btn-templates", "topbar_templates_open"),
    ("btn-redo", "topbar_redo_disabled"),
]


def sweep(mode):
    note = mode
    openers = BASIC_OPENERS if mode == "basic" else ADV_OPENERS
    captured = []
    with sync_playwright() as p:
        browser, page, errors = make_browser(p, 1280, 800)
        load_app(page, fresh=False)
        dismiss_overlays(page)
        if mode == "advanced":
            to_advanced(page)
        set_camera(page)
        n = shot(page, "topbar_idle_" + note)
        captured.append(n)

        if mode == "basic":
            for data_mode, label in (("advanced", "topbar_mode_toggled_advanced"),
                                     ("basic", "topbar_mode_toggled_back_basic")):
                page.locator(f"#mode-toggle button[data-mode='{data_mode}']").click()
                page.wait_for_timeout(700)
                if data_mode == "basic":
                    captured.append(shot(page, label))

        # View toggle both ways
        page.locator("#view-toggle button[data-view='2d']").click()
        page.wait_for_timeout(900)
        captured.append(shot(page, "topbar_view_2d_" + note))
        page.locator("#view-toggle button[data-view='3d']").click()
        page.wait_for_timeout(900)
        captured.append(shot(page, "topbar_view_back_3d_" + note))

        for btn, name in openers:
            base = name + "_" + note
            if any(c.endswith(base + ".png") for c in captured):
                continue
            loc = page.locator("#" + btn)
            if loc.count() == 0:
                print("MISSING-IN-MODE", btn, mode)
                continue
            disabled = page.evaluate(f"() => document.getElementById('{btn}').disabled")
            if disabled:
                print("DISABLED (no click):", btn)
                captured.append(shot(page, base))
                continue
            try:
                loc.click(timeout=8000)
                page.wait_for_timeout(700)
                captured.append(shot(page, base))
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
            except Exception as e:
                print("OPENER-ERR", btn, str(e)[:120])
        browser.close()

    recs = []
    for c in captured:
        import os
        recs.append(verdict_and_save(os.path.basename(c)[:-4], "group2 topbar"))
    bad = [r["surface"] for r in recs if not r["clean"]]
    print(f"TOPBAR {mode}: {len(recs)} verdicts, issues: {bad}")


if __name__ == "__main__":
    import sys as _s
    only = _s.argv[1] if len(_s.argv) > 1 else "both"
    if only in ("basic", "both"):
        sweep("basic")
    if only in ("advanced", "both"):
        sweep("advanced")
    print("GROUP2 DONE")
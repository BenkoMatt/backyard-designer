#!/usr/bin/env python3
"""S29 Agent 3 Phase 1: modal sweep at 1280x800 (Advanced mode).

Surfaces: help open + scrolled-bottom + scrolled-back, shortcuts via 4 openers
(? / F1 / topbar btn / help-modal link), share, templates, gallery, label-edit,
cmd palette (Ctrl+K), print preview. Each gets a real-click capture + vision verdict
+ DOM overflow probe. Vision verdicts happen in this same run (sequential).
"""
import json
import sys
import time

sys.path.insert(0, "/root/byd29-audit-modals")
from playwright.sync_api import sync_playwright
from s29a_common import (URL, SHOTS, capture, is_clean, load_app, make_page,
                         overlay_probe, shot_path, sidecar, vision_qa)

FINDINGS = []


def judge(page, name, label):
    path = shot_path(name)
    page.screenshot(path=path)
    verdict = vision_qa(path)
    probe = overlay_probe(page)
    dirty_extra = ""
    if probe["overflow"]:
        dirty_extra = json.dumps(probe["overflow"])[:300]
    capture(page, name, label, verdict, dirty_extra)
    FINDINGS.append({"surface": name, "label": label, "verdict": verdict,
                     "probe": probe["overflow"], "clean": is_clean(verdict)})
    return is_clean(verdict)


def main():
    with sync_playwright() as p:
        browser, page, errors = make_page(p, 1280, 800)
        load_app(page)
        # Advanced mode so all modals are reachable
        page.locator("#mode-toggle button[data-mode='advanced']").click()
        page.wait_for_timeout(700)

        # ---- help modal: topbar opener ----
        page.click("#btn-help")
        page.wait_for_timeout(600)
        judge(page, "help_open_1280", "Help modal open (topbar)")

        # scroll to bottom via real wheel events on the help panel
        panel = page.locator(".help-panel")
        for _ in range(14):
            panel.hover()
            page.mouse.wheel(0, 400)
            page.wait_for_timeout(60)
        page.wait_for_timeout(400)
        judge(page, "help_scrolled_bottom_1280", "Help modal scrolled to bottom")

        # scroll back to top
        for _ in range(14):
            page.mouse.wheel(0, -400)
            page.wait_for_timeout(60)
        page.wait_for_timeout(400)
        judge(page, "help_scrolled_back_1280", "Help modal scrolled back to top")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # ---- shortcuts: opener 1 = ? key ----
        page.keyboard.press("Shift+Slash")  # ?
        page.wait_for_timeout(600)
        judge(page, "shortcuts_qkey_1280", "Shortcuts via ? key")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # opener 2 = F1
        page.keyboard.press("F1")
        page.wait_for_timeout(600)
        judge(page, "shortcuts_f1_1280", "Shortcuts via F1")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # opener 3 = topbar Shortcuts button
        page.click("#btn-shortcuts")
        page.wait_for_timeout(600)
        judge(page, "shortcuts_btn_1280", "Shortcuts via topbar button")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # opener 4 = help modal link
        page.click("#btn-help")
        page.wait_for_timeout(500)
        page.click("#help-open-shortcuts")
        page.wait_for_timeout(600)
        judge(page, "shortcuts_helplink_1280", "Shortcuts via help-modal link")
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)

        # ---- share ----
        page.click("#btn-share")
        page.wait_for_timeout(800)  # QR code render
        judge(page, "share_open_1280", "Share modal with QR")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # ---- templates ----
        page.click("#btn-templates")
        page.wait_for_timeout(600)
        judge(page, "templates_open_1280", "Templates modal")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # ---- gallery ----
        page.click("#btn-gallery")
        page.wait_for_timeout(600)
        judge(page, "gallery_open_1280", "Gallery modal")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # ---- label-edit: add label via topbar ----
        page.click("#btn-label")
        page.wait_for_timeout(600)
        judge(page, "label_edit_open_1280", "Label edit modal")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # ---- cmd palette ----
        page.keyboard.press("Control+k")
        page.wait_for_timeout(600)
        judge(page, "cmd_palette_open_1280", "Command palette Ctrl+K")
        # type a query to see filtered results
        page.keyboard.type("terrain")
        page.wait_for_timeout(500)
        judge(page, "cmd_palette_typed_1280", "Command palette query typed")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # ---- print preview ----
        page.click("#btn-print")
        page.wait_for_timeout(900)
        judge(page, "print_preview_1280", "Print preview overlay")
        page.click("#print-cancel-btn")
        page.wait_for_timeout(300)

        # page errors?
        print("PAGE_ERRORS:", errors[:5])

    with open(f"{SHOTS}/phase1_results.json", "w") as f:
        json.dump(FINDINGS, f, indent=1)
    dirty = [f for f in FINDINGS if not f["clean"]]
    print(f"\n=== Phase 1 done: {len(FINDINGS)} shots, {len(dirty)} dirty ===")
    for d in dirty:
        print("DIRTY:", d["surface"], "::", d["verdict"][:200].replace("\n", " | "),
              "PROBE:", json.dumps(d["probe"])[:200])


if __name__ == "__main__":
    main()
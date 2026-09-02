"""S29 Agent 1 — Group 1: first-run wizard (both steps) + welcome prompt.

Real CDP clicks through the wizard: step 1 (shape select, hover), step 2
(dimension quick-sizes, back/forward), finish, then the welcome prompt that
appears after the wizard closes. Advanced mode is exercised at the end
(wizard shows identically before any mode is chosen, but the welcome prompt
sits on top of the Basic-mode workspace; we capture it once more after
toggling Advanced to check dock-tab bleedthrough).
"""
import json
import sys
sys.path.insert(0, "/root/byd29-audit-core")
from s29a_common import (SHOTS, append_handoff, dismiss_overlays, is_clean,
                         load_app, make_browser, rect, shot, to_advanced,
                         verdict_and_save)
from playwright.sync_api import sync_playwright

FINDINGS = []


def run(mode_note):
    with sync_playwright() as p:
        browser, page, errors = make_browser(p, 1280, 800)
        load_app(page, fresh=True)

        # --- Step 1: wizard initial state ---------------------------------
        s1 = shot(page, "wizard_step1_" + mode_note, )
        shot(page, "wizard_step1_" + mode_note)

        # Hover a shape card (real pointer) — selected state check
        page.locator(".shape-card[data-shape='L']").hover()
        page.wait_for_timeout(300)
        page.locator(".shape-card[data-shape='L']").click()
        page.wait_for_timeout(300)
        shot(page, "wizard_step1_lshape_" + mode_note)

        # Skip button visible on step 1?
        r = rect(page, "#wizard-skip")
        print("wizard-skip rect:", r)

        # --- Step 2: dimensions ------------------------------------------
        page.locator("#wizard-next").click()
        page.wait_for_timeout(500)
        shot(page, "wizard_step2_" + mode_note)

        # Type custom dims (real keyboard)
        w = page.locator("#wiz-width")
        w.click()
        w.press("Control+a")
        w.type("60")
        d = page.locator("#wiz-depth")
        d.click()
        d.press("Control+a")
        d.type("110")
        page.wait_for_timeout(200)
        shot(page, "wizard_step2_typed_" + mode_note)

        # Back then forward (state persistence)
        page.locator("#wizard-back").click()
        page.wait_for_timeout(400)
        page.locator("#wizard-next").click()
        page.wait_for_timeout(400)
        shot(page, "wizard_step2_returned_" + mode_note)

        # --- Finish --------------------------------------------------------
        page.locator("#wizard-finish").click()
        page.wait_for_timeout(1000)
        # Welcome prompt should appear (observer fires 600ms after wizard hides)
        shot(page, "welcome_prompt_" + mode_note)

        # Welcome prompt quick actions hover
        page.locator("#wp-template").hover()
        page.wait_for_timeout(250)
        shot(page, "welcome_prompt_hover_" + mode_note)

        if mode_note == "advanced":
            # Dismiss welcome, toggle Advanced, reopen? Welcome shows once —
            # instead capture the Advanced workspace with welcome visible.
            pass
        # Close welcome via "Start from scratch" (real click)
        page.locator("#wp-scratch").click()
        page.wait_for_timeout(900)
        shot(page, "welcome_prompt_after_scratch_" + mode_note)

        if errors:
            print("PAGEERRORS:", errors[:5])
        browser.close()

    names = [n for n in [
        "wizard_step1_" + mode_note,
        "wizard_step1_lshape_" + mode_note,
        "wizard_step2_" + mode_note,
        "wizard_step2_typed_" + mode_note,
        "wizard_step2_returned_" + mode_note,
        "welcome_prompt_" + mode_note,
        "welcome_prompt_hover_" + mode_note,
        "welcome_prompt_after_scratch_" + mode_note,
    ]]
    for n in names:
        rec = verdict_and_save(n, "group1 wizard/welcome " + mode_note)
        FINDINGS.append({
            "surface": "first-run:" + n,
            "verdict": "CLEAN" if rec["clean"] else "NOT-CLEAN",
            "issue": "" if rec["clean"] else rec["verdict"][:300],
            "fixed_y_n": "",
            "commit": "",
        })


run("basic")

# Advanced-mode pass: wizard is shown BEFORE any mode; then after finish we
# toggle Advanced and shoot the workspace + re-shoot welcome if re-triggered.
with sync_playwright() as p:
    browser, page, errors = make_browser(p, 1280, 800)
    load_app(page, fresh=True)
    page.locator("#wizard-next").click(); page.wait_for_timeout(400)
    page.locator("#wizard-finish").click(); page.wait_for_timeout(900)
    page.locator("#wp-remind-later").click()
    page.wait_for_timeout(600)
    to_advanced(page)
    page.wait_for_timeout(600)
    shot(page, "workspace_after_wizard_advanced")
    browser.close()
rec = verdict_and_save("workspace_after_wizard_advanced", "group1 advanced workspace post-wizard")
FINDINGS.append({"surface": "first-run:workspace_after_wizard_advanced",
                 "verdict": "CLEAN" if rec["clean"] else "NOT-CLEAN",
                 "issue": "" if rec["clean"] else rec["verdict"][:300],
                 "fixed_y_n": "", "commit": ""})

for f in FINDINGS:
    append_handoff(["```json\n" + json.dumps(f) + "\n```" if False else json.dumps(f)])
import json
print("GROUP1 DONE", len(FINDINGS), "surfaces")
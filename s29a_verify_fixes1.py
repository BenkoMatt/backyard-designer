"""S29 Agent 1 — verify fixes S29-V01..V03 + wizard-skip position (read-only + shots)."""
import json
import sys
sys.path.insert(0, "/root/byd29-audit-core")
from s29a_common import (load_app, make_browser, set_camera, shot, verdict_and_save, SHOTS)
from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser, page, errors = make_browser(p, 1280, 800)
    load_app(page, fresh=True)

    # wizard step 1 with skip now bottom-left
    r = page.evaluate("""() => {
        const skip = document.getElementById('wizard-skip').getBoundingClientRect();
        const sun = document.getElementById('sun-btn').getBoundingClientRect();
        const scale = document.getElementById('scale-bar').getBoundingClientRect();
        const tb = document.getElementById('bottom-left-toolbar').getBoundingClientRect();
        const ov = (a,b) => Math.max(0, Math.min(a.right,b.right)-Math.max(a.left,b.left)) *
                          Math.max(0, Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
        return {skip: {x:skip.x, y:skip.y, right:skip.right, bottom:skip.bottom},
                sun_ov: ov(skip,sun), scale_ov: ov(skip,scale), tb_ov: ov(skip,tb)};
    }""")
    print("skip rect:", r)
    shot(page, "FIX_wizard_step1")

    # finish wizard -> welcome: check toast/hint suppressed
    page.locator("#wizard-next").click(); page.wait_for_timeout(400)
    page.locator("#wizard-finish").click(); page.wait_for_timeout(1500)
    probe = page.evaluate("""() => {
        const t = document.getElementById('toast');
        const h = document.getElementById('context-hint');
        const wp = document.getElementById('welcome-prompt');
        return {wp_visible: wp.classList.contains('visible'),
                toast_visible: t.classList.contains('visible'),
                hint_visible: h.classList.contains('visible')};
    }""")
    print("welcome state:", probe)
    shot(page, "FIX_welcome_prompt")

    # FPS item hidden initially?
    fps = page.evaluate("() => document.getElementById('sb-fps-item').hidden")
    print("fps item hidden:", fps)

    # after closing welcome + some frames, FPS should appear with a value
    page.locator("#wp-scratch").click(); page.wait_for_timeout(1000)
    page.mouse.move(640, 400); page.mouse.wheel(0, -200)  # force renders
    page.wait_for_timeout(2500)
    fps2 = page.evaluate("() => ({hidden: document.getElementById('sb-fps-item').hidden, val: document.getElementById('sb-fps').textContent})")
    print("fps after activity:", fps2)
    shot(page, "FIX_workspace_after_welcome")
    print("ERRORS:", errors[:5])
    browser.close()

for n in ("FIX_wizard_step1", "FIX_welcome_prompt", "FIX_workspace_after_welcome"):
    verdict_and_save(n, "fix verification", force=True)
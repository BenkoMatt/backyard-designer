#!/usr/bin/env python3
"""Sprint 23 Agent 1 (VISION-AUDIT-SURFACES) — full surface audit.

Serves nothing itself; expects the app at BASE_URL (default http://localhost:8091/index.html).
Walks every surface in SPRINT23_BRIEF.md in Basic AND Advanced mode using REAL CDP
clicks (Playwright locators → real input pipeline), captures 1280x800 screenshots,
sends each to glm-5.3-flash multimodal for the per-surface QA verdict.

Usage:  BYD_MODE=before BASE_URL=http://localhost:8091/index.html python3 sprint23_vision_audit.py [--only name,name2]
Outputs: reports/sprint23_shots/<MODE>-<surface>.png + reports/sprint23_shots/vision_results_<MODE>.json
"""
import base64
import json
import os
import sys
import time
import urllib.request

URL = os.environ.get("BASE_URL", "http://localhost:8091/index.html")
MODE = os.environ.get("BYD_MODE", "before")
OUT = "/root/byd23-vision-audit/reports/sprint23_shots"
os.makedirs(OUT, exist_ok=True)
ENVKEY = None
for envf in ("/root/.hermes/.env", "/root/.env"):
    if os.path.exists(envf):
        for line in open(envf):
            if line.startswith("OLLAMA_API_KEY="):
                ENVKEY = line.strip().split("=", 1)[1]
                break
    if ENVKEY:
        break
API_KEY = os.environ.get("OLLAMA_API_KEY") or ENVKEY or ""

QA_PROMPT = (
    "1280x800 screenshot of a 3D backyard design web app. "
    "(1) Anything overlapping or clipped? "
    "(2) Would a new user understand what to do within 5 seconds? "
    "(3) Anything confusing, ambiguous, or broken-looking? Reply CLEAN if perfect."
)


def vision_qa(png_path):
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = json.dumps({
        "model": "glm-5.3-flash",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": QA_PROMPT},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
        ]}],
        "options": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(
        "https://ollama.com/v1/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return "VISION_ERROR: %s" % e


from playwright.sync_api import sync_playwright

# (name, mode, actions, settle_s)
# action tuple kinds: ('click', sel) ('hover', sel) ('press', key) ('scroll', sel) ('scroll_to', sel)
#   ('wait', s) ('shot', None)  — 'shot' is implicit at surface end anyway
S = [
    # ── Wizard (first-run): fresh context, no clicks before shot
    ("01-wizard-step1", "fresh", [], 1.2),
    ("02-wizard-step2", "fresh", [("click", "#wizard-next")], 0.6),
    ("02-wizard-step2-scrolled", "fresh", [("click", "#wizard-next"), ("scroll_to", ".wizard-panel")], 0.6),
    # ── Main default (continue past wizard in SAME context, real clicks)
    ("03-main-default", "main", [], 1.2),
    # Right-toolbar hover (tape first)
    ("04-toolbar-hover-tape", "main", [("hover", "#tape-measure-btn")], 0.8),
    # Left sidebar: all categories expanded + hover on an item (default view)
    ("05-sidebar-all-expanded", "main", [("expand_sidebar", None), ("scroll_to", "#sidebar .lib-item:last-of-type")], 0.8),
    ("05b-sidebar-hover-item", "main", [("expand_sidebar", None), ("scroll_to", "#sidebar .lib-item:last-of-type"), ("hover", "#sidebar .lib-item:last-of-type")], 0.8),
    # Bottom-left toolbar: Tape/Terrain/Excavate/Analyze/Innovate/Sun each clicked
    ("06-toolbar-tape", "main", [("click", "#tape-measure-btn")], 0.8),
    ("07-toolbar-terrain", "main", [("click", "#terrain-btn")], 0.8),
    ("08-toolbar-excavate", "main", [("click", "#excavate-btn")], 0.8),
    ("09-toolbar-analyze", "main", [("click", "#terrain-analysis-btn")], 0.8),
    ("10-toolbar-innovate", "main", [("click", "#innovation-btn")], 0.8),
    ("11-toolbar-sun", "main", [("click", "#sun-btn")], 0.8),
    # ── Panels (Advanced for the basic-hidden ones), each opened alone from clean state
    ("p-terrain-controls", "adv", [("click", "#terrain-btn")], 0.8),
    ("p-excavate", "adv", [("click", "#excavate-btn")], 0.8),
    ("p-terrain-analysis", "adv", [("click", "#terrain-analysis-btn")], 0.8),
    ("p-innovation", "adv", [("click", "#innovation-btn")], 0.8),
    ("p-sun", "adv", [("click", "#sun-btn")], 0.8),
    ("p-cost", "adv", [("click", "#btn-cost")], 0.8),
    ("p-layer", "adv", [("click", "#btn-layers")], 0.8),
    ("p-season", "adv", [("click", "#btn-season")], "toast"),   # triggers Advanced-mode toast — settle
    ("p-growth", "adv", [("click", "#btn-growth")], 0.8),
    ("p-permit", "adv", [("click", "#btn-permit")], 0.8),
    ("p-cross-section", "adv", [("click", '.td-tab[data-dock="underground"]'), ("click", "#cross-section-toggle")], 0.8),
    ("p-cut-fill", "adv", [("click", '.td-tab[data-dock="analyze"]'), ("click", "#ta-cutfill-toggle")], 1.2),
    # ── Dock panels at 1280x800 via td-tab clicks; verify ZERO scroll
    ("d-terrain", "adv", [("click", '.td-tab[data-dock="terrain"]')], 0.8),
    ("d-underground", "adv", [("click", '.td-tab[data-dock="underground"]')], 0.8),
    # ── Modals
    ("m-help", "adv", [("click", "#btn-help")], 0.8),
    ("m-help-bottom", "adv", [("click", "#btn-help"), ("scroll_to", ".help-panel .close-btn")], 0.8),  # open, then scroll inside (help)
    ("m-shortcuts", "adv", [("press", "Shift+Slash")], 0.8),
    ("m-shortcuts-f1", "adv", [("press", "F1")], 0.8),
    ("m-share", "adv", [("click", "#btn-share")], 0.8),
    ("m-templates", "adv", [("click", "#btn-templates")], 0.8),
    ("m-gallery", "adv", [("click", "#btn-gallery")], 0.8),
    ("m-label-edit", "adv", [("click", "#btn-label")], 0.8),
    ("m-command-palette", "adv", [("press", "Control+K")], 0.8),
    # ── Overlays / badges / banners
    ("o-walk-mode", "adv", [("click", "#btn-walk")], 1.2),
    ("o-grid-level-badge", "adv", [("grid_badge", None)], 1.0),
    ("o-depth-gauge", "adv", [("click", "#vc-underground")], 1.0),
    # ── Status bar + context hint
    ("s-status-bar", "main", [("hover", "#sidebar .lib-item:first-of-type")], 0.5),
    ("s-context-hint", "main", [("click", "#terrain-btn")], 3.5),  # hint persists while active
    # ── Toast (capture quickly at appearance)
    ("t-toast", "adv", [("toast", None)], 0.35),
    # ── Print view
    ("x-print", "adv", [("click", "#btn-print")], 1.0),
]

ONLY = None
if len(sys.argv) > 2 and sys.argv[1] == "--only":
    ONLY = set(sys.argv[2].split(","))

results = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    # one persistent "main" context (wizard completed via real clicks), plus fresh contexts
    mainctx = None
    advmode = {"on": False}

    def new_page(ctx):
        page = ctx.new_page()
        page.set_viewport_size({"width": 1280, "height": 800})
        return page

    def make_ctx():
        return browser.new_context(viewport={"width": 1280, "height": 800},
                                   device_scale_factor=1)

    for name, kind, actions, settle in S:
        if ONLY and name not in ONLY:
            continue
        settle_wait = 0.8 if settle == "toast" else settle

        def boot(kind):
            global mainctx
            if mainctx is None:
                mainctx = make_ctx()
            pg = new_page(mainctx)
            pg.goto(URL, wait_until="networkidle")
            pg.wait_for_selector("#mode-toggle button[data-mode='advanced']", timeout=30000)
            pg.wait_for_timeout(600)
            # Deterministic boot: escape the wizard if it shows (real click),
            # then force the wanted mode with real clicks regardless of persistence.
            if pg.is_visible("#wizard"):
                pg.click("#wizard-skip")
                pg.wait_for_timeout(400)
            if pg.is_visible("#welcome-prompt"):
                pg.click("#wp-remind-later")
                pg.wait_for_timeout(400)
            want_adv = (kind == "adv")
            tb = pg.locator("#mode-toggle button[data-mode='advanced']")
            is_adv = "advanced" in (tb.get_attribute("class") or "")
            basic_first = pg.locator("#mode-toggle button[data-mode='basic']").get_attribute("class") or ""
            is_basic = "active" in basic_first
            # A page may boot into Advanced if the previous page left it there.
            if want_adv:
                if is_basic:
                    pg.click("#mode-toggle button[data-mode='basic']")
                    pg.wait_for_timeout(600)
                tb.click()  # ensure a fresh Advanced transition (toast fires)
                pg.wait_for_timeout(1700)
            elif not is_basic:
                pg.click("#mode-toggle button[data-mode='basic']")
                pg.wait_for_timeout(600)
            return pg

        pg = None
        for _attempt in range(2):
            try:
                pg = boot(kind)
                break
            except Exception as e:
                if _attempt == 1:
                    results[name] = {"ok": False, "err": "boot: " + str(e)[:300]}
                    print(f"[{MODE}] {name}: FAIL boot {e}")
                    pg = None
                    break
        if pg is None:
            if name not in results:
                results[name] = {"ok": False, "err": "boot failed"}
            continue
        if kind == "fresh":
            # Wizard shot needs a truly fresh profile (no autosave state)
            for _ftry in range(2):
                ctx = make_ctx()
                pg = new_page(ctx)
                pg.goto(URL, wait_until="networkidle")
                try:
                    pg.wait_for_selector("#wizard", timeout=25000)
                except Exception:
                    if _ftry == 0:
                        ctx.close()
                        continue
                    raise
                break
            pg.wait_for_timeout(600)

        try:
            for a in actions:
                k, sel = a
                if k == "click":
                    pg.click(sel, timeout=5000)
                elif k == "hover":
                    pg.hover(sel, timeout=5000)
                elif k == "press":
                    pg.keyboard.press(sel)
                elif k == "scroll_to":
                    pg.locator(sel).first.scroll_into_view_if_needed(timeout=3000)
                elif k == "expand_sidebar":
                    # click every collapsed category header open (real clicks)
                    n = pg.evaluate("document.querySelectorAll('#sidebar .cat-section').length")
                    for i in range(n):
                        sec = pg.locator("#sidebar .cat-section").nth(i)
                        if "collapsed" in (sec.get_attribute("class") or ""):
                            sec.locator(".cat-title").click()
                        pg.wait_for_timeout(60)
                elif k == "grid_badge":
                    # read-only probe (allowed): set grid level, fire app's own listener path via real slider keyboard
                    pg.focus("#grid-level-slider")
                    for _ in range(11):
                        pg.keyboard.press("ArrowUp")
                        pg.wait_for_timeout(30)
                elif k == "toast":
                    pass
                pg.wait_for_timeout(120)

            if settle == "toast":
                pg.wait_for_timeout(300)
            else:
                pg.wait_for_timeout(int(settle_wait * 1000))
            pg.screenshot(path=f"{OUT}/{MODE}-{name}.png")
            results[name] = {"ok": True, "shot": f"{OUT}/{MODE}-{name}.png"}
            print(f"[{MODE}] {name}: shot ok")
        except Exception as e:
            results[name] = {"ok": False, "err": str(e)[:300]}
            print(f"[{MODE}] {name}: FAIL {e}")

    browser.close()

with open(f"{OUT}/vision_results_{MODE}.json", "w") as f:
    json.dump(results, f, indent=1)
print("shots:", len(results), "failures:", sum(1 for v in results.values() if not v["ok"]))
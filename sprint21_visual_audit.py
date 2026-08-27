#!/usr/bin/env python3
"""Sprint 21 Agent 3 — Visual Audit harness.

Opens every panel/modal/dock in Basic and Advanced mode via REAL CDP clicks
(Playwright mouse / element.click through the CDP input domain — never
page.evaluate driving app functions), captures a 1280x800 screenshot per
surface plus DOM geometry metrics used to detect scroll-orphaned controls,
overlaps and off-viewport elements.

Outputs: reports/sprint21_shots/{before,after}/<surface>.png  (+ .json metrics)
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

URL = os.environ.get("BYD_URL", "http://localhost:9099/index.html")
MODE = os.environ.get("BYD_MODE", "before")          # before | after
OUT = f"/root/byd21-visual-audit/reports/sprint21_shots/{MODE}"
os.makedirs(OUT, exist_ok=True)

results = {}
issues = []

# surface -> (open_steps, close_steps). Every step is ("click", selector)
# Real CDP input: page.click / tab clicks are genuine hit-tested events.
SURFACES = [
    # --- modals first, each closed with Escape so nothing blocks later clicks ---
    ("help-modal", [("click", "#btn-help")], [("press", "Escape")]),
    ("templates-modal", [("click", "#btn-templates")], [("press", "Escape")]),
    ("share-modal", [("click", "#btn-share")], [("press", "Escape")]),
    ("command-palette", [("press", "Control+KeyK")], [("press", "Escape")]),
    # --- right stack ---
    ("cost-panel", [("click", "#btn-cost")], None),
    ("layer-panel", [("click", "#btn-layers")], None),
    ("season-panel", [("click", "#btn-season")], None),
    ("growth-panel", [("click", "#btn-growth")], None),
    ("permit-panel", [("click", "#btn-permit")], None),
]

CTX = ("context-menu", [("rclick", "#viewport")], None)


def log(msg):
    print(msg, flush=True)


def measure_scroll(page, selector):
    """Detect scroll-orphaned content inside a scrollable container."""
    return page.evaluate(
        """(sel) => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const cs = getComputedStyle(el);
            const r = el.getBoundingClientRect();
            return {
                scrollH: el.scrollHeight, clientH: el.clientHeight,
                scrollW: el.scrollWidth, clientW: el.clientWidth,
                rect: {x: r.x, y: r.y, w: r.width, h: r.height},
                overflowY: cs.overflowY, overflowX: cs.overflowX,
            };
        }""",
        selector,
    )


def offscreen_controls(page, panel_sel):
    """Controls inside panel that extend past the 1280x800 viewport."""
    return page.evaluate(
        """([sel, vw, vh]) => {
            const panel = document.querySelector(sel);
            if (!panel) return [];
            const bad = [];
            const ctrls = panel.querySelectorAll(
                'button, input, select, label, a[href], [role="button"], [role="switch"], [role="tab"]');
            for (const c of ctrls) {
                const cs = getComputedStyle(c);
                if (cs.display === 'none' || cs.visibility === 'hidden') continue;
                const r = c.getBoundingClientRect();
                if (r.width === 0 && r.height === 0) continue;
                if (r.bottom > vh + 1 || r.right > vw + 1 || r.top < -1 || r.left < -1) {
                    bad.push({
                        tag: c.tagName, id: c.id || null, text: (c.textContent||'').trim().slice(0,40),
                        rect: {t: Math.round(r.top), b: Math.round(r.bottom), l: Math.round(r.left), r: Math.round(r.right)},
                    });
                }
            }
            return bad;
        }""",
        [panel_sel, 1280, 800],
    )


def panel_controls(page, panel_sel):
    """Count visible interactive controls + whether the last one is below fold."""
    return page.evaluate(
        """(sel) => {
            const panel = document.querySelector(sel);
            if (!panel) return null;
            const pr = panel.getBoundingClientRect();
            let vis = 0, below = 0, last = null;
            const ctrls = panel.querySelectorAll(
                'button, input, select, [role="button"], [role="switch"], [role="tab"]');
            for (const c of ctrls) {
                const cs = getComputedStyle(c);
                if (cs.display === 'none' || cs.visibility === 'hidden') continue;
                const r = c.getBoundingClientRect();
                if (r.width === 0 && r.height === 0) continue;
                vis++;
                if (r.bottom > window.innerHeight - 2) { below++; last = c.id || (c.textContent||'').trim().slice(0,30); }
            }
            return {panelBottom: Math.round(pr.bottom), controls: vis, belowFold: below, lastBelow: last};
        }""",
        panel_sel,
    )


def open_app(page):
    page.goto(URL, wait_until="load", timeout=30000)
    page.wait_for_timeout(600)
    # pass the wizard with real clicks (defaults are fine)
    nxt = page.locator("#wizard-next")
    if nxt.count() and nxt.is_visible():
        nxt.click()
        page.wait_for_timeout(250)
        fin = page.locator("#wizard-finish")
        if fin.count() and fin.is_visible():
            fin.click()
        page.wait_for_timeout(1200)
    # dismiss the welcome prompt if it appeared (real click)
    wp = page.locator("#wp-scratch")
    if wp.count() and wp.is_visible():
        wp.click()
        page.wait_for_timeout(600)


def set_mode(page, mode):
    """Click the Basic/Advanced toggle buttons with real CDP input."""
    btn = page.locator(f'#mode-toggle button[data-mode="{mode}"]')
    if btn.count() and btn.is_visible():
        btn.click()
        page.wait_for_timeout(250)
        return True
    return False


def run_surface(page, name, opens, closes, tab):
    entry = {"open_ok": False, "shot": None}
    try:
        for step in opens:
            if step[0] == "click":
                loc = page.locator(step[1]).first
                loc.scroll_into_view_if_needed(timeout=2000)
                loc.click(timeout=4000, force=True)
            elif step[0] == "rclick":
                el = page.locator(step[1]).first
                box = el.bounding_box()
                page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, button="right")
            elif step[0] == "press":
                page.keyboard.press(step[1].replace("Control+KeyK", "Control+K"))
            page.wait_for_timeout(350)

        page.wait_for_timeout(350)
        page.screenshot(path=f"{OUT}/{name}.png")
        entry["shot"] = f"{OUT}/{name}.png"
        entry["open_ok"] = True

        # metrics against the most relevant scroll container
        base_name = name.split('-', 1)[1] if name.startswith(('basic-', 'advanced-')) else name
        sel = PANEL_SEL.get(base_name) or PANEL_SEL.get(name)
        if sel:
            entry["scroll"] = measure_scroll(page, sel)
            entry["offscreen"] = offscreen_controls(page, sel)
            entry["controls"] = panel_controls(page, sel)
        if tab:
            entry["metrics"] = page.evaluate(
                """(sel) => {
                    const el = document.querySelector(sel);
                    if (!el) return null;
                    const r = el.getBoundingClientRect();
                    return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)};
                }""",
                tab,
            )
    except Exception as e:
        entry["error"] = str(e)[:200]
        log(f"  !! {name}: {entry['error']}")
    finally:
        if closes:
            for step in closes:
                try:
                    if step[0] == "click":
                        page.click(step[1], timeout=3000)
                    elif step[0] == "press":
                        page.keyboard.press(step[1])
                    page.wait_for_timeout(250)
                except Exception:
                    pass
    results[name] = entry
    log(f"  {name}: ok={entry['open_ok']}")


PANEL_SEL = {
    "dock-terrain": "#dock-terrain-content",
    "dock-underground": "#dock-underground-content",
    "dock-analyze": "#dock-analyze-content",
    "dock-innovate": "#dock-innovate-content",
    "dock-sun": "#dock-sun-content",
    "dock-measure": "#dock-measure-content",
    "dock-experience": "#dock-experience-content",
    "excavate-panel": "#excavate-panel",
    "terrain-analysis": "#terrain-analysis-panel",
    "innovation-panel": "#innovation-panel",
    "sun-panel": "#sun-panel",
    "cost-panel": "#cost-panel",
    "layer-panel": "#layer-panel",
    "cross-section": "#cross-section-panel",
    "season-panel": "#season-panel",
    "growth-panel": "#growth-panel",
    "permit-panel": "#permit-panel",
    "help-modal": "#help-modal",
    "templates-modal": "#templates-modal",
    "share-modal": "#share-modal",
    "command-palette": "#cmd-palette",
}

MODALS = ["help-modal", "templates-modal", "share-modal"]

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu", "--use-gl=swiftshader"],
    )
    for mode in ("basic", "advanced"):
        mode_out = OUT
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        open_app(page)
        set_mode(page, mode)
        page.wait_for_timeout(300)
        log(f"=== {MODE} / {mode} ===")

        for name, opens, closes in SURFACES:
            run_surface(page, f"{mode}-{name}", opens, closes, None)

        # close right-stack panels before the dock tour
        for btn in ("#btn-permit", "#btn-growth", "#btn-season", "#btn-layers", "#btn-cost"):
            try:
                page.click(btn, timeout=1500, force=True)
                page.wait_for_timeout(150)
            except Exception:
                pass

        # docks (tool dock tabs) — one at a time
        for dock in ("terrain", "underground", "analyze", "innovate", "sun", "measure", "experience"):
            run_surface(page, f"{mode}-dock-{dock}", [( "click", f'.td-tab[data-dock="{dock}"]')], None, None)
        # close dock
        try:
            page.click(".td-tab.active", timeout=1500, force=True)
        except Exception:
            pass

        # bottom-left viewport buttons
        run_surface(page, f"{mode}-excavate-panel", [("click", "#excavate-btn")], None, None)
        # cross-section lives INSIDE the excavate panel — chain from open state
        run_surface(page, f"{mode}-cross-section", [("click", "#cross-section-toggle")], [("click", "#excavate-btn")], None)
        try:
            page.click("#excavate-btn", timeout=1500, force=True)
            page.wait_for_timeout(200)
        except Exception:
            pass
        run_surface(page, f"{mode}-terrain-analysis", [("click", "#terrain-analysis-btn")], None, None)
        try:
            page.click("#terrain-analysis-btn", timeout=1500, force=True)
        except Exception:
            pass
        run_surface(page, f"{mode}-innovation-panel", [("click", "#innovation-btn")], None, None)
        try:
            page.click("#innovation-btn", timeout=1500, force=True)
        except Exception:
            pass
        run_surface(page, f"{mode}-sun-panel", [("click", "#sun-btn")], None, None)
        try:
            page.click("#sun-btn", timeout=1500, force=True)
        except Exception:
            pass

        # context menu via right-click on the viewport
        run_surface(page, f"{mode}-context-menu", CTX[1], None, None)
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)

        page.screenshot(path=f"{OUT}/{mode}-baseline.png")

        # Basic-mode cleanliness: open an advanced-only dock, switch to basic
        if mode == "advanced":
            try:
                page.click('.td-tab[data-dock="underground"]', timeout=2000, force=True)
                page.wait_for_timeout(250)
            except Exception:
                pass
            set_mode(page, "basic")
            page.wait_for_timeout(300)
            vis = page.evaluate(
                """() => {
                    const out = [];
                    for (const el of document.querySelectorAll('.dock-panel.visible, .viewport-overlay.visible, #dock-panel-container.visible')) {
                        const cs = getComputedStyle(el);
                        const r = el.getBoundingClientRect();
                        if (cs.display !== 'none' && r.width > 0) out.push(el.id || el.className);
                    }
                    return out;
                }"""
            )
            results[f"{mode}-switch-to-basic-orphan-panels"] = vis
            page.screenshot(path=f"{OUT}/{mode}-switch-to-basic.png")

        if errors:
            results[f"{mode}-jserrors"] = errors[:5]
        page.close()
    browser.close()

with open(f"{OUT}/metrics.json", "w") as f:
    json.dump(results, f, indent=2)

log(f"done -> {OUT}/metrics.json")
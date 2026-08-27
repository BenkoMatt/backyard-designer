#!/usr/bin/env python3
"""Sprint 22 Agent 5 — Visual Consistency harness.

Opens every modal/panel/dock in Basic and Advanced mode via REAL CDP clicks,
captures 1280x800 screenshots, and records a per-surface style audit of the
interactive controls (border-radius, height, padding, font, gap, transition,
colors) so token drift and mismatched metrics can be detected between shots.

Usage: BYD_MODE=before|after BYD_URL=http://localhost:8175/index.html python3 sprint22_visual_consistency.py
Outputs: reports/sprint22_shots/<MODE>/<surface>.png (+ audit.json)
"""
import json
import os

from playwright.sync_api import sync_playwright

URL = os.environ.get("BYD_URL", "http://localhost:8175/index.html")
MODE = os.environ.get("BYD_MODE", "before")
OUT = f"/root/byd22-visual-consistency/reports/sprint22_shots/{MODE}"
os.makedirs(OUT, exist_ok=True)

results = {}

SURFACES = [
    ("help-modal", [("click", "#btn-help")], [("press", "Escape")]),
    ("templates-modal", [("click", "#btn-templates")], [("press", "Escape")]),
    ("share-modal", [("click", "#btn-share")], [("press", "Escape")]),
    ("command-palette", [("press", "Control+K")], [("press", "Escape")]),
    ("cost-panel", [("click", "#btn-cost")], None),
    ("layer-panel", [("click", "#btn-layers")], None),
    ("season-panel", [("click", "#btn-season")], None),
    ("growth-panel", [("click", "#btn-growth")], None),
    ("permit-panel", [("click", "#btn-permit")], None),
]

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

AUDIT_JS = """(sel) => {
    const root = document.querySelector(sel);
    if (!root) return null;
    const vw = window.innerWidth, vh = window.innerHeight;
    const pick = (el) => {
        const cs = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        return {
            id: el.id || null,
            cls: (el.className && typeof el.className === 'string') ? el.className.slice(0, 40) : null,
            h: Math.round(r.height), w: Math.round(r.width),
            radius: cs.borderRadius, pad: cs.padding, margin: cs.margin,
            font: cs.fontSize + '/' + cs.fontWeight + '/' + cs.fontFamily.split(',')[0],
            gap: cs.gap !== 'normal' ? cs.gap : undefined,
            transition: cs.transitionDuration !== '0s' ? cs.transitionDuration + ' ' + cs.transitionProperty.slice(0, 30) : 'none',
            bg: cs.backgroundColor, color: cs.color, border: cs.borderTopColor + ' ' + cs.borderTopWidth,
            display: cs.display,
        };
    };
    const out = {rect: (() => { const r = root.getBoundingClientRect(); return {t: Math.round(r.top), l: Math.round(r.left), w: Math.round(r.width), h: Math.round(r.height)}; })(), buttons: [], inputs: [], headers: [], gaps: []};
    const seen = new Set();
    for (const c of root.querySelectorAll('button, [role="button"], .btn')) {
        const cs = getComputedStyle(c);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        const r = c.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) continue;
        if (r.bottom > vh + 1 || r.right > vw + 1) out.offscreen = (out.offscreen || 0) + 1;
        const key = pick(c);
        const sig = JSON.stringify([key.cls, key.h, key.radius, key.pad, key.font, key.bg]);
        if (!seen.has(sig)) { seen.add(sig); out.buttons.push(key); }
    }
    seen.clear();
    for (const c of root.querySelectorAll('input, select, textarea')) {
        const cs = getComputedStyle(c);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        const r = c.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) continue;
        const key = pick(c);
        const sig = JSON.stringify([key.cls, key.h, key.radius, key.pad, key.font]);
        if (!seen.has(sig)) { seen.add(sig); out.inputs.push(key); }
    }
    seen.clear();
    for (const c of root.querySelectorAll('h1,h2,h3,h4,.panel-title,.section-title,[class*="title"]')) {
        const cs = getComputedStyle(c);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        const r = c.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) continue;
        const key = pick(c);
        const sig = JSON.stringify([key.cls, key.font, key.color]);
        if (!seen.has(sig)) { seen.add(sig); out.headers.push(key); }
    }
    // flex gap between direct children of section/row containers
    for (const c of root.querySelectorAll('div,fieldset')) {
        const cs = getComputedStyle(c);
        if (cs.display.includes('flex') && c.children.length >= 2 && c.children.length <= 12) {
            const r = c.getBoundingClientRect();
            if (r.width === 0 || r.height === 0 || r.height > 600) continue;
            out.gaps.push({cls: (typeof c.className === 'string' ? c.className.slice(0, 40) : ''), gap: cs.gap, kids: c.children.length});
        }
        if (out.gaps.length > 40) break;
    }
    return out;
}"""


def log(msg):
    print(msg, flush=True)


def audit(page, sel):
    try:
        return page.evaluate(AUDIT_JS, sel)
    except Exception as e:
        return {"error": str(e)[:120]}


def open_app(page):
    page.goto(URL, wait_until="load", timeout=30000)
    page.wait_for_timeout(600)
    nxt = page.locator("#wizard-next")
    if nxt.count() and nxt.is_visible():
        nxt.click()
        page.wait_for_timeout(250)
        fin = page.locator("#wizard-finish")
        if fin.count() and fin.is_visible():
            fin.click()
        page.wait_for_timeout(1200)
    wp = page.locator("#wp-scratch")
    if wp.count() and wp.is_visible():
        wp.click()
        page.wait_for_timeout(600)


def set_mode(page, mode):
    btn = page.locator(f'#mode-toggle button[data-mode="{mode}"]')
    if btn.count() and btn.is_visible():
        btn.click()
        page.wait_for_timeout(250)
        return True
    return False


def run_surface(page, name, opens, closes, tab=None):
    entry = {"open_ok": False}
    try:
        for step in opens:
            if step[0] == "click":
                loc = page.locator(step[1]).first
                try:
                    loc.scroll_into_view_if_needed(timeout=800)
                except Exception:
                    pass
                loc.click(timeout=2500, force=True)
            elif step[0] == "press":
                page.keyboard.press(step[1])
            page.wait_for_timeout(350)
        page.wait_for_timeout(300)
        page.screenshot(path=f"{OUT}/{name}.png")
        entry["open_ok"] = True
        base = name.split("-", 1)[1] if name.startswith(("basic-", "advanced-")) else name
        sel = PANEL_SEL.get(base) or PANEL_SEL.get(name)
        if sel:
            entry["audit"] = audit(page, sel)
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


with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu", "--use-gl=swiftshader"],
    )
    for mode in ("basic", "advanced"):
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        open_app(page)
        set_mode(page, mode)
        page.wait_for_timeout(300)
        log(f"=== {MODE} / {mode} ===")

        for name, opens, closes in SURFACES:
            run_surface(page, f"{mode}-{name}", opens, closes)

        for btn in ("#btn-permit", "#btn-growth", "#btn-season", "#btn-layers", "#btn-cost"):
            try:
                page.click(btn, timeout=1500, force=True)
                page.wait_for_timeout(150)
            except Exception:
                pass

        for dock in ("terrain", "underground", "analyze", "innovate", "sun", "measure", "experience"):
            run_surface(page, f"{mode}-dock-{dock}", [("click", f'.td-tab[data-dock="{dock}"]')], None)
        try:
            page.click(".td-tab.active", timeout=1500, force=True)
        except Exception:
            pass

        run_surface(page, f"{mode}-excavate-panel", [("click", "#excavate-btn")], None)
        run_surface(page, f"{mode}-cross-section", [("click", "#cross-section-toggle")], [("click", "#excavate-btn")])
        try:
            page.click("#excavate-btn", timeout=1500, force=True)
            page.wait_for_timeout(200)
        except Exception:
            pass
        run_surface(page, f"{mode}-terrain-analysis", [("click", "#terrain-analysis-btn")], None)
        try:
            page.click("#terrain-analysis-btn", timeout=1500, force=True)
        except Exception:
            pass
        run_surface(page, f"{mode}-innovation-panel", [("click", "#innovation-btn")], None)
        try:
            page.click("#innovation-btn", timeout=1500, force=True)
        except Exception:
            pass
        run_surface(page, f"{mode}-sun-panel", [("click", "#sun-btn")], None)
        try:
            page.click("#sun-btn", timeout=1500, force=True)
        except Exception:
            pass

        page.screenshot(path=f"{OUT}/{mode}-baseline.png")
        if errors:
            results[f"{mode}-jserrors"] = errors[:5]
        page.close()
    browser.close()

with open(f"{OUT}/audit.json", "w") as f:
    json.dump(results, f, indent=2)
log(f"done -> {OUT}/audit.json")
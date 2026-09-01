#!/usr/bin/env python3
"""Read-only DOM probe: verify selectors exist + which are basic-mode reachable."""
import json
from playwright.sync_api import sync_playwright

URL = "http://localhost:8220/index.html"

CHECKS = [
    "#terrain-btn", "#terrain-controls", ".tc-acc", "#tc-panel-ground", "#tc-panel-carving",
    "#tc-panel-presets", "#gridlevel-section-toggle", "#carving-section-toggle",
    "[data-terrain-minimize]", ".terrain-preset-btn", ".terrain-mode-btn",
    "#excavate-btn", "#excavate-panel", "#wireframe-toggle", "#cross-section-toggle",
    "#cs-clip-axis", "#cs-clip-enable", "#cs-clip-pos", "#buried-list", "#buried-count",
    "#terrain-analysis-btn", "#terrain-analysis-panel", "#ta-contour-toggle", "#ta-slope-toggle",
    "#ta-cutfill-toggle", "#ta-waterflow-toggle", "#ta-elev-toggle", "#ta-ghost-toggle",
    "#ta-crosssection-btn", "#ta-compare-btn", "#ta-contour-interval",
    "#innovation-btn", "#innovation-panel", "#innov-pool-btn", "#innov-flatten-btn",
    "#innov-marker-btn", "#innov-slope-btn", "#innov-stats-btn", "#innov-retwall-btn",
    "#innov-ugstruct-btn", "#innov-geolayer-btn", "#innov-volcalc-btn",
    "#innov-watertable-btn", "#innov-ghostpreview-btn", "#innov-exploded-btn",
    "#innov-geolayer-toggle", "#innov-watertable-toggle", "#innov-ghostpreview-toggle",
    "#sun-btn", "#sun-panel", "#sun-time", "#sun-play", "#sun-reset", ".sun-preset",
    "#btn-cost", "#cost-panel", "#btn-layers", "#layer-panel",
    "#btn-season", "#season-panel", ".season-btn", "#btn-growth", "#growth-panel",
    "#growth-slider", "#growth-play", "#btn-permit", "#permit-panel", "#permit-region",
    "#cross-section-panel", "#cut-fill-panel", "#btn-walk",
]

def probe(mode):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
        pg = b.new_page(viewport={"width": 1280, "height": 800})
        pg.goto(URL, wait_until="networkidle", timeout=30000)
        pg.wait_for_timeout(1500)
        pg.evaluate("() => { try{localStorage.removeItem('backyard-recovery-snapshot');}catch(e){} }")
        pg.reload(wait_until="networkidle"); pg.wait_for_timeout(1500)
        skip = pg.locator("#wizard-skip")
        if skip.count() > 0:
            skip.click(); pg.wait_for_timeout(800)
        if mode == "advanced":
            pg.locator("#mode-toggle button[data-mode='advanced']").click()
            pg.wait_for_timeout(700)
        out = {}
        for sel in CHECKS:
            loc = pg.locator(sel)
            n = loc.count()
            vis = False
            if n:
                try:
                    vis = loc.first.is_visible()
                except Exception:
                    vis = False
            out[sel] = {"n": n, "visible": vis}
        # accordion structure
        accs = pg.evaluate("""() => [...document.querySelectorAll('.tc-acc')].map(e => ({
            text: e.textContent.trim().slice(0,40), target: e.getAttribute('aria-controls'),
            expanded: e.getAttribute('aria-expanded')}))""")
        print(f"MODE={mode}")
        print("ACCORDIONS:", json.dumps(accs))
        for sel, v in out.items():
            if v["n"] == 0 or (mode == "basic" and v["visible"]):
                flag = "MISSING" if v["n"] == 0 else "visible-in-basic"
                print(f"  {flag}: {sel} n={v['n']} vis={v['visible']}")
        b.close()

probe("basic")
probe("advanced")
print("DONE")
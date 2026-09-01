#!/usr/bin/env python3
"""S29R (Agent R2) — full panel sweep: every panel surface, Basic AND Advanced.

Surfaces: terrain-controls dock (3 accordions + presets), excavate/underground
dock, terrain-analysis dock (every toggle), innovation dock (every tool incl.
Advanced Tools disclosure), sun dock (every control), cost, layer, season,
growth, permit, cross-section, cut-fill, buried-objects list with 2+ buried items.

Real CDP clicks/keys via Playwright. page.evaluate ONLY for read-only probes and
window._test setup (burying objects / terrain preset). Serve :8220 from MY worktree.
Outputs: reports/s29_shots/r2_<tag>_<mode>.png + .verdict.json
"""
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/byd29r-panels")
from s29r_common import (URL, judge, load_app, make_page, rect_probe,
                         run_surface, sidecar)

REPO = "/root/byd29r-panels"
OUT = os.path.join(REPO, "reports", "s29r_results")

# window._test SETUP (sanctioned): bury two objects below grade so the
# buried-objects list shows 2 items. Read-only otherwise.
BURY = ("() => { const T = window._test;"
        "T.addObject('shed', {}, {x:-12, y:-6, z:0});"
        "T.addObject('pergola', {}, {x:8, y:-9, z:4}); }")
# terrain deform setup so cut-fill/cross-section/analysis have data
DEFORM = ("() => { const T = window._test; T.applyTerrainPreset('hill');"
          "T._recomputeTerrainDeformed(); }")

S = []


def s(tag, mode, actions, label, probe=None):
    S.append((tag, mode, actions, label, probe))


# ── terrain dock: open, 3 accordions, presets, modes, overlays ────────
TC = ("click", "#terrain-btn"), ("wait", 0.6)
ACC_G = ("click", ".tc-acc[aria-controls='tc-panel-ground']"), ("wait", 0.5)
ACC_C = ("click", ".tc-acc[aria-controls='tc-panel-carving']"), ("wait", 0.5)
ACC_P = ("click", ".tc-acc[aria-controls='tc-panel-presets']"), ("wait", 0.5)
DOCKTC = ["#dock-terrain", "#bottom-left-toolbar", "#scale-bar", "#sun-btn"]

s("tc-open", "basic", [TC], "terrain dock default", DOCKTC)
s("tc-open", "adv", [TC], "terrain dock default (Advanced)")
s("tc-acc-ground", "basic", [TC, ACC_G], "accordion 1: Grid Level & Depth open",
  ["#dock-terrain", "#tc-panel-ground"])
s("tc-acc-ground", "adv", [TC, ACC_G], "accordion 1 open (Advanced)")
s("tc-acc-carving", "basic", [TC, ACC_C], "accordion 2: Carving open",
  ["#dock-terrain", "#tc-panel-carving"])
s("tc-acc-carving", "adv", [TC, ACC_C], "accordion 2 open (Advanced)")
s("tc-acc-presets", "basic", [TC, ACC_P], "accordion 3: Presets & Tools open",
  ["#dock-terrain", "#tc-panel-presets"])
s("tc-acc-presets", "adv", [TC, ACC_P], "accordion 3 open (Advanced)")
s("tc-gridlevel", "basic", [TC, ACC_G, ("drag", "#grid-level-slider", 0.55), ("wait", 0.6)],
  "grid level slider mid-track", ["#dock-terrain", "#grid-level-badge"])
s("tc-digmode", "basic", [TC, ("click", ".terrain-mode-btn[data-tmode='dig']"), ("wait", 0.6)],
  "Dig mode armed", ["#dock-terrain"])
s("tc-preset-hill", "basic", [TC, ACC_P, ("click", ".terrain-preset-btn[data-preset='hill']"), ("wait", 1.4)],
  "Hill preset applied", ["#dock-terrain", "#terrain-height-legend"])
s("tc-overlay-height", "basic", [TC, ACC_P, ("click", "#terrain-toggle-height"), ("wait", 1.0)],
  "Height overlay on", ["#terrain-height-legend"])
s("tc-overlay-drainage", "basic", [TC, ACC_P, ("click", "#terrain-toggle-drainage"), ("wait", 1.0)],
  "Drainage overlay on")

# ── excavate / underground dock ────────────────────────────────────────
EX = ("click", "#excavate-btn"), ("wait", 1.0)
DOCKUG = ["#dock-underground", "#scale-bar", "#sun-btn", "#bottom-left-toolbar"]
s("exc-open", "basic", [EX], "excavate dock default", DOCKUG)
s("exc-open", "adv", [EX], "excavate dock default (Advanced)")
s("exc-cutaway", "adv", [EX, ("drag", "#terrain-cutaway", 0.5), ("wait", 0.9)],
  "cutaway slider at 50%")
s("exc-opacity", "adv", [EX, ("drag", "#terrain-opacity", 0.35), ("wait", 0.9)],
  "underground opacity lowered")
s("exc-wireframe", "adv", [EX, ("click", "#wireframe-toggle"), ("wait", 0.9)],
  "wireframe toggle on")
s("exc-cross-section", "adv", [EX, ("click", "#cross-section-toggle"), ("wait", 0.9)],
  "cross-section toggle on", ["#cross-section-panel", "#dock-underground"])
s("exc-cs-clip", "adv", [EX, ("click", "#cross-section-toggle"), ("wait", 0.4),
   ("click", "#cs-clip-enable"), ("wait", 0.6)],
  "cross-section clip enabled", ["#cross-section-panel"])
s("exc-buried-empty", "basic", [EX], "buried list empty state", ["#dock-underground", "#buried-list"])
s("exc-buried-2items", "basic", [("eval_setup", BURY), EX], "buried list with 2 items",
  ["#dock-underground", "#buried-list"])
s("exc-buried-2items", "adv", [("eval_setup", BURY), EX], "buried list 2 items (Advanced)")

# ── terrain-analysis dock: every toggle ────────────────────────────────
TA = ("click", "#terrain-analysis-btn"), ("wait", 0.8)
DOCKAN = ["#dock-analyze", "#bottom-left-toolbar", "#scale-bar"]
s("ta-open", "basic", [TA], "analyze dock default", DOCKAN)
s("ta-open", "adv", [TA], "analyze dock default (Advanced)")
for t, sel, lab in [
    ("ta-contour", "#ta-contour-toggle", "contours on"),
    ("ta-slope", "#ta-slope-toggle", "slope heatmap on"),
    ("ta-elev", "#ta-elev-toggle", "color by height on"),
    ("ta-waterflow", "#ta-waterflow-toggle", "water flow on"),
]:
    s(t, "adv", [("eval_setup", DEFORM), TA, ("click", sel), ("wait", 1.1)], lab,
      ["#dock-analyze", "#terrain-height-legend"])
    s(t, "basic", [TA, ("click", sel), ("wait", 1.1)], lab + " (Basic)", ["#dock-analyze"])
s("ta-cutfill", "adv", [("eval_setup", DEFORM), TA, ("click", "#ta-cutfill-toggle"), ("wait", 1.1)],
  "cut/fill volume on", ["#dock-analyze", "#cut-fill-panel"])
s("ta-ghost", "adv", [("eval_setup", BURY), ("eval_setup", DEFORM), TA,
   ("click", "#ta-ghost-toggle"), ("wait", 1.1)], "highlight buried on")
s("ta-crosssection", "adv", [TA, ("click", "#ta-crosssection-btn"), ("wait", 0.9)],
  "draw cross-section line tool", ["#ta-cross-section-overlay", "#dock-analyze"])
s("ta-compare", "adv", [TA, ("hover", "#ta-compare-btn"), ("wait", 0.6)],
  "hold-to-compare pressed state", ["#dock-analyze"])

# ── innovation dock: every tool + advanced disclosure ──────────────────
IN = ("click", "#innovation-btn"), ("wait", 0.8)
DOCKIN = ["#dock-innovate", "#bottom-left-toolbar"]
s("innov-open", "basic", [IN], "innovate dock default", DOCKIN)
s("innov-open", "adv", [IN], "innovate dock default (Advanced)")
CORE_TOOLS = [
    ("pool", "#innov-pool-btn"), ("flatten", "#innov-flatten-btn"),
    ("marker", "#innov-marker-btn"),
]
ADV_TOOLS = [
    ("slope", "#innov-slope-btn"), ("stats", "#innov-stats-btn"),
    ("retwall", "#innov-retwall-btn"), ("ugstruct", "#innov-ugstruct-btn"),
    ("geolayer", "#innov-geolayer-btn"), ("volcalc", "#innov-volcalc-btn"),
    ("exploded", "#innov-exploded-btn"), ("watertable", "#innov-watertable-btn"),
    ("ghostpreview", "#innov-ghostpreview-btn"),
]
for name, sel in CORE_TOOLS:
    s(f"innov-{name}", "basic", [IN, ("click", sel), ("wait", 1.0)],
      f"innov tool: {name}", DOCKIN)
    s(f"innov-{name}", "adv", [IN, ("click", sel), ("wait", 1.0)],
      f"innov tool: {name} (Advanced)")
ADV_OPEN = [IN, ("click", ".advanced-toggle"), ("wait", 0.6)]
for name, sel in ADV_TOOLS:
    s(f"innov-{name}", "adv", ADV_OPEN + [("click", sel), ("wait", 1.0)],
      f"innov advanced tool: {name}", DOCKIN)
s("innov-advanced-open", "adv", ADV_OPEN, "Advanced Tools disclosure expanded", DOCKIN)

# ── sun dock: every control ────────────────────────────────────────────
SU = ("click", "#sun-btn"), ("wait", 0.7)
DOCKSU = ["#dock-sun", "#scale-bar", "#sun-btn", "#bottom-left-toolbar"]
s("sun-open", "basic", [SU], "sun dock default", DOCKSU)
s("sun-open", "adv", [SU], "sun dock default (Advanced)")
s("sun-morning", "basic", [SU, ("drag", "#sun-time", 0.15), ("wait", 0.7)],
  "sun time early morning")
s("sun-evening", "basic", [SU, ("drag", "#sun-time", 0.92), ("wait", 0.7)],
  "sun time evening")
s("sun-play", "basic", [SU, ("click", "#sun-play"), ("wait", 1.6)],
  "sun day-cycle playing")

# ── cost / layer ───────────────────────────────────────────────────────
s("cost-open", "basic", [("click", "#btn-cost"), ("wait", 0.8)], "cost panel empty",
  ["#cost-panel", "#right-panel-stack"])
s("cost-open", "adv", [("eval_setup", BURY), ("click", "#btn-cost"), ("wait", 0.8)],
  "cost panel with objects", ["#cost-panel"])
s("layer-open", "basic", [("click", "#btn-layers"), ("wait", 0.8)], "layer panel",
  ["#layer-panel"])
s("layer-open", "adv", [("click", "#btn-layers"), ("wait", 0.8)], "layer panel (Advanced)")
s("layer-toggle", "basic", [("click", "#btn-layers"), ("wait", 0.5),
   ("click", ".layer-row .layer-toggle"), ("wait", 0.6)],
  "one layer toggled off", ["#layer-panel"])

# ── season / growth / permit (Advanced-only openers) ───────────────────
s("season-open", "adv", [("click", "#btn-season"), ("wait", 0.8)], "season panel",
  ["#season-panel"])
s("season-winter", "adv", [("click", "#btn-season"), ("wait", 0.5),
   ("click", ".season-btn[data-season='winter']"), ("wait", 0.9)],
  "season: winter", ["#season-panel"])
s("growth-open", "adv", [("click", "#btn-growth"), ("wait", 0.8)], "growth panel",
  ["#growth-panel"])
s("growth-year10", "adv", [("click", "#btn-growth"), ("wait", 0.5),
   ("drag", "#growth-slider", 0.5), ("wait", 0.8)],
  "growth slider mid (year ~10)", ["#growth-panel"])
s("growth-play", "adv", [("click", "#btn-growth"), ("wait", 0.4),
   ("click", "#growth-play"), ("wait", 1.6)],
  "growth animation playing", ["#growth-panel"])
s("permit-open", "adv", [("click", "#btn-permit"), ("wait", 1.0)], "permit panel",
  ["#permit-panel", "#permit-results"])

# ── cross-section + cut-fill panels ────────────────────────────────────
s("cross-section-open", "adv", [("eval_setup", DEFORM), EX,
   ("click", "#cross-section-toggle"), ("wait", 1.0)],
  "cross-section panel + terrain", ["#cross-section-panel", "#dock-underground"])
s("cross-section-open", "basic", [("eval_setup", DEFORM), EX,
   ("click", "#cross-section-toggle"), ("wait", 1.0)],
  "cross-section panel (Basic)", ["#cross-section-panel"])
s("cut-fill-open", "adv", [("eval_setup", DEFORM), TA,
   ("click", "#ta-cutfill-toggle"), ("wait", 1.1)],
  "cut-fill panel populated", ["#cut-fill-panel", "#dock-analyze"])
s("cut-fill-open", "basic", [("eval_setup", DEFORM), TA,
   ("click", "#ta-cutfill-toggle"), ("wait", 1.1)],
  "cut-fill panel populated (Basic)", ["#cut-fill-panel"])


def run(only=None, modes=None):
    results = {}
    with sync_playwright() as p:
        browser, page, errors = make_page(p, 1280, 800)
        for tag, mode, actions, label, probe in S:
            if only and only not in tag:
                continue
            if modes and mode not in modes:
                continue
            # fresh load per surface for determinism
            load_app(page, mode)
            ok, err = run_surface(page, actions, tag, mode)
            if not ok:
                rec = {"surface": tag, "mode": mode, "label": label,
                       "ok": False, "err": err}
                name = f"r2_{tag}_{mode}"
                sidecar(name, rec)
                results[name] = rec
                print(f"[FAIL] {name} :: {err[:140]}", flush=True)
                continue
            judge(page, tag, mode, label, results, probe)
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, f"r2_sweep_{time.strftime('%H%M%S')}.json"), "w") as f:
            json.dump(results, f, indent=1)
        print("PAGE ERRORS:", errors[:5])
        browser.close()
    return results


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
    modes = None
    for a in sys.argv[1:]:
        if a == "--basic":
            modes = ["basic"]
        elif a == "--adv":
            modes = ["adv"]
    r = run(only, modes)
    nclean = sum(1 for v in r.values() if v.get("clean") is True)
    ndirty = sum(1 for v in r.values() if v.get("clean") is False)
    nerr = sum(1 for v in r.values() if v.get("clean") is None)
    print(f"\nSUMMARY: {len(r)} surfaces | CLEAN {nclean} | DIRTY {ndirty} | VISIONERR {nerr}")
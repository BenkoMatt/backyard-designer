#!/usr/bin/env python3
"""S29R (Agent R2) — full panel sweep: every panel surface, Basic AND Advanced.

Real CDP clicks/keys via Playwright. page.evaluate ONLY for read-only probes and
window._test setup (burying objects). Serve :8220 from MY worktree.
Outputs: reports/s29_shots/r2_<tag>_<mode>.png + .verdict.json
"""
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/byd29r-panels")
from s29r_common import (URL, judge, load_app, make_page, rect_probe,
                         run_surface, shot_path, sidecar, vision_qa, is_clean)

REPO = "/root/byd29r-panels"
OUT = os.path.join(REPO, "reports", "s29r_results")

# window._test SETUP (sanctioned): bury two objects by giving them negative y
# (below grade) so the buried-objects list shows 2 items. Read-only otherwise.
BURY = ("() => { const T = window._test;"
        "T.addObject('shed', {}, {x:-12, y:-6, z:0});"
        "T.addObject('pergola', {}, {x:8, y:-9, z:4}); }")
# terrain deform setup so cut-fill/cross-section/analysis have data
DEFORM = ("() => { const T = window._test; T.applyTerrainPreset('hill');"
          "T._recomputeTerrainDeformed(); }")

# (tag, mode, actions, label, probe_selectors)
S = []

def s(tag, mode, actions, label, probe=None):
    S.append((tag, mode, actions, label, probe))

# ── terrain-controls: open, 3 accordions, presets ─────────────────────
TC = ("click", "#terrain-btn"), ("wait", 0.5)
ACC_G = ("click", ".tc-acc[aria-controls='tc-panel-ground']"), ("wait", 0.4)
ACC_C = ("click", ".tc-acc[aria-controls='tc-panel-carving']"), ("wait", 0.4)
ACC_P = ("click", ".tc-acc[aria-controls='tc-panel-presets']"), ("wait", 0.4)

s("tc-open", "basic", [TC], "terrain-controls default",
  ["#terrain-controls", "#scale-bar", "#sun-btn"])
s("tc-open", "adv", [TC], "terrain-controls default (Advanced)",
  ["#terrain-controls", "#scale-bar", "#sun-btn"])
s("tc-acc-ground", "basic", [TC, ACC_G, ("wait", 0.4)], "accordion 1: Grid Level & Depth",
  ["#terrain-controls", "#tc-panel-ground"])
s("tc-acc-ground", "adv", [TC, ACC_G, ("wait", 0.4)], "accordion 1 (Advanced)")
s("tc-acc-carving", "basic", [TC, ACC_C, ("wait", 0.4)], "accordion 2: Carving",
  ["#terrain-controls", "#tc-panel-carving"])
s("tc-acc-carving", "adv", [TC, ACC_C, ("wait", 0.4)], "accordion 2 (Advanced)")
s("tc-acc-presets", "basic", [TC, ACC_P, ("wait", 0.4)], "accordion 3: Presets & Tools",
  ["#terrain-controls", "#tc-panel-presets"])
s("tc-acc-presets", "adv", [TC, ACC_P, ("wait", 0.4)], "accordion 3 (Advanced)")
# grid-level slider moved (real drag on the range input inside accordion 1)
s("tc-gridlevel", "basic", [TC, ACC_G,
   ("drag", "#grid-level-slider", 0.55), ("wait", 0.5)],
  "grid level slider mid-drag", ["#terrain-controls", "#grid-level-badge"])
s("tc-digmode", "basic", [TC, ACC_G,
   ("click", ".terrain-mode-btn[data-tmode='dig']"), ("wait", 0.5)],
  "Dig mode armed", ["#terrain-controls"])
s("tc-preset-applied", "basic", [TC, ACC_P,
   ("click", ".terrain-preset-btn[data-preset='hill']"), ("wait", 1.2)],
  "Hill preset applied", ["#terrain-controls", "#terrain-height-legend"])
s("tc-overlay-height", "basic", [TC, ACC_P,
   ("click", "#terrain-toggle-height"), ("wait", 0.9)],
  "Height overlay on", ["#terrain-height-legend"])
s("tc-overlay-drainage", "basic", [TC, ACC_P,
   ("click", "#terrain-toggle-drainage"), ("wait", 0.9)],
  "Drainage overlay on")

# ── excavate ───────────────────────────────────────────────────────────
EX = ("click", "#excavate-btn"), ("wait", 0.9)
s("exc-open", "basic", [EX], "excavate panel default",
  ["#excavate-panel", "#scale-bar", "#sun-btn"])
s("exc-open", "adv", [EX], "excavate panel default (Advanced)")
s("exc-wireframe", "adv", [EX, ("click", "#wireframe-toggle"), ("wait", 0.8)],
  "wireframe toggle on")
s("exc-cross-section", "adv", [EX, ("click", "#cross-section-toggle"), ("wait", 0.8)],
  "cross-section toggle on", ["#cross-section-panel"])
s("exc-cs-clip", "adv", [EX, ("click", "#cross-section-toggle"), ("wait", 0.4),
   ("click", "#cs-clip-enable"), ("wait", 0.5)],
  "cross-section clip enabled")
s("exc-buried-2items", "basic", [("eval_setup", BURY), EX], "buried list 2 items",
  ["#excavate-panel", "#buried-list"])
s("exc-buried-2items", "adv", [("eval_setup", BURY), EX], "buried list 2 items (Advanced)",
  ["#excavate-panel", "#buried-list"])

# ── terrain-analysis: every toggle ─────────────────────────────────────
TA = ("click", "#terrain-analysis-btn"), ("wait", 0.7)
s("ta-open", "basic", [TA], "terrain-analysis default",
  ["#terrain-analysis-panel", "#scale-bar"])
s("ta-open", "adv", [TA], "terrain-analysis default (Advanced)")
for t, sel, lab in [
    ("ta-contour", "#ta-contour-toggle", "contours on"),
    ("ta-slope", "#ta-slope-toggle", "slope heatmap on"),
    ("ta-elev", "#ta-elev-toggle", "color by height on"),
    ("ta-waterflow", "#ta-waterflow-toggle", "water flow on"),
]:
    s(t, "adv", [("eval_setup", DEFORM), TA, ("click", sel), ("wait", 1.0)],
      lab, ["#terrain-analysis-panel", "#terrain-height-legend"])
s("ta-cutfill", "adv", [("eval_setup", DEFORM), TA, ("click", "#ta-cutfill-toggle"), ("wait", 1.0)],
  "cut/fill volume on", ["#terrain-analysis-panel", "#cut-fill-panel"])
s("ta-ghost", "adv", [("eval_setup", BURY), ("eval_setup", DEFORM), TA,
   ("click", "#ta-ghost-toggle"), ("wait", 1.0)],
  "highlight buried on")
s("ta-crosssection", "adv", [TA, ("click", "#ta-crosssection-btn"), ("wait", 0.8)],
  "ta cross-section tool", ["#ta-cross-section-overlay"])

# ── innovation: every tool ─────────────────────────────────────────────
IN = ("click", "#innovation-btn"), ("wait", 0.7)
s("innov-open", "basic", [IN], "innovation panel default", ["#innovation-panel"])
s("innov-open", "adv", [IN], "innovation panel default (Advanced)")
TOOLS = [
    ("pool", "#innov-pool-btn"), ("flatten", "#innov-flatten-btn"),
    ("marker", "#innov-marker-btn"), ("slope", "#innov-slope-btn"),
    ("stats", "#innov-stats-btn"), ("retwall", "#innov-retwall-btn"),
    ("ugstruct", "#innov-ugstruct-btn"), ("geolayer", "#innov-geolayer-btn"),
    ("volcalc", "#innov-volcalc-btn"), ("watertable", "#innov-watertable-btn"),
    ("ghostpreview", "#innov-ghostpreview-btn"), ("exploded", "#innov-exploded-btn"),
]
for name, sel in TOOLS:
    s(f"innov-{name}", "adv", [IN, ("click", sel), ("wait", 0.9)],
      f"innovation tool: {name}", ["#innovation-panel"])
# a couple of basic-mode tool states too (panel is reachable in basic)
for name, sel in TOOLS[:3]:
    s(f"innov-{name}", "basic", [IN, ("click", sel), ("wait", 0.9)],
      f"innovation tool: {name} (Basic)")

# ── sun: every control ────────────────────────────────────────────────
SU = ("click", "#sun-btn"), ("wait", 0.6)
s("sun-open", "basic", [SU], "sun panel default",
  ["#sun-panel", "#scale-bar", "#sun-btn"])
s("sun-open", "adv", [SU], "sun panel default (Advanced)")
s("sun-morning", "basic", [SU, ("drag", "#sun-time", 0.15), ("wait", 0.6)],
  "sun time early morning")
s("sun-evening", "basic", [SU, ("drag", "#sun-time", 0.92), ("wait", 0.6)],
  "sun time evening")
s("sun-play", "basic", [SU, ("click", "#sun-play"), ("wait", 1.5)],
  "sun day-cycle playing")

# ── cost / layer ───────────────────────────────────────────────────────
s("cost-open", "basic", [("click", "#btn-cost"), ("wait", 0.7)], "cost panel",
  ["#cost-panel"])
s("cost-open", "adv", [("eval_setup", BURY), ("click", "#btn-cost"), ("wait", 0.7)],
  "cost panel with objects (Advanced)")
s("layer-open", "basic", [("click", "#btn-layers"), ("wait", 0.7)], "layer panel",
  ["#layer-panel"])
s("layer-open", "adv", [("click", "#btn-layers"), ("wait", 0.7)], "layer panel (Advanced)")
s("layer-toggle", "basic", [("click", "#btn-layers"), ("wait", 0.4),
   ("click", ".layer-row .layer-toggle"), ("wait", 0.5)],
  "layer toggle off one layer", ["#layer-panel"])

# ── season / growth / permit (Advanced-only topbar buttons) ───────────
s("season-open", "adv", [("click", "#btn-season"), ("wait", 0.7)], "season panel",
  ["#season-panel"])
s("season-winter", "adv", [("click", "#btn-season"), ("wait", 0.4),
   ("click", ".season-btn[data-season='winter']"), ("wait", 0.8)],
  "season: winter", ["#season-panel"])
s("growth-open", "adv", [("click", "#btn-growth"), ("wait", 0.7)], "growth panel",
  ["#growth-panel"])
s("growth-year10", "adv", [("click", "#btn-growth"), ("wait", 0.4),
   ("drag", "#growth-slider", 0.5), ("wait", 0.7)],
  "growth slider year 10", ["#growth-panel"])
s("growth-play", "adv", [("click", "#btn-growth"), ("wait", 0.3),
   ("click", "#growth-play"), ("wait", 1.5)],
  "growth animation playing", ["#growth-panel"])
s("permit-open", "adv", [("click", "#btn-permit"), ("wait", 0.8)], "permit panel",
  ["#permit-panel", "#permit-results"])

# ── cross-section + cut-fill (triggered via excavate/analysis) ────────
s("cross-section-open", "adv", [("eval_setup", DEFORM), EX,
   ("click", "#cross-section-toggle"), ("wait", 0.9)],
  "cross-section panel with terrain", ["#cross-section-panel"])
s("cross-section-line", "adv", [("eval_setup", DEFORM), EX,
   ("click", "#cross-section-toggle"), ("wait", 0.4),
   ("eval_setup", "() => { window._testCSLinePreset && window._testCSLinePreset(); }"),
   ("wait", 0.8)],
  "cross-section with drawn line (if preset hook)")
s("cut-fill-open", "adv", [("eval_setup", DEFORM),
   ("click", "#terrain-analysis-btn"), ("wait", 0.5),
   ("click", "#ta-cutfill-toggle"), ("wait", 1.0)],
  "cut-fill panel populated", ["#cut-fill-panel", "#terrain-analysis-panel"])

# basic-mode: cut-fill reachable in basic too
s("cut-fill-open", "basic", [("eval_setup", DEFORM),
   ("click", "#terrain-analysis-btn"), ("wait", 0.5),
   ("click", "#ta-cutfill-toggle"), ("wait", 1.0)],
  "cut-fill panel populated (Basic)", ["#cut-fill-panel"])

# cross-section in basic mode
s("cross-section-open", "basic", [("eval_setup", DEFORM), EX,
   ("click", "#cross-section-toggle"), ("wait", 0.9)],
  "cross-section panel (Basic)", ["#cross-section-panel"])


def run(only=None):
    results = {}
    with sync_playwright() as p:
        browser, page, errors = make_page(p, 1280, 800)

        i = 0
        for tag, mode, actions, label, probe in S:
            i += 1
            if only and only not in tag:
                continue
            # fresh load per surface for determinism (prevents eval_setup
            # accumulation and panel state bleed between surfaces)
            load_app(page, mode)
            ok, err = run_surface(page, actions, tag, mode)
            if not ok:
                rec = {"surface": tag, "mode": mode, "label": label,
                       "ok": False, "err": err}
                name = f"r2_{tag}_{mode}"
                sidecar(name, rec)
                results[name] = rec
                print(f"[FAIL] {name} :: {err[:140]}", flush=True)
                # hard reset on failure
                load_app(page, mode)
                continue
            judge(page, tag, mode, label, results, probe)
        # save batch results
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, f"r2_sweep_{time.strftime('%H%M%S')}.json"), "w") as f:
            json.dump(results, f, indent=1)
        print("PAGE ERRORS:", errors[:5])
        browser.close()
    return results


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    r = run(only)
    nclean = sum(1 for v in r.values() if v.get("clean") is True)
    ndirty = sum(1 for v in r.values() if v.get("clean") is False)
    nerr = sum(1 for v in r.values() if v.get("clean") is None)
    print(f"\nSUMMARY: {len(r)} surfaces | CLEAN {nclean} | DIRTY {ndirty} | VISIONERR {nerr}")
# Sprint 7 — Discovery Log: Real-World Utility Explorer

**Agent:** Agent 1 (Builder)  
**Role:** THE REAL-WORLD UTILITY EXPLORER  
**Date:** August 23, 2026  
**Working Directory:** `/root/byd7-real-world/`

---

## Mission

Research how the Backyard Designer 3D tool could be used in real landscaping and construction workflows. Identify what would make this tool genuinely useful to a homeowner, landscaper, or contractor. Prototype the 3 most impactful ideas as working code.

---

## Ideas Explored

All 6 candidate ideas were evaluated for real-world utility:

### 1. SEASONAL PLANNING ⭐ PROTOTYPED
**What it does:** A season selector (Spring/Summer/Fall/Winter) that changes tree foliage color, grass/ground color, and sun angle. Users can see how their yard looks across all 4 seasons.

**Why it's impactful:**
- Homeowners planting trees need to know what the yard will look like year-round — not just in summer
- Deciduous trees that look great in summer may look bare and stark in winter
- Fall foliage colors help plan visual appeal
- Sun angle changes dramatically across seasons, affecting shade patterns
- Contractors can show clients seasonal variations to set expectations

**Implementation:**
- Added `#season-panel` with 4 season buttons (spring 🌱, summer ☀️, fall 🍂, winter ❄️)
- Created `SEASON_FOLIAGE` color palette system with species-specific colors per season
  - Spring: light green buds, flowering shrubs (crabapple pink, forsythia yellow)
  - Summer: full green canopy (original colors)
  - Fall: orange/red maple, brown oak, russet dogwood
  - Winter: bare branches for deciduous trees, darker evergreens, brown dormant grass
- Modified `createTreeDeciduous()`, `createTreeEvergreen()`, `createBush()`, `createHedge()`, `createLawn()` to use seasonal colors
- Ground mesh (`yardMesh`) color changes per season (green summer → brown winter)
- Sun date auto-updates to represent each season (April 15 / July 15 / October 15 / January 15)
- Winter deciduous trees lose their canopy (bare branches only)
- Added `#btn-season` topbar button

**Lines added:** ~150 lines CSS, ~80 lines JS (season module), ~60 lines modified in factory functions

### 2. PLANT GROWTH SIMULATION ⭐ PROTOTYPED
**What it does:** A growth timeline slider (Year 0 to Year 20) that animates trees and shrubs growing from saplings to mature size using a logistic growth curve.

**Why it's impactful:**
- Homeowners planting young trees often underestimate how large they'll become
- "Will this tree eventually hit the power line / fence / house?" — a 20-year projection answers this
- Contractors can show clients why spacing matters at maturity
- Visualizing the "future yard" helps with long-term planning
- The animation feature (play button) creates an engaging "time-lapse" effect

**Implementation:**
- Added `#growth-panel` with a range slider (0-20 years), year display, info text, and play button
- Created `growthFactor()` function using a logistic growth curve:
  - Year 0: 8% of mature size (sapling)
  - Year 5: ~40% (young established)
  - Year 10: ~75% (filling in)
  - Year 15: ~95% (nearly mature)
  - Year 20: 100% (full maturity)
- Modified all plant factories to scale dimensions by `growthFactor()`:
  - Tree trunk height/radius scales
  - Tree canopy radius scales
  - Bush diameter scales
  - Hedge height scales (length stays — hedges are trimmed)
  - Evergreen cone layers scale
- Minimum size clamping prevents degenerate geometry (radius > 0.1)
- Growth animation plays from year 0 to 20 in 200ms steps
- Info text updates dynamically with growth stage descriptions
- Added `#btn-growth` topbar button

**Lines added:** ~40 lines CSS, ~90 lines JS (growth module), integrated into factory functions

### 3. COST ESTIMATION EXPANSION (evaluated, not prototyped)
**What it does:** Expand cost estimator with real material costs, labor estimates, and project timeline.

**Assessment:** The existing cost estimator already has a reasonable `COST_TABLE` with per-object cost compute functions. While expanding it with labor/timeline would be useful, it's an incremental improvement to an existing feature rather than a new capability. The existing cost panel already covers material costs for all object types. Lower impact than the 3 selected.

### 4. PERMIT CHECKER ⭐ PROTOTYPED
**What it does:** Checks designs against common building permit requirements: setback distances from property lines, structure/fence height limits, pool barrier requirements, fire pit safety clearances, retaining wall engineering thresholds, and deck permit thresholds.

**Why it's impactful:**
- This is the #1 question homeowners have: "Do I need a permit for this?"
- Setback violations are the most common reason projects get red-tagged
- Pool fence requirements are legally mandated in most jurisdictions
- Fire pit clearances prevent real fire hazards
- Retaining walls over 4ft require engineering in most codes
- Decks over 30 inches need permits per IRC
- Region-specific rules (CA, TX, FL, IRC, Generic US) add real value
- Saves homeowners from costly mistakes before they build

**Implementation:**
- Added `#permit-panel` with configurable inputs:
  - Property setback distance (ft)
  - Max structure height (ft)
  - Max fence height (ft)
  - Region selector (Generic US, IRC Standard, California, Texas, Florida)
- Region-specific rules (`REGION_RULES`) with different defaults per region
  - TX allows 15ft structures, 8ft fences, 25ft fire clearance
  - CA requires 60-inch pool barriers
  - FL/IRC require 48-inch pool barriers
- Checks performed:
  1. **Setback violations:** Object footprint vs. distance to each property boundary
  2. **Structure height limits:** Sheds, pergolas exceeding max height
  3. **Fence height limits:** Fences exceeding local max
  4. **Pool barrier requirement:** Pools without a fence within 30ft
  5. **Fire pit clearance:** Fire pits too close to structures (< 10-25ft depending on region)
  6. **Retaining wall engineering:** Walls over 4ft need engineering
  7. **Deck permit threshold:** Decks over 30 inches need permits
- Warnings are color-coded: critical (red), caution (yellow), ok (green)
- Auto-rechecks when objects are added/removed (hooked into `addObject`/`removeObject`)
- Added `#btn-permit` topbar button

**Lines added:** ~50 lines CSS, ~200 lines JS (permit module)

### 5. PRINT/EXPORT (evaluated, not prototyped)
**What it does:** Generate a clean 2D top-down view with measurements, plant legend, and materials list.

**Assessment:** Useful for contractors who need to print plans, but the app already has a 2D bird's-eye view and screenshot capability. This would require significant canvas-based rendering work for the print layout. Lower impact than the 3 selected for this sprint.

### 6. DIY PROJECT GUIDES (evaluated, not prototyped)
**What it does:** Step-by-step building instructions for raised beds, fire pits, patios, etc.

**Assessment:** Valuable content feature but essentially static text content rather than interactive tool functionality. Would add more value as a companion to the permit checker (which tells you what you need permission for) and growth simulator (which tells you what to plant). Lower interactive impact than the 3 selected.

---

## Bugs Found and Fixed

### Bug 1: `applySeasonalGroundColor is not defined`
**Root cause:** The function was initially defined inside the seasonal planning IIFE (immediately-invoked function expression), which runs after the scene initialization code that calls it during page load.
**Fix:** Moved `applySeasonalGroundColor()` to a global function definition placed near the `SEASON_FOLIAGE` constant, before the scene init code runs.
**Impact:** Would have caused a console error on every page load.

---

## Test Results

**Test file:** `test_sprint7_realworld.py`  
**Total tests:** 37  
**Passing:** 37  
**Failing:** 0

### Test Coverage:
- **Seasonal Planning (13 tests):** Button exists, panel opens, 4 season buttons, season switching, ground color changes for all 4 seasons, season info text updates, sun date updates, tree foliage color changes
- **Plant Growth Simulation (9 tests):** Button exists, panel opens, slider range 0-20, growth factor at year 0/10/20, growth display updates, growth factor scaling, growth info text
- **Permit Checker (10 tests):** Button exists, panel opens, config inputs exist, permit check runs, pool barrier detection, fence clears warning, fire pit clearance detection, region change updates defaults, setback violation detection
- **Regression (5 tests):** Page loads, no console errors, cost estimator works, sun panel works, objects persist

---

## Architecture Notes

### How Season & Growth Work Together
Both features use global state variables (`currentSeason`, `growthYear`) that are read by the object factory functions. When either value changes, all scene objects are rebuilt via `buildSceneObject()`. This approach:
- ✅ Doesn't modify the `addObject`/`buildSceneObject` API
- ✅ Works with existing save/load (season/growth are visual-only, not serialized)
- ✅ Can be combined (e.g., winter + year 5 = small bare trees)
- ✅ Rebuilds are efficient (only re-runs factories, doesn't re-add objects)

### How Permit Checker Hooks In
The permit checker wraps `addObject` and `removeObject` to auto-recheck when the design changes, but only if the panel is visible. This avoids unnecessary computation when the panel is closed.

---

## Files Modified

1. **index.html** — Added 3 feature prototypes (~750 lines of new code)
2. **test_sprint7_realworld.py** — New Playwright test suite (37 tests)
3. **DISCOVERY_LOG.md** — This file

---

## Summary

Three high-impact real-world utility features were prototyped:

| Feature | Impact | Real-World Use |
|---------|--------|----------------|
| Seasonal Planning | Visual | Homeowners see year-round appearance; contractors set expectations |
| Plant Growth Simulation | Planning | Homeowners understand mature tree sizes; prevents future problems |
| Permit Checker | Regulatory | Homeowners know if they need permits; prevents costly violations |

All 37 tests pass. No existing features were broken. No console errors on load.
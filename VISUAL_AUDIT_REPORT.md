# Sprint 21 — Visual Audit Report (Agent 3)

**Branch:** `sprint21-visual-audit` · **Baseline:** `da1163f`
**Method:** Playwright + real CDP input (mouse clicks / right-clicks / keyboard — no `page.evaluate()` click paths), 1280×800 viewport, screenshots of every surface in **both Basic and Advanced mode**, plus DOM geometry metrics (scrollHeight vs clientHeight, below-fold controls, off-viewport rects).

**Screenshots:** `reports/sprint21_shots/before/` (49) and `reports/sprint21_shots/after/` (44+), metrics in `metrics.json` in each dir.

---

## Surfaces audited (each opened via real CDP click, both modes unless Basic-hidden by design)

| Surface | Trigger | Before | After |
|---|---|---|---|
| Terrain dock | `.td-tab[data-dock="terrain"]` | ❌ scroll-orphan | ✅ fixed |
| Underground dock | `.td-tab[data-dock="underground"]` | ✅ | ✅ |
| Analyze dock | `.td-tab[data-dock="analyze"]` | ✅ | ✅ |
| Pro Tools (innovate) dock | `.td-tab[data-dock="innovate"]` | ✅ | ✅ |
| Sun dock | `.td-tab[data-dock="sun"]` | ✅ | ✅ |
| Measure dock | `.td-tab[data-dock="measure"]` | ✅ | ✅ |
| Atmosphere (experience) dock | `.td-tab[data-dock="experience"]` | ✅ | ✅ |
| Excavate flow | `#excavate-btn` | ❌ dead button | ✅ wired |
| Cross-Section panel | `#cross-section-toggle` | ⚠️ 11px scroll | ✅ |
| Terrain Analysis panel | `#terrain-analysis-btn` / dock | ✅ | ✅ |
| Innovation panel | `#innovation-btn` / dock | ✅ | ✅ |
| Sun panel | `#sun-btn` / dock | ✅ | ✅ |
| Cost panel | `#btn-cost` | ✅ | ✅ |
| Layer panel | `#btn-layers` | ✅ | ✅ |
| Cut/Fill panel | `#ta-cutfill-toggle` | ✅ (opens from Analyze dock) | ✅ |
| Help modal | `#btn-help` | ✅ (long doc scrolls by design) | ✅ |
| Templates modal | `#btn-templates` | ✅ | ✅ |
| Share modal | `#btn-share` | ✅ | ✅ |
| Command Palette | Ctrl+K | ✅ | ✅ |
| Context menu | right-click on object | ✅ (self-clamping to viewport) | ✅ |
| Season / Growth / Permit panels | topbar buttons | ✅ | ✅ |
| Wizard (step 2) | wizard next | ✅ | ✅ |
| Welcome prompt | post-wizard dialog | ✅ | ✅ |

---

## Findings & fixes (all verified in rendered pixels, not just DOM)

### 1. Terrain dock scroll-orphan — 11 controls below the fold (Brief Mandate #1)
- **Before:** content `scrollHeight=860px` inside a 700px panel; panel bottom at y=816 extended under the status bar (top y=776). Below fold: `carving-clear-btn`, all 6 preset buttons, both overlay toggles, `terrain-flatten`, `terrain-smooth-pass`. Reaching them required scrolling.
- **Fixes** (`index.html`):
  - Mode buttons (Raise/Excavate/Smooth/Erode/Flatten/**Dig**/**Fill**) now lay out in a 4-column grid — all 7 primary modes visible in the top region with **zero scrolling**; IDs and `data-tmode` attributes preserved.
  - **Carving Tools**, **Presets & Overlays**, and **Grid Level** became one-click collapsible sections (`.s21-collapse-btn`, `aria-expanded`/`aria-controls` wired; default collapsed). No feature removed — 1 click expands.
  - Instructions banner compacted (62px → ~28px).
- **After:** `scrollable=false`; content 390px in 390px viewport area; 20 visible controls, 0 below fold; all mode buttons fully on-screen.

### 2. Bottom-left quick-access toolbar was empty — Excavate button invisible (Brief Mandate #2 root context)
- **Before:** `#bottom-left-toolbar` existed at runtime but had **zero visible buttons** — `#tape-measure-btn`, `#terrain-btn`, `#excavate-btn`, `#terrain-analysis-btn`, `#innovation-btn`, `#sun-btn` were `display:none !important` (a leftover from Sprint 5's dock migration; Sprint 19 then built a container for buttons that were never shown).
- **Fix:** the six quick-access buttons are visible again inside `#bottom-left-toolbar` (flex, in-flow). The tool dock remains the full-panel system; these are 1-click launchers. All element IDs preserved. Sprint 11 gate compatibility kept (it records dock-replaced buttons as "hidden expected" regardless of visibility).

### 3. Excavate flow never revealed the ground (Brief Mandate #2 — root cause)
- **Before:** `#excavate-btn` toggled `.visible` on `#excavate-panel`, whose content had been **moved into `#dock-underground-content`** at setup (Sprint 13) — clicking it toggled an empty, CSS-hidden shell. The auto-dig clip plane only armed via the Terrain dock Dig button.
- **Fix:** one canonical function `_setUndergroundReveal(on)` (exported on `window`) drives the clip-plane state from **any** route:
  - `#excavate-btn` now opens the Underground dock, sets `terrainBrushMode='dig'`, calls `updateAutoDigClip()` (geological layers revealed), updates the buried list, and shows a hint.
  - Closing (button, `#excavate-close`) restores `terrainBrushMode='raise'`, removes the clip plane, and closes the dock if the excavate flow opened it.
- **Verified with real CDP clicks:** open → `ugDockVisible=true, brushMode='dig', clipActive=true`; close → `ugVisible=false, brushMode='raise', clipActive=false`. JS errors: none.

### 4. Cross-Section panel micro-scroll
- **Before:** `scrollHeight=200 > clientHeight=189` — canvas 200px forced an 11px scroll in the panel.
- **Fix:** `#cross-section-canvas` height 200→176px + `display:block`. After: `scrollH == clientH == 189`.

### 5. Pre-existing crash: `activeTab.getAttribute is not a function` (caught by audit)
- `applyMode('basic')` called `.getAttribute()` on `window._dockActiveTab()`, which returns the dock id **string**, not an element. Switching to Basic with an advanced dock open threw a TypeError **and left the hidden dock open** (orphaned `dock-underground` visible in Basic mode).
- **Fix:** handle the string return; Basic mode now closes hidden-in-basic docks. **Verified:** orphan panels after advanced→basic switch = `[]`; zero JS errors.

### 6. Basic / Advanced mode cleanliness
- Basic mode correctly hides underground/analyze/innovate/measure/experience tabs and the advanced topbar buttons (audit confirms those triggers are non-clickable in Basic — expected per Sprint 17 spec; screenshots exist for every surface that is reachable in each mode).
- Advanced mode shows all 7 dock tabs and everything renders.
- Advanced→Basic switch leaves no orphaned panels and no JS errors.

### Surfaces audited clean (no changes needed)
Cost, Layer, Season, Growth, Permit panels; Help/Templates/Share modals; Command Palette; Context menu (built-in viewport-edge clamping works); Wizard; Welcome prompt; Analyze/Innovate/Sun/Measure/Experience docks — all controls within viewport, no scroll-orphaning, no overlaps.

---

## Verification

| Gate | Result |
|---|---|
| `sprint17_quality_gate.py` (port 8175) | **81 / 81 PASS** |
| `sprint11_quality_gate.py` (port 8115) | **143 / 143 PASS** |
| `sprint15_quality_gate.py` (port 8095/8099) | 51 / 52 — `static:brightness_boost_25pct` fails; **pre-existing at baseline** `da1163f` (Sprint 20 deliberately changed `UNDERGROUND_BRIGHTNESS_BOOST` 0.25→0.45; the stale static check expects 0.25). Not touched by this sprint. |
| CSS brace balance after edits | 890 open / 890 close — balanced |
| File size | 748,796 bytes ≤ 750KB (768,000 safety limit) ✓ |
| JS console errors after all fixes | 0 |

**Element IDs / data attributes preserved:** all (`data-tmode`, `data-cshape`, `data-preset`, `#terrain-flatten`, `#carving-*`, `#grid-level-*`, `#excavate-*`, `#cross-section-*`, etc.). No features removed.

## Key before/after screenshots
- `reports/sprint21_shots/before/dock-terrain-live.png` vs `after/advanced-dock-terrain.png` (scroll-orphan fixed)
- `before/verify-toolbar...` / `after/verify-toolbar.png` (quick-access buttons restored)
- `after/verify-excavate-open.png` (underground dock + clip plane via Excavate)
- `after/verify-carving-expanded.png` (collapsible section expanded)
- `after/advanced-switch-to-basic.png` (no orphan panels)
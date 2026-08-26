# UI Overlaps Fix Report — Sprint 19

## Summary

Fixed all overlapping UI elements in Backyard Designer 3D by:
1. Reorganizing bottom-left toolbar buttons into a flex container
2. Creating a right-side panel stack container for clean vertical stacking
3. Fixing z-index hierarchy with unique values per layer
4. Verifying with Playwright screenshots and bounding box overlap detection

**Result: 0 overlaps across all test scenarios. 81/81 quality gate tests passing.**

---

## Overlaps Found and Fixed

### 1. Bottom-Left Toolbar Button Overlaps (FIXED)

**Problem:** Multiple buttons positioned with absolute `left:` values at `bottom: 16px`:
- `excavate-btn` at left:460px and `terrain-analysis-btn` at left:480px — only 20px apart, guaranteed overlap
- `sun-btn` at left:410px, `innovation-btn` at left:530px — incremental positioning with no flex flow
- All buttons at z-index:10, same as viewport overlays

**Fix:**
- Created `#bottom-left-toolbar` flex container at `bottom:16px; left:380px` (right of tool-dock)
- JavaScript moves all 6 toolbar buttons into the container on page load
- Buttons now flow left-to-right with `gap: 6px`, wrapping to second row if needed
- `max-width: calc(100% - 460px)` prevents overlap with view-controls on the right
- All buttons set to `z-index: 30` (bottom toolbar layer)
- Popup panels (terrain-controls, excavate-panel, etc.) repositioned to `left:380px` to open above the toolbar
- Popup panels set to `z-index: 30`

**Elements affected:**
- `#tape-measure-btn` — moved to flex container, z-index 10→30
- `#terrain-btn` — moved to flex container (z-index was default 10)
- `#excavate-btn` — moved to flex container, z-index 10→30
- `#terrain-analysis-btn` — moved to flex container, z-index 10→30
- `#innovation-btn` — moved to flex container, z-index 10→30
- `#sun-btn` — moved to flex container, z-index 10→30
- `#terrain-controls` — repositioned left:330px→380px, z-index added:30
- `#excavate-panel` — repositioned left:460px→380px, z-index 10→30
- `#terrain-analysis-panel` — repositioned left:480px→380px, z-index 50→30
- `#sun-panel` — repositioned left:410px→380px, z-index 10→30
- `#innovation-panel` — repositioned left:530px→380px, z-index 10→30
- `#ta-cross-section-overlay` — z-index 50→30

### 2. Right-Side Panel Stacking Overlaps (FIXED)

**Problem:** Multiple panels at conflicting positions:
- `cost-panel` at top:16px, right:16px, z-index:30
- `layer-panel` at top:200px, right:16px, z-index:25
- `cross-section-panel` at top:16px, right:340px, z-index:50
- `cut-fill-panel` at top:16px, right:340px, z-index:40 — **SAME POSITION as cross-section-panel**
- `compass-indicator` at top:60px (then top:120px), right:16px, z-index:50 — **OVERLAPS with cost-panel**
- `depth-gauge-overlay` at top:16px, right:16px, z-index:50 — **OVERLAPS with cost-panel**
- `season-panel` at top:200px, right:16px, z-index:50 — **OVERLAPS with layer-panel**
- `growth-panel` at top:380px, right:16px, z-index:50
- `permit-panel` at top:200px, right:340px, z-index:50

**Fix:**
- Created `#right-panel-stack` flex container at `top:16px; right:16px`
- JavaScript moves all right-side panels into the container on page load
- Panels stack vertically with `gap: 8px`, `flex-direction: column`
- Container has `max-height: calc(100vh - 100px); overflow-y: auto` for scrolling
- `pointer-events: none` on container, `pointer-events: auto` on children
- Each panel's `position: absolute` is overridden to `position: relative` inside the stack
- z-index hierarchy: cost/layer/compass/depth-gauge/season/growth at z-index:40, cross-section/cut-fill/permit at z-index:50

**Elements affected:**
- `#cost-panel` — moved to right-panel-stack, z-index 30→40, position overridden to relative
- `#layer-panel` — moved to right-panel-stack, z-index 25→40, position overridden to relative
- `#cross-section-panel` — moved to right-panel-stack, z-index stays 50, position overridden to relative
- `#cut-fill-panel` — moved to right-panel-stack, z-index 40→50, position overridden to relative
- `#compass-indicator` — moved to right-panel-stack, z-index 50→40, position overridden to relative
- `#depth-gauge-overlay` — moved to right-panel-stack, z-index 50→40, position overridden to relative
- `#season-panel` — moved to right-panel-stack, z-index 50→40, position overridden to relative
- `#growth-panel` — moved to right-panel-stack, z-index 50→40, position overridden to relative
- `#permit-panel` — moved to right-panel-stack, z-index stays 50, position overridden to relative
- `#walk-exit` — conditional move (only when not inside walk-controls), z-index stays 200
- `#cost-panel.shifted` — overridden to `right: auto` inside stack (no longer needed)

### 3. Z-Index Hierarchy (FIXED)

**Problem:** Duplicate z-index values causing unpredictable stacking:
- 11 elements at z-index:50
- 8 elements at z-index:200
- 8 elements at z-index:10

**Fix:** Assigned unique z-index values per layer:

| z-index | Layer | Elements |
|---------|-------|----------|
| 1 | Canvas/sky-dome | `#sky-dome`, `#viewport canvas` |
| 10 | Viewport overlays | `.viewport-overlay`, `#measure-readout`, `#terrain-height-legend`, `#grid-level-badge` |
| 15 | Scale-bar | `#scale-bar`, `#atmosphere-badge` |
| 20 | View controls | `#view-controls` |
| 25 | Dock tabs | `#tool-dock`, `#dock-panel-container` |
| 30 | Bottom toolbar + popups | All 6 toolbar buttons, 5 popup panels, `#ta-cross-section-overlay`, `.discovery-badge` |
| 40 | Right-side panels (base) | `#cost-panel`, `#layer-panel`, `#compass-indicator`, `#depth-gauge-overlay`, `#season-panel`, `#growth-panel` |
| 50 | Right-side panels (high) | `#cross-section-panel`, `#cut-fill-panel`, `#permit-panel` |
| 100 | Topbar | `#topbar` |
| 150 | Toast/walk-controls | `#toast`, `#walk-controls` |
| 200 | Modals/wizard/walk-exit | `#walk-exit`, `#ctx-menu`, `#ctx-tooltip`, `#progressive-hint` (was 200) |
| 500 | Progressive hint | `#progressive-hint` (moved from 200→500) |
| 9999 | Command palette | `#cmd-palette-overlay`, `#desktop-gate`, `.mi-progress` |

**Specific z-index changes:**
- `#tool-dock`: 20→25
- `#dock-panel-container`: 19→25
- `#terrain-analysis-btn`: 10→30
- `#terrain-analysis-panel`: 50→30
- `#ta-cross-section-overlay`: 50→30
- `#cut-fill-panel`: 40→50
- `#terrain-height-legend`: 40→10
- `#measure-readout`: 50→10
- `#excavate-btn`: 10→30
- `#excavate-panel`: 10→30
- `#sun-btn`: 10→30
- `#sun-panel`: 10→30
- `#innovation-btn`: 10→30
- `#innovation-panel`: 10→30
- `#grid-level-badge`: 50→10
- `#depth-gauge-overlay`: 50→40
- `#compass-indicator`: 50→40
- `#season-panel`: 50→40
- `#growth-panel`: 50→40
- `#cost-panel`: 30→40
- `#layer-panel`: 25→40
- `#progressive-hint`: 200→500
- `.discovery-badge`: 50→30

### 4. Scale-Bar Repositioning (FIXED)

**Problem:** `#scale-bar` at `bottom:16px; left:16px` overlapped with `#tool-dock` at same position.

**Fix:** Moved scale-bar to `left:170px` (right of tool-dock which is ~139px wide).

### 5. Progressive-Hint Repositioning (FIXED)

**Problem:** `#progressive-hint` at `bottom:80px` overlapped with `#toast` at `bottom:70px` when both visible.

**Fix:** Moved progressive-hint to `bottom:120px` (50px above toast).

---

## Verification

### Playwright Screenshot Tests (0 overlaps)

Tested 10 scenarios with bounding box overlap detection:
1. **Baseline** (no panels open): 0 overlaps ✓
2. **Cost + Layer panels**: 0 overlaps ✓
3. **Cross-section + Cut-fill panels**: 0 overlaps ✓
4. **All right panels open** (7 panels): 0 overlaps ✓
5. **Bottom-left toolbar buttons** (6 buttons force-shown): 0 overlaps ✓
6. **Popup: terrain-controls**: 0 overlaps ✓
7. **Popup: excavate-panel**: 0 overlaps ✓
8. **Popup: terrain-analysis-panel**: 0 overlaps ✓
9. **Popup: sun-panel**: 0 overlaps ✓
10. **Popup: innovation-panel**: 0 overlaps ✓
11. **Depth-gauge + compass + cost**: 0 overlaps ✓

### Sprint 17 Quality Gate: 81/81 tests passing ✓

---

## Implementation Details

### JavaScript Container Injection

A script injected at the top of `#viewport` creates two containers and moves elements into them on DOMContentLoaded + delayed re-runs (100ms, 500ms) to catch dynamically added elements:

```javascript
// Bottom-left toolbar: moves 6 toolbar buttons into #bottom-left-toolbar
// Right-side panel stack: moves 10 panels into #right-panel-stack
// walk-exit is skipped if inside #walk-controls (walk mode)
```

### CSS Overrides

For each panel moved into a container, CSS rules override `position: absolute` to `position: relative` and reset `top/right` to `auto`, allowing the flex container to handle positioning.

### Files Modified

- `index.html` — CSS z-index fixes, container creation, positioning fixes, JS container injection

### Screenshots

All screenshots saved to `screenshots/` directory:
- `fix-baseline.png` — Default state
- `fix-cost-layer.png` — Cost + Layer panels
- `fix-crosssection-cutfill.png` — Cross-section + Cut-fill
- `fix-all-right-panels.png` — All 7 right panels open
- `fix-bottom-left-buttons.png` — All 6 toolbar buttons visible
- `fix-popup-*.png` — Individual popup panels
- `fix-depth-compass-cost.png` — Depth gauge + compass + cost
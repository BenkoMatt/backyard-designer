# Sprint 14 — Precision Brush Controls: Discovery Log

**Agent:** Agent 3  
**Sprint:** 14  
**Role:** Precision Brush Controls  
**Date:** 2026-08-24  
**Working Copy:** `/root/byd14-precision-brush/index.html`

---

## Initial State

- **File size:** 17,068 lines, 728,644 bytes
- **Git state:** Clean working tree, last commit `bb9bcd3` (Sprint 13 merge)
- **Baseline tests:** Sprint 13 Quality Gate — 34/34 tests passing, 0 console errors
- **Test infrastructure:** Playwright + Chromium available, `sprint13_quality_gate.py` runner

---

## Discovery: Key Code Locations

### Terrain Controls HTML (~line 2240-2300)
- Brush size slider: `#terrain-brush-size` — was `min=3, max=30, step=1`
- Brush strength slider: `#terrain-strength` — was `min=0.01, max=1.0, step=0.01`
- Dig depth slider: `#dig-depth-slider` — was `min=0, max=30, step=1`
- Terrain mode buttons: `data-tmode` = raise, lower, smooth, erode, dig, fill
- Precision mode toggle with max=10 size, max=0.2 strength limits

### Old Shape-Selection Carving UI (~line 2308-2372)
- `#carve-shape-btns` — None/Box/Cylinder/Sphere buttons (data-cshape)
- `#carve-size-slider` — Carve size, `#carve-depth-slider` — Carve depth
- `#carve-hint` — "Click on terrain to preview, click again to carve"
- `.carving-section` — Carving Tools with box/cylinder/trench + commit button
  - `#carving-depth`, `#carving-width`, `#carving-length` sliders
  - `#carving-commit-btn` — Two-click commit button
  - `#carving-clear-btn` — Clear all carvings
  - `#carving-hint` — Carving instructions
  - `#carving-preview-info` — Preview info display

### Excavate Panel (~line 2406-2445)
- `#excavate-panel` — "Underground View" viewport overlay
- Contains: cutaway slider, opacity slider, wireframe toggle, cross-section toggle, buried objects panel
- **Already migrated to dock:** JS at line ~13046 moves children to `#dock-underground-content`
- `#excavate-btn` toggles panel visibility (still in viewport)
- `#excavate-close` closes the panel

### Terrain Constants (~line 4243-4253)
- `terrainSegs: 300` — terrain mesh resolution
- `MAX_TERRAIN_HEIGHT = 30`, `MIN_TERRAIN_HEIGHT = -30`
- `clampTerrainHeight()` function

### Brush Cursor (~line 8232-8291)
- `terrainBrushMesh` — THREE.Line ring mesh following mouse on terrain
- `createBrushCursor()` — Creates ring with 48 segments, color 0x8B5E3C (brown)
- `updateBrushCursorSize()` — Resizes ring based on brush size
- `moveBrushCursor()` — Moves ring to mouse position on terrain surface
- **No color-coding by tool** — fixed brown color

### paintTerrain Function (~line 7901-8015)
- Modes: raise, lower, smooth, erode, dig, fill
- Dig/fill branch (line 7908) calls `carveWithBrush`/`fillWithBrush` for voxel carving only
- Does NOT modify terrain mesh height in dig mode (only voxels)
- Uses cosine falloff for raise/lower, Gaussian kernel for smooth

### Depth Readout (~line 6983-6996)
- `updateDigDepthReadout()` — Shows "Digging to:" / "Filling to:" with depth value
- `updateHeightReadout()` — Shows "Height at cursor:" with terrain height

### Test Objects
- Sprint 12 quality gate tests `terrainSegs=300` and `MAX/MIN_TERRAIN_HEIGHT=30/-30` — these will fail with new values (expected, task requires changes)
- Sprint 13 quality gate does NOT test these specific values — all 34 tests pass

---

## Changes Made

1. **Brush size slider:** Changed to `min=1, max=30, step=0.5`
2. **Strength slider:** Changed to `min=0.005, max=0.5, step=0.005`
3. **Flatten button:** Added `data-tmode="flatten"` button between Erode and Dig
4. **Flatten mode in paintTerrain:** Computes average height in brush area, blends toward it
5. **Dig brush improvement:** Now lowers terrain mesh toward `-digDepth` with cosine falloff + carves voxels
6. **Brush cursor color-coding:** Added `BRUSH_CURSOR_COLORS` map and `updateBrushCursorColor()` function
   - green=raise, orange=lower, blue=smooth, dark orange=erode, gray=flatten, brown=dig, light green=fill
7. **Depth indicator:** Updated `updateDigDepthReadout()` to show "Depth below surface:" for Dig mode
8. **Removed old shape-selection carving UI:**
   - `#carve-shape-btns`, `#carve-size-slider`, `#carve-depth-slider`, `#carve-hint` (the carve-hint)
   - Entire `.carving-section` with box/cylinder/trench + commit + clear buttons
   - `#excavate-panel` viewport overlay (content migrated directly to `#dock-underground-content`)
9. **terrainSegs:** Changed from 300 to 200
10. **MAX_TERRAIN_HEIGHT:** Changed from 30 to 15
11. **MIN_TERRAIN_HEIGHT:** Changed from -30 to -15
12. **Dig depth slider:** Changed max from 30 to 15, step from 1 to 0.5
13. **Grid level slider:** Changed range from -30..30 to -15..15
14. **Depth gauge:** Updated relative height divisor from 30 to 15
15. **Strength display:** Changed from 2 decimal places to 3 (for 0.005 step)
16. **Null guards:** Added null guards for all removed element JS references

---

## Testing Results

- **Sprint 13 Quality Gate:** 34/34 tests passing, 0 console errors
- **Sprint 14 Precision Brush Tests:** 28/28 tests passing, 0 console errors
- **Mobile (375px):** 0 console errors, Flatten button present
- **Flatten mode:** Verified to reduce terrain variance (beforeVar=2.477 → afterVar=2.196)
- **Dig mode:** Verified to lower terrain (centerH=-1.500 after one stroke with strength=0.3, digDepth=5)
- **Brush cursor colors:** All 7 tool colors present and correct
- **Old carving UI:** Confirmed removed from DOM
- **Underground view:** Confirmed content in dock panel
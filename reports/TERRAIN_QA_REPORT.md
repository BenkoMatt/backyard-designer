# TERRAIN QA REPORT — Sprint 20 (Quality of Life Audit)

**Agent:** Agent 3 — Terrain QA  
**Date:** 2026-08-26  
**Working copy:** `/root/byd20-terrain-qa/index.html`  
**Baseline commit:** `2f5b76b` (Sprint 20 baseline)

---

## Executive Summary

All 7 terrain sculpting modes verified working. Geological layer coloring confirmed correct and visually distinct. The long-standing "can't see into the ground" issue has been **FIXED** with an auto-dig clip plane that automatically reveals geological layers when the user enters Dig mode.

### Key Fix: "Can't See Into the Ground"

**Problem:** When digging a hole, the terrain mesh (`yardMesh`) forms a continuous smooth bowl. The green grass surface wraps around the entire bowl, hiding the `solidEarthMesh` interior walls that display geological layer colors (topsoil, subsoil, clay, bedrock). The vertex colors on the terrain surface ARE correct (center of a -15ft hole is gray bedrock), but the camera can't see them because the terrain mesh surface covers the opening from above.

**Root Cause:** The terrain mesh is a `PlaneGeometry` with `DoubleSide` rendering — it's a continuous surface with no holes. When you dig, the surface dips down but remains intact, creating a bowl shape. The `solidEarthMesh` with interior walls and geological colors is built correctly underneath, but it's fully occluded by the terrain surface above it.

**Solution Implemented:** Auto-dig clip plane (`autoDigClipPlane`):
- When the user selects **Dig** brush mode, a horizontal clipping plane at `y=0` (ground level) is automatically applied to `yardMesh` only
- This clips away the terrain surface below ground level, revealing the `solidEarthMesh` interior walls with geological layer colors
- The `solidEarthMesh` is **NOT** clipped by this plane, so geological layers remain fully visible
- When the user switches away from Dig mode, the clip plane is automatically removed
- The clip plane coexists with existing manual clip planes (`terrainClipPlane` from the Cutaway slider, `crossSectionClipPlane` from Cross-Section tool) via `_rebuildYardClipPlanes()`
- All clip plane management code (cutaway slider, cross-section, clear-carvings, flatten) was updated to use `_rebuildYardClipPlanes()` to preserve the auto-dig clip when active

**Files modified:** `index.html` — ~15 locations updated:
1. New variables: `autoDigClipPlane`, `_rebuildYardClipPlanes()`, `updateAutoDigClip()`
2. Brush mode change handler: calls `updateAutoDigClip()` on mode switch
3. `buildYardMesh()`: uses `_rebuildYardClipPlanes()` instead of direct clipping plane assignment
4. Cutaway slider handler: uses `_rebuildYardClipPlanes()`
5. Cross-section clip handler: uses `_rebuildYardClipPlanes()`
6. Flatten button handler: uses `_rebuildYardClipPlanes()`
7. Clear-carvings handler: uses `_rebuildYardClipPlanes()`
8. `window` exports: `paintTerrain`, `_flushTerrainFull`, `autoDigClipPlane`, `updateAutoDigClip`, `_rebuildYardClipPlanes`
9. `_test` object: exposed `autoDigClipPlane`, `updateAutoDigClip`, `_rebuildYardClipPlanes`

---

## Audit Results

### 1. Terrain Deformation — All 7 Brush Modes ✅

| Mode | Status | Details |
|------|--------|---------|
| raise | ✅ PASS | terrain changed, maxChange=7.40ft, range=[0.00, 7.40] |
| lower | ✅ PASS | terrain changed, maxChange=7.40ft, range=[-7.40, 0.00] |
| smooth | ✅ PASS | terrain changed (on bumpy terrain), variance reduced |
| flatten | ✅ PASS | terrain changed, maxChange=6.47ft, terrain leveled toward target |
| erode | ✅ PASS | terrain changed, material moved from high to low cells |
| dig | ✅ PASS | terrain changed, maxChange=15.00ft, range=[-15.00, 0.00] |
| fill | ✅ PASS | terrain changed, maxChange=15.00ft, range=[0.00, 15.00] |

### 2. Terrain Height Clamping (±15ft) ✅

- Max height after 200 aggressive raise strokes: **15.000ft** (clamped at +15)
- Min height: **0.000ft** (flat terrain baseline)
- `clampTerrainHeight()` enforces `[-15, 15]` correctly

### 3. Vertex Colors at Different Depths ✅

- At -15ft (max dig depth): color = `(0.539, 0.539, 0.584)` — gray bedrock ✅
- Not green (grass color) at depth ✅
- Geological colors applied via `_getNamedGeoLayerColor()` with 1.45x brightness boost
- Depth banding every 2ft for visual layering

### 4. Geological Layer Colors — Visually Distinct ✅

| Layer | Depth Range | Color (RGB) | Visual |
|-------|------------|-------------|--------|
| topsoil | 0 to -2ft | (0.29, 0.19, 0.12) | Rich dark brown |
| subsoil | -2 to -6ft | (0.61, 0.48, 0.31) | Warm brown |
| clay | -6 to -12ft | (0.72, 0.33, 0.19) | Red/orange |
| bedrock | -12 to -15ft | (0.38, 0.38, 0.41) | Gray |

- All 4 layers pairwise distinct (min distance > 0.05) ✅
- Bedrock is gray (R≈G) ✅
- Clay is reddish (R > G > B) ✅
- Smooth transitions at boundaries (0.75ft transition width)

### 5. Solid Earth Mesh Rebuild ✅

- `buildSolidEarth()` creates interior walls + floor cap in dug areas
- Vertex count before dig: 3,204 (flat terrain — perimeter walls only)
- Vertex count after dig: 9,772 (interior walls + floor cap added)
- Rebuilt during painting via `_debouncedApplyTerrainFull()` (80ms debounce)
- Rebuilt immediately on pointer-up via `_flushTerrainFull()`

### 6. Debouncing ✅

- `TERRAIN_FULL_DEBOUNCE_MS = 80ms`
- During active painting: `applyTerrainPositions()` (fast, positions only) + `_debouncedApplyTerrainFull()` (debounced full update)
- `_terrainFullPending` flag correctly set during painting, cleared after debounce fires
- Test: pending=true during painting, pending=false after 200ms wait ✅

### 7. Flush on Pointer-Up ✅

- `onTerrainPointerUp()` calls `_flushTerrainFull()` on line 8176
- `_flushTerrainFull()` clears any pending debounce timer and calls `applyTerrainFull()` immediately
- Test: pending=false after flush ✅

### 8. Console Errors ✅

- **0 console errors** during all terrain operations
- **0 page errors** during testing

### 9. Terrain Normals Recomputed ✅

- `applyTerrainFull()` calls `geo.computeVertexNormals()` on line 7658
- `applyTerrainPositions()` deliberately skips normal computation for speed (line 7631)
- Test: edge normal y=0.8775 (tilted from vertical 1.0) after terrain deformation ✅
- `buildSolidEarth()` also calls `geo.computeVertexNormals()` for the solid earth mesh

### 10. Geological Layer Visibility (Dig Visibility Fix) ✅

- **FIXED**: Auto-dig clip plane automatically applied when entering Dig mode
- `yardMesh` clipped below y=0 → terrain surface removed in dug areas
- `solidEarthMesh` NOT clipped → geological layer interior walls fully visible
- Clip plane removed automatically when switching away from Dig mode
- Coexists with manual Cutaway and Cross-Section clip planes
- Test: autoClip on yardMesh=true, solidEarth NOT clipped=true, removed on mode switch=true ✅

---

## Quality Gate Results

### Sprint 15 Quality Gate (Terrain-Specific)
- **51/52 tests passed** (98.1%)
- 1 failure: `static:brightness_boost_25pct` — expects `UNDERGROUND_BRIGHTNESS_BOOST = 0.25`, but Sprint 19 intentionally increased this to `0.45` for better visibility. This is a **stale test expectation**, not a regression.
- All browser tests passed: geological colors, interior walls, bottom cap, transitions, underground lighting, FPS during painting, regression checks, no console errors

### Sprint 17 Quality Gate
- **81/81 tests passed** (100%)
- All mode toggle, sidebar, topbar, canvas, keyboard shortcut, command palette, and console error checks passed

### Sprint 20 Terrain QA (Custom)
- **14/14 tests passed** (100%)
- 7 brush modes, height clamping, vertex colors, geological layers, solid earth rebuild, debounce, flush, normals, auto-dig clip

---

## Technical Implementation Details

### Auto-Dig Clip Plane Architecture

```
When terrainBrushMode === 'dig':
  → updateAutoDigClip() creates autoDigClipPlane = Plane(normal=(0,1,0), constant=0)
  → _rebuildYardClipPlanes() adds it to yardMesh.material.clippingPlanes
  → solidEarthMesh.material.clippingPlanes is NOT modified
  → Result: yardMesh surface below y=0 is clipped away, solidEarthMesh visible

When terrainBrushMode changes away from 'dig':
  → updateAutoDigClip() sets autoDigClipPlane = null
  → _rebuildYardClipPlanes() rebuilds without the auto-dig plane
  → Result: yardMesh surface fully visible again
```

### Clip Plane Coexistence

`_rebuildYardClipPlanes()` preserves all active clip planes:
1. `terrainClipPlane` (from Cutaway slider) — if set
2. `crossSectionClipPlane` (from Cross-Section tool) — if set  
3. `autoDigClipPlane` (auto-dig) — if in Dig mode

All manual clip plane management code was updated to call `_rebuildYardClipPlanes()` instead of directly assigning `clippingPlanes` arrays, ensuring the auto-dig clip is preserved when other clip planes are toggled.

---

## Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `index.html` | Modified | Auto-dig clip plane implementation + window exports |
| `terrain_qa_sprint20.py` | Created | Comprehensive terrain QA test suite |
| `terrain_qa_sprint20_results.json` | Created | Test results JSON |
| `TERRAIN_QA_REPORT.md` | Created | This report |
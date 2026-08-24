# Sprint 15 Agent 1: Interior Earth Walls — Report

## Objective
Build interior walls wherever terrain drops, so dug holes show earth cross-sections with geological layers instead of a green void.

## Problem
`buildSolidEarth()` (line ~7190) only built walls at the 4 yard boundary edges. When a user dug a hole in the terrain, they saw a green void — no earth walls inside the hole showing the geological cross-section.

## Solution
Added interior wall scanning code in `buildSolidEarth()`, after the 4 boundary wall strips and before the geometry creation. The code:

1. **Iterates over the terrain grid** (segs+1 × segs+1 vertices)
2. **Skips vertices at or above height 0** — only processes dug areas (terrain < 0)
3. **Checks 2 neighbors per vertex**: right (ix+1) and down (iz+1)
   - Only 2 directions needed to cover all edges without duplication (each edge is checked once from the lower-indexed vertex)
4. **Height difference threshold**: 1.0 ft — if `|h - hNeighbor| > 1.0`, build a wall quad
5. **Additional condition**: at least one side must be below 0 (dug area) — prevents walls on hills
6. **Wall quad construction**: 4 vertices (2 top at higher terrain height, 2 bottom at bottomY), 2 triangles for the quad
7. **Geological layer coloring**: surfaceHeights tracks the higher vertex's height, so the existing vertex color code applies `_getNamedGeoLayerColor(depthBelowSurface)` correctly — showing topsoil, subsoil, clay, and bedrock layers in the cross-section

## Code Changes

### 1. Interior wall scanning in `buildSolidEarth()` (after line 7263)
- Added `INTERIOR_WALL_THRESHOLD = 1.0` constant
- Added nested loop scanning all vertices, checking right and down neighbors
- Builds wall quads where height differences exceed threshold in dug areas
- Uses same `positions`, `indices`, `surfaceHeights` arrays as boundary walls
- Same `MeshStandardMaterial` with `vertexColors: true` and `DoubleSide`

### 2. Fixed duplicate `buildSolidEarth()` calls
- **Line ~7398**: `applyTerrainFull()` had `buildSolidEarth()` called twice — removed duplicate
- **Line ~15302**: `stressTestGenerate()` had `buildSolidEarth()` called twice — removed duplicate

## Testing

### Test Results (Playwright + headless Chromium)

| Test | Description | Expected | Result | Status |
|------|-------------|----------|--------|--------|
| Hill test | Terrain raised to +5ft hill | 0 interior wall vertices | 0 extra vertices | **PASS** |
| Flat test | Flat terrain (all zeros) | 0 interior wall vertices | 0 extra vertices | **PASS** |
| Dig test | Sharp hole dug to -5ft | Interior walls present | 1496 extra vertices, 373 wall quads | **PASS** |

### Key Metrics (dig test)
- Boundary-only vertices: 3204 (4 bottom + 4 strips × 200 segs × 4 verts)
- With interior walls: 4700 vertices
- Extra vertices from interior walls: 1496
- Interior wall quads: ~373
- Edge differences > 1ft detected: 432
- Console errors: 0

### Debounce
Interior wall construction is debounced via the existing `applyTerrainFull()` debounce (80ms via `_debouncedApplyTerrainFull`). `buildSolidEarth()` is called from `applyTerrainFull()`, so interior walls rebuild automatically during painting with proper debounce coalescing.

## Files Modified
- `/root/byd15-interior-walls/index.html` — interior wall code added, duplicate calls fixed

## Files Created
- `test_interior_walls.js` — Playwright test script
- `test_verification.js` — Verification test suite (3 tests)
- `DISCOVERY_LOG.md` — Discovery log
- `INTERIOR_WALLS_REPORT.md` — This report
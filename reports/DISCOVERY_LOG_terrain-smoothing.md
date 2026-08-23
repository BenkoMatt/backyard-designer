# DISCOVERY LOG — Sprint 10, Agent 1 (Terrain Smoothing)

## Session Info
- **Agent**: Agent 1 (Builder) — Terrain Resolution & Smoothing
- **Sprint**: 10
- **Date**: 2026-08-23
- **Working Directory**: /root/byd10-terrain-smoothing/
- **Starting File**: index.html (16,163 lines → 16,227 lines)

## Discovery 1: Terrain Architecture
- **Terrain mesh**: `PlaneGeometry(width, depth, terrainSegs, terrainSegs)` — single mesh, `yardMesh`
- **terrainSegs**: Was 100 (10,201 vertices), now 200 (40,401 vertices)
- **Material**: Was `MeshLambertMaterial`, now `MeshStandardMaterial` with `flatShading: false, roughness: 0.95, metalness: 0.0`
- **Terrain data**: `Float32Array` of size `(segs+1)²` stored in `state.terrain`
- **Terrain application**: `applyTerrainToMesh()` copies heights to geometry, calls `computeVertexNormals()`

## Discovery 2: Brush System
- **paintTerrain()** function at line ~7327 handles all brush modes
- **Original falloff**: `Math.pow(1 - t*t, 2)` — polynomial, decent but not ideal
- **New falloff**: `(Math.cos(t * Math.PI) + 1) * 0.5` — smooth cosine curve
- **Brush modes**: raise, lower, smooth, erode — all use same falloff
- **Smooth mode**: Was 3x3 neighborhood, now 5x5 with distance-weighted averaging

## Discovery 3: Voxel System Independence
- **VOXEL_SIZE = 2** (fixed, 2ft voxels)
- Voxel dimensions computed from `yard.width/depth / VOXEL_SIZE`, NOT from `terrainSegs`
- Voxel carving system is completely independent of terrain resolution
- **CRITICAL**: Changing terrainSegs does NOT affect voxel carving — confirmed by tests

## Discovery 4: Serialization Compatibility
- `serializeDesign()` saves `terrainSegs` in the design JSON
- `loadDesign()` detects terrain array length and auto-detects segs from it
- Old designs with 100 segs will auto-detect and load correctly
- New designs save with segs=200, old designs load with their original segs
- Compact hash encoding only saves `terrainSegs` if ≠ default (now 200)

## Discovery 5: Smooth Shading
- `computeVertexNormals()` was already called after every terrain modification
- Confirmed at: `applyTerrainToMesh()`, `flattenAllTerrain`, `stressTestClear`, and other locations
- With `MeshStandardMaterial` + `flatShading: false`, normals produce smooth Gouraud shading
- All 8+ call sites verified to have `computeVertexNormals()` after position updates

## Discovery 6: Performance Characteristics
- **Headless swiftshader** (software rendering): FPS very low (~0.1-1.0) — not representative of real GPU
- **40,401 vertices** is trivial for any modern GPU (handles millions)
- **Key metric**: Smoothness improved dramatically
  - Before: avgNeighborDiff=0.0124, maxNeighborDiff=0.0568
  - After: avgNeighborDiff=0.0018, maxNeighborDiff=0.0230
  - Improvement: ~7x smoother average, ~2.5x smoother maximum

## Discovery 7: Brush Falloff Verification
- Single brush stroke at center produces perfect cosine curve
- Center value: 0.5000 (max strength)
- Edge values: 0.2500 (smooth falloff to ~50% at ±20 vertices from center)
- Perfectly symmetric profile — no artifacts or discontinuities

## Discovery 8: Feature Compatibility
All 19 feature tests passed:
- State initialization ✓
- Terrain sculpting (raise/lower/smooth/erode) ✓
- Voxel carving ✓ (unchanged, independent system)
- Terrain presets (hill, valley, slope, terraced, poolslope) ✓
- Contour lines ✓
- Slope heatmap ✓
- Height colors ✓
- Pool excavation ✓
- Solid earth mesh ✓
- Undo/redo ✓
- Serialize/deserialize ✓
- Flatten terrain ✓
- No console errors ✓

## Files Modified
- `index.html`: terrainSegs 100→200, MeshLambertMaterial→MeshStandardMaterial, brush falloff, smooth mode, smoothTerrainPass function, Smooth Terrain button
- `test_fps.js`: FPS and smoothness test script
- `test_features.js`: Feature compatibility test script
- `TERRAIN_SMOOTHING_REPORT.md`: This report
- `DISCOVERY_LOG.md`: This discovery log
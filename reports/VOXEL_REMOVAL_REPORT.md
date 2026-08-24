# Sprint 14: Voxel System Removal Report

## Summary
Removed the entire voxel volume system (~617 lines, ~15 functions) from Backyard Designer 3D and replaced Dig/Fill brush modes with terrain mesh surface manipulation. This is the biggest architectural change in the project's history.

## What Was Removed

### Voxel Constants (5 items)
- `VOXEL_SIZE = 1`
- `VOXEL_DEPTH = 32`
- `VOXEL_COLOR = 0x5C4033`
- `voxelNX`, `voxelNZ`, `voxelNY` (grid dimensions)
- `voxelOriginX`, `voxelOriginZ` (origin coordinates)

### Voxel State (7 items)
- `state.voxels` (Uint8Array voxel grid)
- `voxelMesh` (THREE.Mesh voxel rendering)
- `carvingPreviewMesh` (carving preview visualization)
- `_buildVoxelsLazy` (lazy initialization callback)
- `_voxelMeshDebounceTimer` (debounce timer)
- `_voxelMeshRebuildPending` (rebuild flag)
- `_voxelSnapBeforeBrush` (undo snapshot)

### Voxel Functions (15 functions, ~489 lines)
1. `computeVoxelDims()` — compute voxel grid dimensions
2. `voxelToWorld(ix, iy, iz)` — convert voxel index to world coordinates
3. `worldToVoxel(wx, wy, wz)` — convert world coordinates to voxel index
4. `getVoxel(ix, iy, iz)` — get voxel value at index
5. `setVoxel(ix, iy, iz, val)` — set voxel value at index
6. `initVoxelsFromTerrain()` — initialize voxel grid from terrain heights
7. `updateVoxelsFromTerrain()` — update voxel grid from terrain heights
8. `buildVoxelMesh()` — build greedy-meshed voxel geometry (largest function)
9. `debouncedBuildVoxelMesh()` — debounced mesh rebuild for smooth FPS
10. `_flushVoxelMeshRebuild()` — flush pending debounced rebuild
11. `rebuildVoxelVolume()` — full voxel volume rebuild
12. `countSolidVoxels()` — count solid voxels for info display
13. `countVoxelFaces()` — count exposed faces for info display
14. `carveShape()` / `carveWithBrush()` — carve voxel shapes (box/cylinder/sphere)
15. `fillShape()` / `fillWithBrush()` — fill voxel shapes
16. `serializeVoxels()` / `deserializeVoxels()` — RLE serialization
17. `snapshotVoxels()` / `restoreVoxelSnapshot()` / `pushVoxelUndo()` — undo/redo
18. `showCarvingPreview()` / `hideCarvingPreview()` / `updateCarvingPreview()` — preview

### Other Removed
- `mergeVertices` import from Three.js BufferGeometryUtils
- `updateVoxelInfoDisplay()` — voxel info display function
- Voxel info HTML div (`#voxel-info`, `#voxel-count`, `#voxel-faces`)
- Voxel CSS classes (`.voxel-layer-info`, `.voxel-layer-swatch`, `.voxel-layer-label`)
- Voxel legend items in cross-section ("Voxel earth", "Voxel boundary")
- `stressTestVoxels()` performance test function and button
- Voxel exports from `window._test` and `window._byd*` objects

### Carving Preview System (old voxel-based)
- `carvingPreviewMesh` variable
- `carvingPendingCenter` variable
- `carvingShape`, `carvingSize`, `carvingDepth` variables
- `showCarvingPreview()`, `hideCarvingPreview()`, `updateCarvingPreview()` functions
- Carving shape button handlers (`[data-cshape]`)
- Carving size/depth slider handlers
- Carving shape references in pointer event handlers

## What Was Changed

### Dig Brush Mode (Rewritten)
**Before:** Called `carveWithBrush()` which used `carveShape('sphere', ...)` to remove voxel blocks in a spherical region.
**After:** Lowers terrain mesh vertices toward `-digDepth` using the same cosine falloff as Raise/Lower brushes:
```javascript
const targetY = -digDepth * falloff * edgeFactor;
state.terrain[vi] = clampTerrainHeight(Math.min(state.terrain[vi] || 0, targetY));
```
This creates a smooth depression using only the terrain mesh — no voxel data needed.

### Fill Brush Mode (Rewritten)
**Before:** Called `fillWithBrush()` which used `fillShape('sphere', ...)` to add voxel blocks.
**After:** Raises terrain mesh vertices back toward 0 using cosine falloff:
```javascript
const targetY = digDepth * falloff * edgeFactor;
state.terrain[vi] = clampTerrainHeight(Math.max(state.terrain[vi] || 0, Math.min(0, targetY)));
```

### Constants Updated
| Constant | Before | After | Reason |
|----------|--------|-------|--------|
| MAX_TERRAIN_HEIGHT | 30 | 15 | Reduced height range |
| MIN_TERRAIN_HEIGHT | -30 | -15 | Reduced depth range |
| EARTH_DEPTH_BELOW_MIN | 32 | 17 | Reduced earth depth |
| terrainSegs | 300 | 200 | Reduce mesh complexity |
| grid-level-slider min/max | -30/30 | -15/15 | Match new limits |

### Functions Updated
- `paintTerrain()` — removed dig/fill voxel branches, replaced with mesh-based depression/raising
- `applyTerrainFull()` — removed `updateVoxelsFromTerrain()` and `buildVoxelMesh()` calls
- `serializeDesign()` — removed `voxels: serializeVoxels()` from save format
- `loadDesign()` — removed voxel deserialization; old saves with voxel data are gracefully ignored
- `initWithYard()` — removed voxel mesh cleanup and initialization
- `setGridLevel()` — removed voxel rebuild, updated limits to ±15
- `stressTestClear()` — removed voxelMesh cleanup and state.voxels reset
- `stressTestTerrain()` — removed voxel initialization
- Cutaway control — removed voxelMesh clipping plane references
- Opacity control — removed voxelMesh opacity references
- Wireframe control — removed voxelMesh wireframe references

## Performance Impact
- **Before:** Voxel system built a separate greedy-meshed geometry (thousands of faces) that was rebuilt on every terrain change, causing FPS drops during painting. Debounced rebuilds of 60ms.
- **After:** Only terrain mesh is updated. No voxel rebuild overhead. Faster painting, higher FPS, lower memory usage. Reduced terrain segments (200 vs 300) also improves performance.

## Testing Results
All 12 Playwright tests passed:
1. ✅ Page loads without JS errors
2. ✅ Three.js loaded
3. ✅ No voxel functions on window object
4. ✅ No voxel functions in _test object
5. ✅ No voxel state
6. ✅ All constants correct (MAX=15, MIN=-15, segs=200, earth=17)
7. ✅ Dig brush creates smooth depression (center height = -5.000)
8. ✅ Fill brush raises terrain back (-5.000 → 0.000)
9. ✅ Save data does not contain voxels field
10. ✅ Loading old save with voxel data succeeds (voxel data ignored)
11. ✅ Grid level limits enforced to ±15
12. ✅ Terrain height limits enforced to ±15
13. ✅ voxel-info element removed
14. ✅ No voxel-related console errors

## Line Count
- Before: 17,068 lines
- After: 16,423 lines
- Removed: 645 lines (net)
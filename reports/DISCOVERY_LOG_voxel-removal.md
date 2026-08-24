# Sprint 14 Agent 1: Voxel System Removal — Discovery Log

## Session Info
- Date: 2026-08-24
- Agent: Agent 1 (Voxel System Removal)
- Working copy: /root/byd14-voxel-removal/index.html
- Starting lines: 17,068
- Starting git commit: bb9bcd3 (Sprint 13)

## Discovery Process

### Phase 1: Inventory (Line-by-line scan)
Scanned all 17,068 lines for voxel references. Found:
- 268 lines containing "voxel" (case insensitive)
- 395 total occurrences of the word "voxel"
- 15 voxel functions spanning lines 7274-7761 (original numbering)
- 5 voxel constants at lines 4275-4279
- 7 voxel state variables
- 1 Three.js import (`mergeVertices`)
- Carving preview system (7 variables + 3 functions)

### Phase 2: Dependency Mapping
Mapped all interdependencies:
- `paintTerrain()` → `carveWithBrush()` / `fillWithBrush()` → `carveShape()` / `fillShape()` → `getVoxel()` / `setVoxel()` → `state.voxels`
- `applyTerrainFull()` → `updateVoxelsFromTerrain()` → `buildVoxelMesh()` → `mergeVertices()`
- `initWithYard()` → voxel mesh cleanup + `initVoxelsFromTerrain()` + `buildVoxelMesh()`
- `setGridLevel()` → `_buildVoxelsLazy` or `initVoxelsFromTerrain()` + `buildVoxelMesh()`
- `loadDesign()` → `deserializeVoxels()` → `buildVoxelMesh()`
- `serializeDesign()` → `serializeVoxels()`
- Pointer handlers → `snapshotVoxels()` / `restoreVoxelSnapshot()` / `pushVoxelUndo()`
- UI controls (cutaway/opacity/wireframe) → `voxelMesh.material` references
- Performance profiler → `stressTestVoxels()` function
- `window._test` exports → 15+ voxel-related exports
- Cross-section canvas → `voxelDepths` array for depth markers

### Phase 3: Two Carving Systems Identified
Discovered the codebase had TWO separate carving systems:
1. **OLD (voxel-based):** `carvingShape`, `carvingSize`, `carvingDepth`, `carvingPendingCenter`, `showCarvingPreview()`, `hideCarvingPreview()`, `updateCarvingPreview()` — operates on `state.voxels`
2. **NEW (mesh-based):** `carvingShapeMode`, `uxCarvingDepth`, `uxCarvingWidth`, `uxCarvingLength`, `uxCarvingPreviewMesh`, `uxCarvingPendingPoint`, `commitCarving()`, `updateCarvingPreviewUX()`, `clearCarvingPreview()` — operates on `state.terrain`

Only the OLD system was removed. The NEW system (which was already mesh-based) was preserved.

### Phase 4: Replacement Strategy
For Dig/Fill brush modes, adopted the same cosine falloff pattern used by Raise/Lower:
- `falloff = (Math.cos(t * Math.PI) + 1) * 0.5` where `t = dist / radius`
- Dig: `targetY = -digDepth * falloff * edgeFactor`; terrain lowered toward this
- Fill: `targetY = digDepth * falloff * edgeFactor`; terrain raised toward 0

This produces smooth depressions/elevations using only the terrain mesh, with no voxel data.

### Phase 5: Edge Fade
Preserved the edge fade logic from Raise/Lower brushes:
```javascript
const edgeFade = 0.1;
const fadeX = Math.min(ix / segs, 1 - ix / segs) / edgeFade;
const fadeZ = Math.min(iz / segs, 1 - iz / segs) / edgeFade;
const edgeFactor = Math.min(1, Math.min(fadeX, fadeZ));
```
This prevents terrain changes at the yard boundary.

### Phase 6: Validation
All 268 original voxel references eliminated. Final state:
- 2 remaining references (both in comments documenting the removal)
- 0 references to removed variables in actual code
- 12/12 Playwright tests passing

## Changes Applied (in order)
1. Removed `mergeVertices` import
2. Changed `terrainSegs: 300` → `200`
3. Removed `state.voxels: null`
4. Changed `MAX_TERRAIN_HEIGHT = 30` → `15`
5. Changed `MIN_TERRAIN_HEIGHT = -30` → `-15`
6. Removed `voxelMesh = null`
7. Removed `carvingPreviewMesh = null`
8. Removed `VOXEL_SIZE`, `VOXEL_DEPTH`, `VOXEL_COLOR` constants
9. Removed `voxelNX/NY/NZ`, `voxelOriginX/Z` variables
10. Removed `carvingShape`, `carvingSize`, `carvingDepth` variables
11. Removed `carvingPendingCenter` variable
12. Removed `_buildVoxelsLazy` variable and assignment
13. Removed `voxels` from `serializeDesign()`
14. Removed voxel loading from `loadDesign()` (replaced with comment)
15. Removed voxel mesh cleanup from `initWithYard()`
16. Updated `initWithYard()` else branch
17. Removed voxel init from terrain mode button handler
18. Removed carving shape button handlers
19. Removed `updateCarvingPreview()` function
20. Removed 489-line voxel function block (computeVoxelDims through pushVoxelUndo)
21. Removed `updateVoxelInfoDisplay()` function
22. Updated `setGridLevel()` — removed voxel rebuild, changed limits to ±15
23. Updated `applyTerrainFull()` — removed voxel calls
24. Rewrote `paintTerrain()` dig/fill branches — mesh-based
25. Updated `paintTerrain()` comment
26. Removed carving shape handler from `onTerrainPointerDown`
27. Removed voxel snapshot from `onTerrainPointerDown`
28. Removed carving preview from `onTerrainPointerMove`
29. Removed `_voxelSnapBeforeBrush` variable
30. Removed voxel undo/redo from `onTerrainPointerUp`
31. Removed `_flushVoxelMeshRebuild()` from `onTerrainPointerUp`
32. Removed `updateVoxelInfoDisplay()` from `onTerrainPointerUp`
33. Removed voxelMesh references from cutaway control (3 places)
34. Removed voxelMesh references from opacity control
35. Removed voxelMesh references from wireframe control
36. Changed `EARTH_DEPTH_BELOW_MIN = 32` → `17`
37. Updated grid-level-slider min/max to -15/15
38. Updated excavation hint text (-30 → -15)
39. Removed voxel-info HTML div
40. Removed voxel CSS classes
41. Removed voxel legend items
42. Removed voxel exports from `window._test` (3 blocks)
43. Removed `_bydDeserializeVoxels` / `_bydBuildVoxelMesh` exports
44. Removed `stressTestVoxels()` button, listener, function
45. Removed voxel init from `stressTestTerrain()`
46. Removed `state.voxels` and voxelMesh from `stressTestClear()`
47. Removed `stressTestVoxels` from `_techPerf`
48. Renamed `voxelDepths` to `depthMarkers` (reduced range to 15ft)
49. Updated cross-section comment
50. Removed `hideCarvingPreview()` and `carvingPendingCenter` from terrain mode exit
51. Fixed pointerleave handler
52. Fixed contextmenu handler
53. Updated remaining comments
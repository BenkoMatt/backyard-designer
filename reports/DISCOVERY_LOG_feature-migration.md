# Discovery Log — Sprint 14 Underground Feature Migration (Agent 4)

## Initial State
- Working copy: `/root/byd14-feature-migration/index.html` (17,068 lines → 17,169 lines after edits)
- Git: Sprint 13 merge commit (bb9bcd3)
- Three.js v0.160.0, single-file self-contained app

## Feature Discovery

### 1. terrainSegs (line 4243)
- **Found**: `terrainSegs: 300` in state initialization
- **Also found**: fallback default `300` in deserialization (line 5692)
- **Compact save**: `data.terrainSegs !== 200` check already present (line 9223)
- **Action**: Changed to 200 in both state init and deserialization fallback

### 2. MAX/MIN_TERRAIN_HEIGHT (line 4249-4250)
- **Found**: `MAX_TERRAIN_HEIGHT = 30`, `MIN_TERRAIN_HEIGHT = -30`
- **Used in**: `clampTerrainHeight()`, `computeVoxelDims()` (line 7277: `topY = MAX_TERRAIN_HEIGHT + VOXEL_SIZE`)
- **Action**: Changed to 15 / -15

### 3. Underground Rooms (placeUndergroundRoom, line 12385)
- **Found**: Already uses terrain lowering (not voxel carving). Modifies `state.terrain` array directly and calls `applyTerrainToMesh()`.
- **Issue**: Did NOT call `buildSolidEarth()` after terrain modification — solid earth walls would not update to show the excavated area.
- **Action**: Added `buildSolidEarth()` calls in place, undo, and redo paths.
- **Test result**: Terrain lowered to -8.0ft at center, solid earth mesh exists. ✅

### 4. Water Table (waterTableMesh, line 12306)
- **Found**: Already a separate `THREE.PlaneGeometry` mesh at `waterY = minH - depth`. No voxel dependency.
- **Uses**: `getMinTerrainHeight()` (reads terrain array), `checkWaterTableWarning()` (iterates terrain array)
- **Action**: No changes needed — already mesh-only compatible.
- **Test result**: Mesh exists, is a THREE.Mesh, has geometry, Y position -10.0. ✅

### 5. Exploded View (explodedViewActive, line 12304)
- **Found**: Only lifted `yardMesh` and scene objects. Did not show geological layers.
- **Issue**: No geological layer visualization in exploded view.
- **Action**: Created `_buildExplodedGeoLayers()` and `_removeExplodedGeoLayers()` functions. Added 4 geological layer planes (Topsoil, Clay, Sandstone, Bedrock) at their respective depths. Modified `applyExplodedView()` to:
  - Lift yardMesh upward
  - Push solidEarthMesh downward
  - Create and progressively offset geological layer planes
- Modified `resetExplodedView()` to restore all positions and remove geo layer meshes.
- **Test result**: 4 geo layer meshes created, yard lifted, solid earth exists. ✅

### 6. Cross-Section (drawCrossSection, line 11021)
- **Found**: Canvas-based 2D profile chart using `getTerrainHeight()` samples. Already mesh-only compatible.
- **3D Clipping**: `terrainClipPlane` (THREE.Plane) already applied to yardMesh, solidEarthMesh, and voxelMesh. Solid earth has geological layer vertex colors.
- **Issue**: 2D cross-section chart used voxel depth lines (`voxelDepths = [5, 10, 15, 20, 25, 30]`) instead of geological layer colors.
- **Action**: Replaced voxel depth lines with geological layer colors. Added filled geological layer regions (Topsoil #6B4423, Clay #B8860B, Sandstone #CD853F, Bedrock #696969) with 35% opacity. Added geological layer boundary lines.
- **Test result**: Canvas has 25,709 non-blank pixels. ✅

### 7. Pool Excavation (excavatePool, line 11399)
- **Found**: Already uses terrain lowering (not voxel carving). Modifies `state.terrain` array and calls `applyTerrainToMesh()`.
- **Issue**: Did NOT call `buildSolidEarth()` — same as underground rooms.
- **Action**: Added `buildSolidEarth()` calls in place, undo, and redo paths.
- **Test result**: Terrain lowered to -5.0ft, solid earth mesh exists. ✅

### 8. Volume Calculator (computeExcavationVolume, line 12564)
- **Found**: Iterates over `state.terrain` array, computing cut/fill volumes from cell areas × heights. No voxel dependency.
- **Action**: No changes needed — already mesh-only compatible.
- **Test result**: Cut 279.2 yd³, Fill 188.0 yd³. ✅

### 9. Cut-Fill (updateCutFillVolume, line 10330)
- **Found**: Iterates over `state.terrain` array with 4-corner cell averaging. No voxel dependency.
- **Action**: No changes needed — already mesh-only compatible.
- **Test result**: Cut 185.2 yd³, Fill 275.5 yd³, Net -90.3 yd³. ✅

### 10. Buried Indicators (updateAllBuriedIndicators, line 8219)
- **Found**: Iterates over `state.objects` and calls `updateBuriedIndicator(id)` which compares object Y position with `getTerrainHeight()`. No voxel dependency.
- **Action**: No changes needed — already mesh-only compatible.
- **Test result**: Objects: 1, function runs without error. ✅

## Voxel Dependencies Found (Not Removed)
The following voxel-related code still exists in the codebase but is NOT used by any of the migrated features:
- `voxelMesh`, `VOXEL_SIZE`, `carveShape`, `snapshotVoxels`, `restoreVoxelSnapshot`
- `initVoxelsFromTerrain`, `buildVoxelMesh`, `rebuildVoxelVolume`
- Carving tools UI (`carvingShape`, `carvingShapeMode`)
- These are separate terrain editing tools that still work alongside the mesh system.

## Test Infrastructure
- `_testS4` exposure object (line ~12855) — provides access to Sprint 4 feature functions
- `_test` exposure object (line ~12970) — provides access to core app functions
- Added `buildSolidEarth` and `solidEarthMesh` to `_testS4` for testing
- Added `_buildExplodedGeoLayers`, `_removeExplodedGeoLayers`, `_explodedGeoLayerMeshes` to `_testS4`
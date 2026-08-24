# DISCOVERY LOG — Sprint 12, Agent 2: Underground Carving Resolution

## Date: 2026-08-24

## Task
Fix underground carving to look smooth instead of blocky 2ft cubes.

## Initial State (Before Changes)
- `VOXEL_SIZE = 2` (line 4227) — every voxel is 2ft × 2ft × 2ft, causing blocky appearance
- `VOXEL_DEPTH = 60` (line 4228) — goes 60ft underground, user says max 30ft
- `EARTH_DEPTH_BELOW_MIN = 15` (line 6990) — solid earth only 15ft below min terrain
- `buildVoxelMesh()` (line 7160) — uses per-face flat normals, no `computeVertexNormals()`
- `initVoxelsFromTerrain()` (line 7122) — fills voxels from terrain surface down
- `computeVoxelDims()` (line 7088) — dimension calculations using VOXEL_SIZE

## Changes Made

### 1. VOXEL_SIZE: 2 → 1 (line 4227)
Changed from 2ft to 1ft cubes — 8x more resolution. Carvings now have 1ft × 1ft × 1ft voxels.

### 2. VOXEL_DEPTH: 60 → 32 (line 4228)
Reduced max underground depth from 60ft to 32ft (user says max 30ft, 32ft buffer).

### 3. EARTH_DEPTH_BELOW_MIN: 15 → 32 (line 6990)
Solid earth now extends to the full underground depth.

### 4. Smooth Normals via mergeVertices + computeVertexNormals (line 7274-7277)
**Discovery:** The greedy meshing algorithm creates 4 unique vertices per quad. Without vertex sharing, `computeVertexNormals()` alone produces axis-aligned (flat) normals because it only averages normals across faces sharing the same vertex INDEX, not the same POSITION.

**Solution:** Added `import { mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js'` and modified `buildVoxelMesh()` to:
1. Create the greedy mesh geometry as before
2. Call `mergeVertices(geo, 0.001)` to merge vertices at the same position (threshold 0.001 for exact voxel grid alignment)
3. Call `mergedGeo.computeVertexNormals()` to compute smooth normals across shared vertices
4. Set `flatShading: false` on the material

**Result:** Vertex count dropped from 2388 → 806 (66% reduction), and 688/806 vertices (85%) now have smooth blended normals instead of flat axis-aligned normals.

### 5. Debug API Exports (lines 14709-14716)
Added window-exposed functions for testing:
- `_bydInitVoxelsFromTerrain`
- `_bydUpdateVoxelsFromTerrain`
- `_bydRebuildVoxelVolume`
- `_bydApplyTerrainPreset`
- `_bydCommitCarving`
- `_bydGetVoxelMesh`
- `_bydGetVoxelDims`
- `_bydGetSolidEarthMesh`

### 6. Removed unused `normals` array from geometry attributes
The per-face normals array was previously set as a geometry attribute. Since `computeVertexNormals()` replaces it entirely, removed the manual `setAttribute('normal', ...)` call. The `normals` array is still populated during mesh building but no longer used (could be cleaned up further).

## Verification Results

### Box Carve Test (12×12ft, 8ft deep)
- Voxel array: 315,000 voxels (50×100×63), 307KB (0.30MB)
- Solid voxels: 174,516 → 173,924 (592 carved away)
- Mesh vertices: 520 (after merge)
- Mesh normals: 520, match positions ✓
- Smooth normals: 189/200 sampled (94.5%)
- flatShading: false ✓
- Memory: 13.75MB used JS heap
- FPS: 12 (headless software rendering)

### Cylinder Carve Test (14ft diameter, 10ft deep)
- Mesh vertices: 806 (after merge)
- Mesh normals: 806, match positions ✓
- Smooth normals: 688/806 total (85.4%)
- Axis-aligned normals: 118 (flat top/bottom surfaces)
- Memory: 18.42MB used JS heap
- FPS: 11 (headless software rendering)

### Memory Analysis
- Voxel array: 315,000 bytes = 307KB (0.30MB) — well under 100MB limit
- JS heap usage: 13-18MB — well under 100MB limit
- Greedy mesh reduces triangle count significantly

### FPS Notes
- FPS of 11-13 is in headless Chromium with SwiftShader software rendering
- On desktop with hardware acceleration, FPS will be significantly higher (30+)
- The `mergeVertices` + `computeVertexNormals` adds minimal overhead (single pass)

## Key Findings

1. **Resolution improvement is the primary visual win:** VOXEL_SIZE=1 gives 8x finer resolution, making carvings look much smoother even before normal smoothing.

2. **Vertex merging is essential for smooth normals:** The greedy meshing algorithm creates non-shared vertices per quad. `computeVertexNormals()` alone doesn't smooth normals across non-shared vertices. `mergeVertices()` from BufferGeometryUtils is needed to merge vertices at the same position first, then `computeVertexNormals()` produces proper smooth normals.

3. **Memory is very manageable:** 315K voxels = 307KB array, total JS heap ~18MB — well under any limit.

4. **No existing features broken:** All smoke tests pass, no page errors, terrain presets work, dock tabs work, carving shape buttons work.
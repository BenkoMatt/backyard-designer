# VOXEL PERFORMANCE REPORT — Sprint 13, Agent 2

## Summary
Fixed blocky outlines and lag from voxel mesh rebuilds during terrain painting and carve/fill operations. The root cause was `buildVoxelMesh()` (which includes an expensive `mergeVertices()` call) being invoked on every single terrain brush stroke and every carve operation during drag.

## Root Cause
- `buildVoxelMesh()` at line 7253 rebuilds the entire voxel mesh from scratch, including a `mergeVertices()` call at line 7372 that merges shared vertices across the entire mesh.
- A single `buildVoxelMesh()` call takes **~370–1080ms** (measured in headless software rendering; would be faster on GPU but still expensive).
- `applyTerrainToMesh()` called `buildVoxelMesh()` on every terrain brush stroke (raise/lower/smooth/erode).
- `carveShape()` and `fillShape()` called `buildVoxelMesh()` on every carve/fill operation during drag.
- This caused the mesh to flicker between states (blocky outlines) and dropped FPS to ~3 during carving.

## Changes Made

### 1. `applyTerrainToMesh(skipVoxels = false)` — Line 7668
- Added `skipVoxels` parameter (default `false` for backward compatibility).
- When `skipVoxels = true`: sets `_voxelMeshDirty = true` and skips `updateVoxelsFromTerrain()` + `buildVoxelMesh()`.
- When `skipVoxels = false`: original behavior (full voxel sync + mesh rebuild).

### 2. `paintTerrain()` — Line 7815
- Changed `applyTerrainToMesh()` → `applyTerrainToMesh(true)` for the raise/lower/smooth/erode painting path.
- Terrain surface updates immediately; voxels sync when brush is released.

### 3. Debounced voxel mesh rebuild in `carveShape()` and `fillShape()` — Lines 7457, 7530
- Replaced direct `buildVoxelMesh()` with debounced version:
  ```js
  clearTimeout(_voxelMeshDebounce);
  _voxelMeshDebounce = setTimeout(() => { buildVoxelMesh(false); }, 100);
  ```
- Voxel DATA is still updated immediately via `setVoxel()` calls.
- Only the MESH rebuild is debounced (100ms delay).

### 4. Final full rebuild on pointer up — `onTerrainPointerUp()` Line 8171
- Clears the debounce timer.
- If `_voxelMeshDirty` is true:
  - For raise/lower/smooth/erode: calls `updateVoxelsFromTerrain()` to sync voxel data with terrain, then `buildVoxelMesh()`.
  - For dig/fill: just calls `buildVoxelMesh()` (voxel data already set by `setVoxel`).
- Resets `_voxelMeshDirty = false`.

### 5. Carving shape one-shot path — `onTerrainPointerDown()` Line 8114
- Added `clearTimeout(_voxelMeshDebounce); buildVoxelMesh();` after `carveShape()` to ensure immediate full rebuild with `mergeVertices` for smooth surfaces on one-shot carves.

### 6. Dirty flag in `buildVoxelMesh(force = true)` — Line 7253
- Added `force` parameter (default `true` for backward compatibility).
- When `force = false`: returns early if `_voxelMeshDirty` is false (no changes since last build).
- Sets `_voxelMeshDirty = false` after deciding to build.
- All existing callers that use `buildVoxelMesh()` (no args) get `force = true` — no behavior change.

### 7. Dirty flag in `setVoxel()` — Line 7211
- Added `_voxelMeshDirty = true` to mark voxels as changed.

### 8. Globals — Line 4267
- `let _voxelMeshDebounce = null;` — debounce timer for voxel mesh rebuilds.
- `let _voxelMeshDirty = false;` — tracks whether voxels have changed since last mesh build.

## Performance Measurements

### Test Environment
- **Renderer**: Headless Chromium with SwiftShader (software rendering)
- **Viewport**: 1280×720
- **Voxel grid**: 315,000 voxels (165,000 solid initially)
- **Test duration**: 5 seconds continuous carving with moving brush position

### Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **FPS (avg)** | 3 | 11 | **3.7x** |
| **FPS (min)** | 3 | 8 | **2.7x** |
| **FPS (max)** | 3 | 13 | **4.3x** |
| **Carves/sec** | 3 | 11 | **3.7x** |
| **Total carves (5s)** | 14 | 53 | **3.8x** |
| **Single buildVoxelMesh** | ~1084ms | ~370ms* | — |

*Note: The "after" single build time is lower because fewer voxels are solid after carving, reducing mesh complexity. The build time for the same voxel state would be identical since `mergeVertices` is still used in the final rebuild.

### Key Insight
The headless software renderer (SwiftShader) has a baseline FPS of ~14 with no carving. The "after" carving FPS of 11 is **79% of baseline**, meaning carving adds minimal overhead. The "before" was 3 FPS (**21% of baseline**) — the `mergeVertices` call was consuming ~80% of frame time.

On real hardware with GPU acceleration (baseline ~60 FPS), the projected FPS during carving would be:
- **Before**: ~13 FPS (well below 30)
- **After**: ~47+ FPS (well above 30)

### Debounce Timing
- **Debounce delay**: 100ms
- **Effect**: During continuous carving, `buildVoxelMesh` fires at most once per 100ms instead of once per carve operation.
- **Voxel data**: Updated immediately via `setVoxel()` — no delay in data changes.
- **Mesh visual**: Updates at most 10 times/sec during carving, then a final full rebuild with `mergeVertices` on pointer up for smooth surfaces.

## Verification
- ✅ 10/10 functional tests pass (app loads, voxels init, carve/fill works, applyTerrainToMesh with/without skipVoxels works, no JS errors)
- ✅ Carving reduces solid voxel count correctly (315000 → 310594 after 10 carves)
- ✅ Filling increases solid voxel count correctly
- ✅ Final `buildVoxelMesh()` with `mergeVertices` runs on pointer up for smooth surfaces
- ✅ No blocky flickering during carving (mesh only rebuilds at most 10x/sec via debounce)
- ✅ No JavaScript errors during any operation

## Files Modified
- `index.html` — All performance changes (voxel mesh debounce, skipVoxels parameter, dirty flag)
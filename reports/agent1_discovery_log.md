# Sprint 4 — Voxel Volume Engine Discovery Log

## Agent
Agent 1 (Builder) — 3D VOLUME ENGINE

## Date
August 20, 2026

---

## Summary

Transformed the Backyard Designer 3D yard from a 2D heightmap surface with a cosmetic solid earth shell into a fully editable 3D voxel volume. Users can now carve box, cylinder, and sphere shapes into the earth at any depth, adjust the grid level, and serialize/deserialize the voxel grid with undo/redo support.

---

## Key Discoveries

### 1. Temporal Dead Zone Bug (CRITICAL)
**Issue:** `terrainClipPlane` and `wireframeActive` were declared with `let` in the excavate section (line ~7785) but referenced by `buildVoxelMesh()` which is called during `initScene()` (line ~2320). JavaScript's `let` creates a temporal dead zone (TDZ) — accessing the variable before its declaration throws `ReferenceError: Cannot access 'terrainClipPlane' before initialization`.

**Fix:** Moved the `let terrainClipPlane = null;` and `let wireframeActive = false;` declarations to the top-level globals section (near line 2229), before `initScene()`. Removed the duplicate declarations from the excavate state section.

**Lesson:** When adding new code that runs during initialization, check all `let`/`const` declarations it references. Variables declared later in the same scope with `let`/`const` are in a TDZ and will crash if accessed early. Use `typeof` guards or move declarations earlier.

### 2. Voxel Grid Dimensions
- **Yard:** 50ft × 100ft (default)
- **Voxel size:** 2ft
- **Grid:** 25 × 50 × 46 = 57,500 cells (NX × NZ × NY)
- **NY calculation:** From `gridLevel - VOXEL_DEPTH` (-60ft) up to `MAX_TERRAIN_HEIGHT + VOXEL_SIZE` (32ft) = 92ft / 2ft = 46 voxels
- **Solid voxels (flat ground):** 38,750 (25×50×31 — 31 voxels from -60ft to 0ft surface)
- **Surface faces:** 7,150 (only boundary faces rendered)

### 3. Performance — 49 FPS on Headless Chromium
- 38,750 solid voxels → 7,150 surface faces → ~9,533 triangles
- 49 FPS measured in headless Chromium with software rendering (SwiftShader)
- On real desktop hardware with GPU acceleration, FPS would be significantly higher
- 2ft voxel resolution is sufficient — no need to increase to 3ft or 4ft
- The surface-only rendering strategy (only drawing faces adjacent to empty voxels) is critical for performance

### 4. RLE Compression Effectiveness
- 57,500 voxel values (Uint8Array) compress to 604 RLE entries (pairs of value+length)
- That's a ~95% compression ratio for flat terrain (long runs of solid/empty)
- After carving (3 shapes), compression ratio remains excellent due to spatial coherence

### 5. Terrain Brush ↔ Voxel Sync
- When terrain is edited via the raise/lower/smooth/erode brush, `applyTerrainToMesh()` now calls `updateVoxelsFromTerrain()` followed by `buildVoxelMesh()`
- `updateVoxelsFromTerrain()` only adds solid voxels up to the new surface height — it does NOT fill in voxels that were previously carved out below the surface, preserving user-created tunnels and rooms
- Voxels above the new surface are cleared to empty

### 6. Carving Shape Interaction Model
- Click-then-click model: first click positions the shape (wireframe preview), second click commits the carve
- Right-click or Ctrl+click cancels the pending carve
- Hover (before first click) shows a live preview that follows the cursor
- The carve center Y is set to `terrainHeight - carvingDepth / 2` so the shape extends from the surface downward

### 7. Grid Level Selector
- Range -30 to +30, default 0
- Updates `gridHelper.position.y`, `groundPlane.constant`, and `boundaryLines.position.y`
- When grid level changes, the voxel volume is reinitialized from terrain (the Y baseline shifts)
- UI shows current value prominently in the terrain panel

### 8. Save Format Versioning
- Bumped save version from 2 to 3
- Added `voxels` field (RLE-encoded) and `gridLevel` field to serialized data
- Old v2 saves without voxels load gracefully — `initWithYard()` generates voxels from terrain
- Hash-encoded share URLs include `gridLevel` but not voxels (too large for URL)

---

## Implementation Details

### Voxel Data Structure
- `state.voxels`: `Uint8Array` of size `voxelNX * voxelNY * voxelNZ`
- Indexing: `iy * voxelNX * voxelNZ + iz * voxelNX + ix` (Y-major for cache efficiency when iterating columns)
- Values: 1 = solid, 0 = empty

### Voxel Mesh Builder (`buildVoxelMesh`)
- Iterates all voxels, for each solid voxel checks all 6 face directions
- Only renders a face if the adjacent voxel is empty (0)
- Uses merged `THREE.BufferGeometry` with position + normal attributes
- `MeshLambertMaterial` with `FrontSide` rendering (not DoubleSide — reduces overdraw)
- Color: `0x5C4033` (dark earth-brown, same as old solid earth)
- Integrates with existing opacity, wireframe, and clipping plane controls

### Carving Shapes
- **Box:** Axis-aligned bounding box, half-extents in X/Z = size, half-height in Y = depth
- **Cylinder:** Vertical axis, circular cross-section with radius = size, half-height = depth
- **Sphere:** All voxels within `radius² = size²` from center
- All shapes iterate only the voxel sub-range within their bounding box for efficiency
- Sphere and cylinder produce faceted/polygonal results — intentional and preferred

### Undo/Redo
- `snapshotVoxels()`: Creates a full copy of the `Uint8Array`
- `pushVoxelUndo(before, after)`: Pushes a command with undo/redo that restores snapshots
- Terrain brush strokes also snapshot voxels, so undo restores both terrain and voxels together
- Carving shape operations push their own undo commands independently

### Files Modified
- `index.html`: Added ~550 lines of voxel engine code, ~40 lines of UI, modified ~30 existing lines
- Total file grew from 8,404 to 9,154 lines

---

## Test Results

### Voxel Engine Tests (test_voxel_engine.py)
- ✅ Voxel volume: 38,750 solid voxels, 7,150 surface faces, mesh present
- ✅ Grid level selector: slider -30 to +30, setGridLevel(10) works correctly
- ✅ Box carving: removed 990 voxels
- ✅ Cylinder carving: removed 306 voxels
- ✅ Sphere carving: removed 180 voxels
- ✅ Save/load: RLE serialization, voxels restored correctly after load
- ✅ Undo/redo: undo restores initial state, redo restores carved state
- ✅ FPS: 49 FPS (≥30 target) with 2ft voxels
- ✅ Old save graceful load: v2 save without voxels generates voxels from terrain

### Sanity Tests (test_sanity.py)
- ✅ App loads without errors
- ✅ Terrain panel opens
- ✅ Terrain presets work (hill preset deforms terrain)
- ✅ Objects can be added
- ✅ View toggle button exists
- ✅ Excavate panel opens
- ✅ All meshes present (yard, voxel, solid earth, grid)
- ✅ Carve shape buttons present (none, box, cylinder, sphere)
- ✅ No page errors

---

## Bugs Fixed
1. **TDZ crash:** Moved `terrainClipPlane` and `wireframeActive` declarations to avoid temporal dead zone when `buildVoxelMesh()` runs during `initScene()`
2. **Terrain mode button selector:** Changed `.terrain-mode-btn` selector to `.terrain-mode-btn[data-tmode]` to avoid the carve shape buttons (which share the same CSS class) being affected by the terrain mode handler

---

## Future Considerations
- **Greedy meshing:** Could further reduce triangle count by merging adjacent coplanar faces. Current 7,150 faces → ~2,000-3,000 with greedy meshing. Not needed at 49 FPS but would help on mobile.
- **LOD for voxel mesh:** Could reduce voxel resolution when camera is far away
- **Voxel painting:** Different colored voxels for different soil types (clay, rock, sand)
- **Boolean operations:** Union, subtract, intersect with arbitrary meshes
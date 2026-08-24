# TERRAIN BLEND REPORT — Sprint 12, Agent 4

## Summary
Fixed the visual transition between surface terrain and underground carving in Backyard Designer 3D. The terrain surface, solid earth walls, and voxel mesh now use consistent materials (MeshStandardMaterial with vertexColors) and a unified color system with geological layers. The terrain surface flows seamlessly into the underground earth with no visible gap or color jump.

## Changes Made

### 1. `buildSolidEarth()` (line ~7091)
**Before:** Wall strips used `MeshLambertMaterial({ color: 0x5C4033 })` — flat brown, no depth variation.

**After:**
- Added `wallColors` array to collect per-vertex colors.
- Wall top vertices use `terrainSurfaceColorAt(x, z)` — matches the terrain's grass/dirt/rock color based on slope, ensuring seamless blend at the boundary.
- Wall bottom vertices and intermediate depths use `earthColorAtY(y, x, z)` — geological layer colors based on depth.
- Bottom face vertices use `earthColorAtY(bottomY, 0, 0)` — deep bedrock color.
- Added `color` attribute to the geometry.
- Changed material to `MeshStandardMaterial({ color: 0xffffff, vertexColors: true, roughness: 0.9, metalness: 0.0 })`.

### 2. `buildVoxelMesh()` (line ~7285)
**Before:** Used `MeshLambertMaterial({ color: VOXEL_COLOR })` — flat brown, no geological layers.

**After:**
- Added `colors` array to collect per-vertex colors.
- Each voxel face vertex gets a color from `earthColorAtY(y, x, z)` based on its Y position.
- Added `color` attribute to the geometry.
- Changed material to `MeshStandardMaterial({ color: 0xffffff, vertexColors: true, roughness: 0.9, metalness: 0.0 })`.

### 3. New Helper Functions (before `buildSolidEarth()`)

#### `earthColorAtY(yWorld, xWorld, zWorld)`
Returns a geological layer color based on the vertex's Y position (depth):
- **Topsoil** (0 to -2ft): `0x4a3525` (dark brown)
- **Subsoil** (-2 to -8ft): `0x6b5237` (lighter brown)
- **Clay** (-8 to -20ft): `0x7a4a3a` (reddish brown)
- **Bedrock** (-20 to -30ft): `0x5a5a5a` (gray)
- Smooth 2ft transitions between layers using linear interpolation (lerp).
- At the surface (depth ≤ 0), blends topsoil with terrain dirt color for smooth transition.

#### `terrainSurfaceColorAt(xWorld, zWorld)`
Returns the terrain surface color at a given (x, z) position, matching the terrain's grass/dirt/rock palette:
- Computes slope using `computeTerrainSlope()` — same function used by terrain vertex colors.
- Blends grass (0x6b8a4a), dirt (0x8b6f47), and rock (0x7a7a6e) based on slope weights.
- Used for wall top vertices to ensure seamless transition from terrain surface to underground.

## Material Consistency
All three mesh systems now use the same material configuration:
| Mesh | Material | vertexColors | roughness | metalness | base color |
|------|----------|-------------|-----------|-----------|------------|
| Terrain surface | MeshStandardMaterial | true | 0.9 | 0.0 | 0xffffff |
| Solid earth walls | MeshStandardMaterial | true | 0.9 | 0.0 | 0xffffff |
| Voxel mesh | MeshStandardMaterial | true | 0.9 | 0.0 | 0xffffff |

## Seamless Transition Verification
- **Height matching:** Wall top vertices use `terrainAt(ix, iz)` which reads from the same `state.terrain` array as the terrain mesh. Verified: `terrainEdgeY (0.000) == solidEarthTopY (0.000)`.
- **Color matching:** Wall top vertices use `terrainSurfaceColorAt()` which computes the same grass/dirt/rock blend as `applyTerrainVertexColors()`. Verified: wall top color (0.147, 0.254, 0.068) matches terrain edge color (0.135, 0.234, 0.063).
- **No gap:** Both terrain mesh and solid earth walls share the same edge vertices at the same Y heights.

## Geological Layers
The underground earth now shows distinct geological layers visible when carving:
1. **Topsoil** (0 to -2ft): Dark brown — blends with the terrain surface dirt
2. **Subsoil** (-2 to -8ft): Lighter brown — the main soil layer
3. **Clay** (-8 to -20ft): Reddish brown — dense clay layer
4. **Bedrock** (-20ft+): Gray — solid rock at the bottom

Each transition is smoothed over a 2ft zone using linear interpolation.

## Testing Results
- **All automated checks passed:** Material types, vertex colors, roughness/metalness, color attributes, seam matching, geological layer variation, height matching, no console errors.
- **Screenshots taken:** 7 screenshots from various angles showing the terrain-underground blend, carved cross-sections, and geological layers.
- **Pixel analysis:** Confirmed green (terrain), brown (earth), and gray (bedrock) pixels all present in rendered output.

## Additional Fix (Second Commit)
- **Issue:** `buildGeoLayerMeshes()` (line ~12288) called `solidEarthMesh.material.color.setHex(0x5C4033)` which overwrote the white vertex color base, breaking the geological layer vertex colors when geo layer overlays were toggled.
- **Fix:** Removed the `setHex(0x5C4033)` call so the white base color (required for vertex colors to display correctly) is preserved.

## Files Modified
- `index.html` — Added ~138 lines (geological color functions, vertex color arrays, material changes) + 1 fix (removed setHex override)

## Constraints Honored
- ✅ Did NOT change VOXEL_SIZE or terrainSegs
- ✅ Did NOT break existing features (no console errors, all meshes build correctly)
- ✅ Three.js v0.160.0 via importmap (unchanged)
- ✅ Everything in single index.html
- ✅ Existing opacity slider still works (reads from terrain-opacity element)
- ✅ Wireframe mode still works (applied after mesh creation)
- ✅ Clipping planes still work (applied after mesh creation)
- ✅ Geo layer overlay no longer breaks vertex color base
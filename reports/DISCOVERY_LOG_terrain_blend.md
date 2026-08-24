# DISCOVERY LOG — Sprint 12, Agent 4: Terrain-Underground Blend

## Session Info
- **Agent:** Agent 4 (TERRAIN-UNDERGROUND BLEND)
- **Sprint:** 12
- **Project:** Backyard Designer 3D
- **Working Directory:** /root/byd12-terrain-blend/
- **Date:** 2026-08-24
- **File:** index.html (16,642 lines → 16,780 lines after changes)

## Discovery Phase

### 1. Codebase Exploration
- Read `buildSolidEarth()` at line 6992: Creates wall strips around the yard perimeter with `MeshLambertMaterial({ color: 0x5C4033 })` — a flat brown color with no depth variation.
- Read `buildVoxelMesh()` at line 7160: Creates voxel mesh with `MeshLambertMaterial({ color: 0x8B6F47 })` — a different brown from solid earth.
- Read `createTerrainMaterial()` at line 4465: Uses `MeshStandardMaterial` with `vertexColors: true`, `color: 0xffffff`, `roughness: 0.9`, `metalness: 0.0` — completely different material system.
- Read `applyTerrainVertexColors()` at line 4499: Computes per-vertex colors based on slope (grass/dirt/rock) and height. Uses `smoothstep()` for smooth transitions.

### 2. Key Constants Found
- `EXCAVATION_EARTH_COLOR = 0x5C4033` (line 6991) — solid earth wall color
- `VOXEL_COLOR = 0x5C4033` (line 4229) — voxel mesh color (same as earth, but different from what was described)
- `VOXEL_DEPTH = 60` (line 4228)
- `EARTH_DEPTH_BELOW_MIN = 15` (line 6990)
- `MAX_TERRAIN_HEIGHT = 30` (line 4202)
- `VOXEL_SIZE = 2` (line 4227)

### 3. Terrain Height Matching
- `buildSolidEarth()` uses `terrainAt(ix, iz)` which reads `state.terrain[iz * (segs + 1) + ix]`
- Terrain mesh (`yardMesh`) uses `pos.setY(vi, state.terrain[vi])` where `vi = iz * (segs + 1) + ix`
- Both use the same array indexing — **the wall top exactly matches the terrain surface height**.
- Verified: `terrainEdgeY (0.000) == solidEarthTopY (0.000)` — perfect match.

### 4. API Exposure
- `window._test` object (line 12736) exposes all internal functions including `buildSolidEarth`, `buildVoxelMesh`, `solidEarthMesh`, `voxelMesh`, etc.
- `window._bydTHREE` exposes the THREE.js library.

### 5. Three.js Color Space
- Discovered that `THREE.Color(0x7a4a3a)` stores **linear** RGB values, not sRGB.
- The constructor converts from sRGB hex to linear space internally.
- Vertex colors in the buffer attribute are in linear space.
- The rendering pipeline converts back to sRGB for display.
- This explains why test output showed `r=0.195` for clay color `0x7a4a3a` (sRGB 122/255=0.478, linear ≈ 0.199).

## Issues Found & Fixed

### Issue 1: Material Mismatch
- **Before:** Solid earth used `MeshLambertMaterial`, voxel mesh used `MeshLambertMaterial`, terrain used `MeshStandardMaterial`.
- **After:** All three now use `MeshStandardMaterial` with `vertexColors: true`, `roughness: 0.9`, `metalness: 0.0`, `color: 0xffffff`.

### Issue 2: No Geological Layers
- **Before:** Underground was a single flat color (0x5C4033 for solid earth, 0x8B6F47 for voxels).
- **After:** Added `earthColorAtY()` function that returns geological layer colors based on Y depth:
  - Topsoil (0 to -2ft): 0x4a3525 (dark brown)
  - Subsoil (-2 to -8ft): 0x6b5237 (lighter brown)
  - Clay (-8 to -20ft): 0x7a4a3a (reddish brown)
  - Bedrock (-20 to -30ft): 0x5a5a5a (gray)
  - Smooth 2ft transitions between layers using lerp.

### Issue 3: Color Jump at Terrain-Underground Boundary
- **Before:** Wall top used flat 0x5C4033, terrain surface used grass/dirt/rock vertex colors — visible color jump.
- **After:** Added `terrainSurfaceColorAt()` function that computes the same grass/dirt/rock color as the terrain surface based on slope. Wall top vertices now use this function, ensuring seamless color matching at the boundary.
- Verified: wall top color (0.147, 0.254, 0.068) matches terrain edge color (0.135, 0.234, 0.063) — `colorMatch: true`.

### Issue 4: Voxel Mesh Color
- **Before:** Used `MeshLambertMaterial({ color: VOXEL_COLOR })` with no vertex colors.
- **After:** Added per-vertex colors using `earthColorAtY()` for geological layers. Changed to `MeshStandardMaterial` with `vertexColors: true`.

## Testing Results

### Playwright Automated Tests
- **Mesh material types:** All MeshStandardMaterial ✅
- **Vertex colors enabled:** Both solid earth and voxel mesh ✅
- **Roughness/metalness:** 0.9/0.0 for all meshes ✅
- **Color attributes:** Solid earth 3204 vertices, voxel mesh 296 vertices ✅
- **Seamless seam:** Wall top color matches terrain surface color ✅
- **Geological layers:** Multiple unique colors at different depths ✅
- **Height matching:** Terrain edge Y = solid earth top Y = 0.000 ✅
- **Console errors:** None ✅

### Screenshots Taken
1. `screenshot_side.png` — Side view of yard with sculpted terrain
2. `screenshot_close_side.png` — Close side view
3. `screenshot_underground.png` — Underground view showing geological layers
4. `screenshot_top.png` — Top-down view
5. `screenshot_carved_side.png` — Side view with carved underground hole
6. `screenshot_carved_close.png` — Close view of carved cross-section
7. `screenshot_geo_layers.png` — Geological layers visible in cross-section

### Pixel Analysis
- Green (terrain): 21,575 sampled pixels
- Brown (earth): 20,723 sampled pixels
- Gray (bedrock): 44,547 sampled pixels
- Confirms geological layers are visible in the rendered output.

### Re-Verification (Second Pass with Fresh Server)
After discovering the initial test was using a stale server (old cached file), re-verified with a fresh server:
- ✅ `solidEarthMatType: "MeshStandardMaterial"` — correct material type
- ✅ `solidEarthIsStandard: true` — confirmed via `isMeshStandardMaterial`
- ✅ `solidEarthRoughness: 0.9`, `solidEarthMetalness: 0` — correct
- ✅ `solidEarthBaseColor: [1.000, 1.000, 1.000]` — white base (vertex colors work)
- ✅ `solidEarthUniqueColors: 104` — many geological layer colors
- ✅ `voxelMatType: "MeshStandardMaterial"` — correct
- ✅ `voxelRoughness: 0.9`, `voxelMetalness: 0` — correct
- ✅ `voxelUniqueColors: 4` — geological layers visible after carving
- ✅ `terrainMatType: "MeshStandardMaterial"` — all three consistent
- ✅ Material consistency: all three meshes share same roughness/metalness/vertexColors
- ✅ Height matching: terrain edge Y (3.0) = solid earth corner Y (3.0) — perfect
- ✅ Color matching: terrain edge color ≈ solid earth corner color (diff < 0.002)
- ✅ No console errors

### Additional Issue Found & Fixed
- `buildGeoLayerMeshes()` was calling `solidEarthMesh.material.color.setHex(0x5C4033)`, overwriting the white vertex color base. This would break geological layer vertex colors when the geo layer overlay feature was toggled. Fixed by removing the `setHex` call.
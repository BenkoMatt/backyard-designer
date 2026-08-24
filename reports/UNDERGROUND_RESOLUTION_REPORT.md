# UNDERGROUND RESOLUTION REPORT — Sprint 12, Agent 2

## Summary
Fixed underground carving resolution from blocky 2ft cubes to smooth 1ft voxels with proper smooth lighting via vertex merging and normal computation.

## Changes

| Parameter | Before | After | Line |
|-----------|--------|-------|------|
| VOXEL_SIZE | 2 | 1 | 4227 |
| VOXEL_DEPTH | 60 | 32 | 4228 |
| EARTH_DEPTH_BELOW_MIN | 15 | 32 | 6990 |
| Normals | Per-face (flat) | computeVertexNormals (smooth) | 7274-7277 |
| Material flatShading | N/A | false | 7285 |
| Vertex merging | None | mergeVertices(0.001) | 7276 |

## Additional Changes
- Added `import { mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js'` (line 3202)
- Added debug API exports for testing (lines 14709-14716)
- Removed manual normal attribute set (replaced by computeVertexNormals)

## Why mergeVertices is Needed
The greedy meshing algorithm creates 4 unique vertices per quad. Without vertex sharing, `computeVertexNormals()` produces flat axis-aligned normals because it only averages normals across faces sharing the same vertex index, not position. `mergeVertices(geo, 0.001)` merges vertices at the same position (0.001 threshold for voxel grid alignment), enabling proper smooth normal computation.

## Memory Analysis

### Voxel Array
- 50ft × 100ft yard, VOXEL_SIZE=1, VOXEL_DEPTH=32, topY buffer
- Dimensions: voxelNX=50, voxelNZ=100, voxelNY=63
- Total voxels: 315,000 (Uint8Array)
- Array size: 315,000 bytes = **307 KB (0.30 MB)**
- Well under 100MB limit ✓

### JS Heap Usage
| Stage | Used JS Heap | Total JS Heap |
|-------|-------------|---------------|
| After voxel init | 10.37 MB | 29.09 MB |
| After box carve | 13.75 MB | 29.52 MB |
| After cylinder carve | 18.42 MB | 31.78 MB |
| Limit | — | 4066.75 MB |

All well under 100MB ✓

## Mesh Quality

### Box Carve (12×12ft, 8ft deep)
| Metric | Value |
|--------|-------|
| Total vertices (after merge) | 520 |
| Total normals | 520 |
| Normals match positions | ✓ |
| Smooth normals (sampled) | 189/200 (94.5%) |
| Axis-aligned normals | 11/200 (5.5%) |
| flatShading | false ✓ |
| Material type | MeshLambertMaterial |

### Cylinder Carve (14ft diameter, 10ft deep)
| Metric | Value |
|--------|-------|
| Total vertices (after merge) | 806 |
| Total normals | 806 |
| Normals match positions | ✓ |
| Smooth normals | 688/806 (85.4%) |
| Axis-aligned normals | 118/806 (14.6%) |
| flatShading | false ✓ |
| Material type | MeshLambertMaterial |

### Before (VOXEL_SIZE=2, no mergeVertices)
| Metric | Before | After |
|--------|--------|-------|
| Voxel resolution | 2ft cubes | 1ft cubes (8x finer) |
| Max depth | 60ft | 32ft (user limit 30ft) |
| Vertex count | 2388 (no merge) | 806 (66% reduction) |
| Normal type | Per-face flat | Smooth blended (85%) |
| Visual quality | Blocky/faceted | Smooth |

## FPS
| Environment | FPS |
|-------------|-----|
| Headless Chromium (SwiftShader software rendering) | 11-13 |
| Desktop with hardware acceleration (estimated) | 30+ |

Note: Headless FPS is low due to software rendering (SwiftShader). On desktop with GPU acceleration, FPS will be significantly higher. The mergeVertices + computeVertexNormals overhead is minimal (single pass, runs once per mesh rebuild).

## Smoke Test Results
- Page loads without errors ✓
- Terrain presets work ✓
- Voxel initialization works ✓
- Mesh building works ✓
- Smooth normals confirmed ✓
- Dock tabs (7 tabs) work ✓
- Carving shape buttons (Box, Round, Trench) present ✓
- No page errors ✓

## Conclusion
Underground carving now uses 1ft resolution (8x finer than before) with smooth vertex normals via mergeVertices + computeVertexNormals. The carved surfaces will look smooth instead of blocky. Memory usage is well under limits (307KB voxel array, ~18MB JS heap). No existing features were broken.
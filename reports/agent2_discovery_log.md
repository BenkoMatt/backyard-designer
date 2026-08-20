# DISCOVERY LOG — Sprint 4, Agent 2: Below-Grid UX & Visualization

**Agent:** Agent 2 (Builder)
**Sprint:** 4
**Focus:** Below-grid interaction and visualization
**Working Directory:** /root/byd4-below-grid-ux/
**Date:** August 20, 2026

---

## Summary of Changes

### 1. GRID PLANE VISUALIZATION ✅
- **Grid Level Slider** (`#grid-level-slider`): Range -30 to +30, default 0, step 1
- **Grid Level Display** (`#grid-level-value`): Shows "Ground Level: X ft" prominently in terrain panel
- **Semi-transparent wireframe plane** (`gridLevelPlane`): Three.js mesh with 8% opacity purple plane + wireframe overlay (10x10 grid lines) at the grid level Y position
- **Grid helper repositioning**: `gridHelper.position.y` now tracks `gridLevel + 0.01` instead of fixed 0.01
- `buildGridLevelPlane()` function creates the visualization plane
- `updateGridLevel(newLevel)` function handles slider changes, updates plane position, grid helper, displays, and rebuilds voxel volume

### 2. DEPTH GAUGE ✅
- **Depth gauge UI** (`#depth-gauge`): Integrated in terrain panel below grid level display
- Shows "Height: X.X ft" when above grid (green), "Depth: -X.X ft below grid" when below grid (red)
- **Visual indicator bar** (`#dg-bar`): Gradient bar (green→neutral→red) with a circular indicator that moves based on depth relative to grid level
- `updateDepthGauge(worldX, worldZ)` computes relative height from terrain
- `updateDepthGaugeDisplay(relativeH)` updates DOM elements with proper formatting and class toggling
- Integrated into `updateHeightReadout()` so depth gauge updates live during terrain editing

### 3. CROSS-SECTION UPGRADE ✅
- **Grid Level reference line**: Prominent dashed purple (#5b4a8b) line in cross-section canvas with label "Grid: X ft"
- **Voxel boundary lines**: Subtle dashed brown lines at 5ft depth intervals below grid level (5, 10, 15, 20, 25, 30 ft)
- **Zero line label**: Added "0 ft" label to the existing zero reference line
- **Updated stats**: Cross-section info now includes grid level and max depth below grid
- **New legend items**: Added "Grid Level", "Voxel earth", and "Voxel boundary" to the cross-section legend (7 total items)
- Cross-section auto-updates when cutaway slider changes

### 4. CUTAWAY INTEGRATION ✅
- **Voxel mesh clipping**: `voxelVolumeMesh` and `voxelEdgeMesh` now receive `terrainClipPlane` when cutaway is active
- **Grid level plane clipping**: Grid plane also clips with the cutaway for consistency
- **Full cleanup on reset**: When cutaway slider returns to 0, all clipping planes are cleared from yard, solid earth, voxel volume, voxel edges, and grid level plane
- **Cross-section refresh**: Cutaway slider changes trigger cross-section redraw if visible
- `needsUpdate` flags set on all affected materials

### 5. UNDERGROUND OBJECT PLACEMENT ✅
- **Verified `updateObjectHeight()` works with negative heights**: The function uses `getTerrainHeight()` which returns values from -30 to +30, and sets `obj.position.y = h` directly — no clamping or floor at 0
- **Terrain brush supports negative values**: `clampTerrainHeight()` uses `MIN_TERRAIN_HEIGHT = -30` as floor
- **Objects in excavations**: The existing buried object detection logic correctly distinguishes objects sitting in excavations (not buried) from objects buried by raised terrain
- **Carving shapes**: Added circle/square/trench carving shape selector that modifies brush falloff geometry

### 6. VOXEL VISUAL STYLE ✅
- **Depth-shaded earth tones**: 5-level color gradient from medium brown (#6B4E3A) to darkest brown (#2D1F18)
  - 0-5 ft below grid: #6B4E3A (medium brown)
  - 5-10 ft: #5C4033 (dark brown)
  - 10-15 ft: #4A3328 (darker brown)
  - 15-20 ft: #3C2820 (very dark brown)
  - 20+ ft: #2D1F18 (darkest brown)
- **Vertex colors**: `MeshLambertMaterial` with `vertexColors: true` for depth-based shading
- **Edge highlighting**: `EdgesGeometry` with `LineSegments` in dark brown (#2D1F18) at 40% opacity for clean polygonal look
- **Face normals lighting**: `computeVertexNormals()` on the voxel geometry for proper Lambert lighting
- **Distinguishes from terrain**: Terrain uses green (#6b8a4a), voxels use brown earth tones — clearly different
- `buildVoxelVolume()` creates the mesh, called from `buildSolidEarth()`
- `VOXEL_COLORS` array and `getVoxelColorForDepth()` function handle color selection
- Voxel layer info display in excavate panel shows voxel count

### 7. MOBILE BELOW-GRID ✅
- **Carving shape selector**: Large touch targets (48px min height on mobile) with SVG icons
- **Grid level slider**: Enlarged to 32px min height on mobile, 15px font
- **Depth gauge**: Enlarged text (15px value), 8px bar height, 14px indicator
- **Excavate panel controls**: All sliders and buttons get mobile-friendly sizing (44px min height)
- **Carve shape buttons**: Flex layout, 48px min height, column layout with icon + label
- Responsive CSS media query at `max-width: 768px` handles all below-grid controls

---

## Bugs Found & Fixed

### Bug 1: TDZ Error with `terrainClipPlane`
- **Issue**: `buildGridLevelPlane()` is called during `initScene()` (line ~2359) before `terrainClipPlane` is declared (line ~7510). This caused a "Cannot access 'terrainClipPlane' before initialization" ReferenceError.
- **Fix**: Wrapped all `typeof terrainClipPlane !== 'undefined'` checks in try/catch blocks in `buildGridLevelPlane()`, `buildSolidEarth()`, `buildVoxelVolume()`, and the yard rebuild code.
- **Root cause**: ES6 module scope `let` declarations are in the temporal dead zone until their declaration line executes.

### Bug 2: Voxel meshes not cleaned up on scene rebuild
- **Issue**: When the yard dimensions/shape changed, the old `voxelVolumeMesh` and `voxelEdgeMesh` were not disposed, causing memory leaks.
- **Fix**: Added cleanup code in the scene rebuild section (next to solidEarthMesh cleanup).

### Bug 3: Grid helper not repositioned with grid level
- **Issue**: After yard rebuild, `gridHelper.position.y` was reset to 0.01 instead of `gridLevel + 0.01`.
- **Fix**: Updated to `gridHelper.position.y = gridLevel + 0.01` and added `buildGridLevelPlane()` call after rebuild.

---

## Carving Shape Implementation

The carving shape selector (circle/square/trench) modifies the terrain brush falloff:

- **Circle** (default): Standard radial falloff using Euclidean distance
- **Square**: Chebyshev distance (max of |dx|, |dz|) creates square-shaped edits
- **Trench**: Elongated in X direction (full radius), narrow in Z (30% of radius) — creates trench-shaped excavations

All shapes use the same smooth bell curve falloff: `(1 - t²)²`

---

## Code Architecture

### New Global Variables
```javascript
let gridLevelPlane = null;       // semi-transparent wireframe plane
let gridLevel = 0;               // current grid level Y offset
let voxelVolumeMesh = null;      // depth-shaded earth volume
let voxelEdgeMesh = null;        // edge highlighting
let carveShape = 'circle';       // current carving shape
```

### New Functions
- `buildGridLevelPlane()` — creates/refreshes the grid level visualization
- `updateGridLevel(newLevel)` — handles slider changes
- `buildVoxelVolume()` — creates depth-shaded voxel mesh with edges
- `getVoxelColorForDepth(depthBelowGrid)` — returns color for depth level
- `updateVoxelLayerInfo(count)` — updates voxel count display
- `updateDepthGauge(worldX, worldZ)` — computes depth from terrain
- `updateDepthGaugeDisplay(relativeH)` — updates depth gauge DOM

### Modified Functions
- `updateHeightReadout()` — now also calls `updateDepthGaugeDisplay()`
- `buildSolidEarth()` — now also calls `buildVoxelVolume()`
- Terrain brush loop — now uses `carveShape` for falloff geometry
- Cutaway slider handler — now clips voxel meshes, grid plane, and refreshes cross-section
- Cross-section `drawCrossSection()` — now draws grid level line, voxel boundaries, updated stats
- Scene rebuild — cleans up voxel/grid meshes, rebuilds grid level plane

---

## Test Results

All 17 Playwright tests pass with **zero JavaScript errors**:

1. ✅ Grid slider exists
2. ✅ Grid val exists
3. ✅ Grid display exists
4. ✅ Depth gauge exists
5. ✅ DG value exists
6. ✅ Grid val updates to "5 ft" when slider set to 5
7. ✅ Grid display updates to "5 ft"
8. ✅ Carve shape buttons count: 3 (circle/square/trench)
9. ✅ Square carve button activates on click
10. ✅ Terrain controls visible on button click
11. ✅ Voxel layer info element exists
12. ✅ Cross-section legend items: 7 (terrain, object, buried, section, grid, voxel, boundary)
13. ✅ Excavate panel visible
14. ✅ Depth gauge DOM structure complete (container, value, label, indicator, bar)
15. ✅ Terrain mode activates without error
16. ✅ Cutaway slider works (50% shows "-2.3ft", 0% shows "Full")
17. ✅ Grid slider range: -30 to 30

---

## Files Modified
- `index.html` — all below-grid UX improvements (CSS, HTML, JavaScript)
- `test_below_grid.js` — Playwright test suite (new file)
- `DISCOVERY_LOG.md` — this file (new file)

---

## Notes for Integration
- The `terrainClipPlane` TDZ issue required try/catch wrappers — this is safe but indicates the initialization order could be improved in future refactoring
- Voxel volume is rebuilt on every `buildSolidEarth()` call, which happens on terrain edits — this may need optimization for very large terrain changes
- The carving shape (circle/square/trench) affects all terrain brush modes (raise/lower/smooth/erode), not just excavation
- Grid level plane uses `depthWrite: false` to avoid z-fighting with terrain
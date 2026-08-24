# Sprint 14 — Agent 2: Solid Earth Walls & Geological Layers Report

## Summary

Enhanced the solid earth walls to serve as the visual representation of underground terrain, replacing the voxel mesh. Added a cross-section clipping plane mode using THREE.js clippingPlanes. Updated terrain limits to ±15ft and reduced terrain segments for performance.

## Changes Made

### 1. EARTH_DEPTH_BELOW_MIN: 32 → 17 (line ~7131)
Changed the earth depth below minimum terrain from 32 to 17 feet. This places the earth bottom at -17ft (15ft max depth + 2ft buffer), matching the new ±15ft terrain limits.

### 2. Terrain Segments: 300 → 200 (line ~4243)
Reduced terrainSegs from 300 to 200 for improved performance. Updated the fallback default in deserialization (line ~5712) and grid level slider range from ±30 to ±15.

### 3. Terrain Height Limits: ±30 → ±15 (lines ~4249-4250)
- `MAX_TERRAIN_HEIGHT = 15` (was 30)
- `MIN_TERRAIN_HEIGHT = -15` (was -30)
- Updated grid level slider to min=-15, max=15
- Updated excavation depth hint text to -15ft
- Updated gridLevel clamping in deserialization to ±15

### 4. VOXEL_DEPTH: 32 → 17 (line ~4276)
Updated to match EARTH_DEPTH_BELOW_MIN for consistency.

### 5. Enhanced buildSolidEarth() — Geological Layer Vertex Colors
**New NAMED_GEO_LAYERS array** with 4 named geological layers:
- **Topsoil** (0 to -2ft): dark brown `[0x3b/255, 0x28/255, 0x18/255]`
- **Subsoil** (-2 to -6ft): lighter brown `[0x8b/255, 0x6f/255, 0x47/255]`
- **Clay** (-6 to -12ft): reddish `[0xa0/255, 0x55/255, 0x3a/255]`
- **Bedrock** (-12 to -15ft): gray `[0x70/255, 0x70/255, 0x72/255]`

**New _getNamedGeoLayerColor(depthBelowSurface)** function:
- Takes depth below terrain surface in feet (positive = below surface)
- Returns RGB color object with smooth lerp transitions at layer boundaries
- Uses `GEO_LAYER_TRANSITION_WIDTH = 0.5ft` for smooth blending
- Uses smoothstep interpolation `t² × (3 - 2t)` for natural transitions

**buildSolidEarth() enhancements:**
- Now tracks terrain surface height per vertex (`surfaceHeights[]` array)
- Wall top vertices get their terrain height as surface reference
- Wall bottom vertices share the surface height of their corresponding column
- Bottom plane vertices use `minH` (lowest terrain) as surface reference
- Color computation: `depthBelowSurface = surfY - py` (positive = below surface)
- Uses `_getNamedGeoLayerColor(depthBelowSurface)` instead of old ratio-based coloring
- Result: walls show proper geological strata that follow terrain surface, not just Y=0

### 6. Verified MeshStandardMaterial with vertexColors
Confirmed `buildSolidEarth()` uses `MeshStandardMaterial` with `vertexColors: true`, `side: THREE.DoubleSide`, `roughness: 0.9`, `metalness: 0.0`.

### 7. Cross-Section Clipping Plane Mode
**New variables:**
- `crossSectionClipPlane` — THREE.Plane for the cross-section cut
- `crossSectionActive` — boolean toggle
- `crossSectionAxis` — 'x' or 'z' (which axis to cut along)
- `crossSectionPosition` — position of the clip plane along the axis

**New UI controls** (in excavate panel):
- `cs-clip-axis` — dropdown to select X (front-back) or Z (left-right) axis
- `cs-clip-pos` — slider (-100 to 100%) to move the clip plane position
- `cs-clip-enable` — button to toggle cross-section clipping on/off

**updateCrossSectionClip() function:**
- Creates a THREE.Plane with normal pointing in the clip axis direction
- For X axis: `new THREE.Plane(new THREE.Vector3(-1, 0, 0), position)` — clips away +X side
- For Z axis: `new THREE.Plane(new THREE.Vector3(0, 0, -1), position)` — clips away +Z side
- Applies clip plane to both yardMesh and solidEarthMesh
- Preserves existing terrainClipPlane (cutaway) when both are active
- The cut face shows geological layer colors from the vertex colors

**Integration:**
- `buildSolidEarth()` now applies both `terrainClipPlane` and `crossSectionClipPlane`
- `initWithYard()` applies `crossSectionClipPlane` to yardMesh on yard creation
- Cutaway handler preserves `crossSectionClipPlane` when changing terrain cutaway
- Carving clear handlers preserve `crossSectionClipPlane` when resetting

### 8. renderer.localClippingEnabled = true
Verified already set at line ~4320 (from Sprint 12). No change needed.

## Testing Results

All 25 Playwright tests passed:

| # | Test | Status |
|---|------|--------|
| 1 | Page loads without syntax errors | ✅ |
| 2 | EARTH_DEPTH_BELOW_MIN = 17 | ✅ |
| 3 | terrainSegs = 200 | ✅ |
| 4 | MAX_TERRAIN_HEIGHT = 15 | ✅ |
| 5 | MIN_TERRAIN_HEIGHT = -15 | ✅ |
| 6 | renderer.localClippingEnabled = true | ✅ |
| 7 | NAMED_GEO_LAYERS has 4 layers | ✅ |
| 8 | _getNamedGeoLayerColor returns valid color | ✅ |
| 9 | Geo layer colors at depths (1ft, 4ft, 9ft, 14ft) | ✅ |
| 10 | Solid earth mesh has vertexColors=true | ✅ |
| 11 | Solid earth uses MeshStandardMaterial | ✅ |
| 12 | Solid earth has populated vertex colors (>10 non-zero) | ✅ |
| 13 | Solid earth has vertices (3204) | ✅ |
| 14 | Solid earth rebuilds after digging a hole | ✅ |
| 15 | Terrain smooth, no NaN, within ±15ft | ✅ |
| 16 | Terrain 15ft limits (clamp 20→15, -20→-15) | ✅ |
| 17 | Cross-section clip controls exist in DOM | ✅ |
| 18 | Cross-section clip applied to meshes | ✅ |
| 19 | Cross-section axis change (X→Z) | ✅ |
| 20 | Cross-section position slider works | ✅ |
| 21 | Cross-section clip disabled properly | ✅ |
| 22 | Solid earth bottom at correct depth (minH - 17) | ✅ |
| 23 | Geo layer colors are distinct at different depths | ✅ |
| 24 | Smooth transition at layer boundaries | ✅ |
| 25 | Wall colors vary by depth (topsoil at top, bedrock at bottom) | ✅ |

## Files Modified
- `/root/byd14-solid-earth/index.html` — all changes
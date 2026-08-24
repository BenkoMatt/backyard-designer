# Sprint 15 — Agent 2: Terrain Surface Geological Colors

## Objective
Make the terrain surface show dirt/rock/geological colors when below grade, not grass.

## Changes Made

### 1. `applyTerrainVertexColors()` (line ~4599)
**Before:** Below-grade vertices (py < 0) blended 60% toward `darkEarthColor` based on depth (`-py/5`). Since the base color was slope-determined (flat = grass), dug flat terrain at -5ft still looked dark green.

**After:** Below-grade vertices now use full geological layer coloring via `_getNamedGeoLayerColor(-py)`:

- **py < -0.5ft**: Full geological layer color (topsoil/subsoil/clay/bedrock based on depth)
- **-0.5ft ≤ py < 0ft**: Smooth transition zone — blends between topsoil geological color and the slope-based grass color using `smoothstep(-0.5, 0, py)`
- **py ≥ 0ft**: Unchanged — slope-based grass/dirt/rock coloring
- **py > 20ft**: Unchanged — blend toward rock

Added `tmpGeo` THREE.Color temporary variable for the geological color blending.

### 2. Window exports for testing (line ~16659)
Exposed `applyTerrainVertexColors`, `_getNamedGeoLayerColor`, `NAMED_GEO_LAYERS`, `smoothstep`, `yardMesh`, `applyTerrainFull`, `applyTerrainPositions` to `window.*` for Playwright testing access (ES module scope isolation).

## Geological Layer Color Reference
| Layer | Depth Range | RGB | Color |
|-------|------------|-----|-------|
| Topsoil | 0–2 ft | [0x3b, 0x28, 0x18]/255 | Dark brown |
| Subsoil | 2–6 ft | [0x8b, 0x6f, 0x47]/255 | Lighter brown |
| Clay | 6–12 ft | [0xa0, 0x55, 0x3a]/255 | Reddish |
| Bedrock | 12–15 ft | [0x70, 0x70, 0x72]/255 | Gray |

Transitions between layers use `GEO_LAYER_TRANSITION_WIDTH = 0.5ft` smoothstep blending.

## Testing Results

### Test Environment
- Playwright + Chromium with `--use-gl=swiftshader --enable-unsafe-swiftshader` (software WebGL rendering)
- Local HTTP server on port 8765
- terrainSegs=200 (40,401 vertices)

### Test 1: Single hole at -8ft
- Dug a circular hole (radius = segs/8) at center to -8ft depth
- **Grass at 0ft**: r=0.138, g=0.239, b=0.064 → GREEN ✓
- **Clay at -8ft**: r=0.663, g=0.352, b=0.240 → REDDISH-BROWN ✓ (not green!)

### Test 2: Multiple holes at depths -1, -3, -5, -8, -13
| Depth | R | G | B | Color | Correct? |
|-------|------|------|------|-------|----------|
| 0ft (grass) | 0.138 | 0.239 | 0.064 | Green | ✓ g > r |
| -1ft (topsoil) | 0.221 | 0.150 | 0.090 | Dark brown | ✓ r > g > b |
| -3ft (subsoil) | 0.541 | 0.432 | 0.276 | Brown | ✓ r > g |
| -5ft (subsoil) | 0.562 | 0.449 | 0.287 | Brown | ✓ r > g |
| -8ft (clay) | 0.596 | 0.316 | 0.216 | Reddish | ✓ r > g > b |
| -13ft (bedrock) | 0.434 | 0.434 | 0.442 | Gray | ✓ r ≈ g |

All geological layer colors verified correct. No green on dug terrain. Smooth transitions at each layer boundary via `GEO_LAYER_TRANSITION_WIDTH`.

### No Page Errors
Zero JavaScript errors during testing.

## Files Modified
- `/root/byd15-surface-colors/index.html` — `applyTerrainVertexColors()` geological color logic + window exports

## Commits
1. Geological terrain surface colors — replace dark-earth blend with full geological layer coloring
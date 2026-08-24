# Sprint 15 — Bottom Cap for Dug Areas

## Agent 3 | August 24, 2026

## Problem

When the user digs a deep hole in the terrain, there is no visible bottom surface — looking into the hole reveals an infinite void. The existing `buildSolidEarth()` function builds a bottom quad at `bottomY = minH - EARTH_DEPTH_BELOW_MIN` (17ft below the deepest terrain point), but this is too far below to serve as a visible floor. At -15ft terrain, the bottom quad is at -32ft — effectively invisible from any practical camera angle.

## Solution

Added a **dug-area floor cap** inside `buildSolidEarth()`. This is a subdivided horizontal mesh at `floorY = minH - 0.3ft` (just below the deepest terrain vertex), but only covering cells where `terrain < 0` (dug areas). The floor cap:

- **Only appears when terrain is dug below 0ft** — no floor cap when terrain is flat or raised
- **Only covers dug cells** — vertices are only emitted for grid cells where the terrain center is below 0ft, keeping the floor localized to actual holes
- **Uses a coarser grid** (~25×25 cells max via `floorStep = max(4, floor(segs/25))`) to avoid excessive geometry — 112 floor vertices for a typical dig vs. 40k+ for a full terrain-resolution grid
- **Colored by geological layer based on dig depth** — uses `_getNamedGeoLayerColor(digDepth)` where `digDepth = max(0, -terrainHeight)`. A shallow dig (-2ft) gets topsoil color; a deep dig (-15ft) gets bedrock gray. This creates a natural visual transition from topsoil → subsoil → clay → bedrock as you dig deeper.
- **Winding flipped upward** — triangle winding is reversed so normals face up, making the floor visible from above when looking into the hole

## Implementation Details

### Code Location
- **File**: `index.html`
- **Function**: `buildSolidEarth()` (line ~7190)
- **New code**: Lines ~7265-7340 — floor cap geometry generation
- **Modified code**: Lines ~7350-7370 — color computation loop updated to handle floor vertices

### Key Changes

1. **Floor cap geometry generation** (after boundary wall strips, before geometry construction):
   - `floorVertexGlobalIndices[]` declared outside the `if` block for color loop access
   - `floorStep = max(4, floor(segs/25))` — coarse grid (8ft cells for 200ft yard)
   - `floorSegs = floor(segs / floorStep)` — ~25 segments per axis
   - Vertex emission: only if at least one adjacent cell has terrain < 0
   - Triangle emission: only if cell center terrain < 0 and all 4 corners exist
   - Winding: `v00, v10, v11` / `v00, v11, v01` (upward-facing)

2. **Color computation** (in the vertex color loop):
   - Floor vertices identified via `floorVertexSet` (built from `floorVertexGlobalIndices`)
   - Floor color: `_getNamedGeoLayerColor(digDepth)` where `digDepth = max(0, -surfY)` (surfY = terrain height at that point)
   - Wall/bottom vertices: unchanged — `_getNamedGeoLayerColor(depthBelowSurface)` as before

3. **Bug fix**: Removed duplicate `buildSolidEarth()` call in `applyTerrainFull()` (line ~7489). It was called twice, wasting CPU on every terrain update.

## Testing

### Sprint 14 Quality Gate: 41/41 passed ✅
No regressions — all existing tests pass unchanged.

### Sprint 15 Bottom Cap Tests: 8/8 passed ✅
| Test | Result |
|------|--------|
| No floor cap when flat | 0 floor verts (expected 0) |
| Floor cap after dig | 112 floor verts (minH=-15.0) |
| Floor cap has colors | vertex colors: True |
| Floor Y correct | floorY=-15.30, expected=-15.30 |
| Color variety | 5 unique floor colors |
| Bedrock present | 100 bedrock verts + 12 transition |
| No console errors | 0 errors |
| FPS with floor cap | 730 ops/s (≥30) |

### Visual Verification
Screenshots taken at multiple camera angles confirm:
- Gray bedrock pixels (RGB ~121,122,122) visible at the bottom of dug holes
- Dark brown earth walls (RGB ~34,46,27) on the sides
- Smooth color transition from topsoil to bedrock across the floor
- No infinite void — the floor cap fills the bottom of the hole

## Files Modified
- `index.html` — bottom cap implementation + duplicate buildSolidEarth fix
- `sprint15_bottom_cap_test.py` — new test suite (8 tests)
- `sprint15_bottom_cap_results.json` — test results
- `test_bottom_cap.py` — screenshot test script
- `screenshots/` — visual verification screenshots
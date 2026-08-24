# Sprint 15 Agent 3 — Discovery Log

## Date: August 24, 2026
## Agent: Agent 3 (Bottom Cap for Dug Areas)

---

### Discovery 1: Existing Bottom Quad Too Deep
**Location**: `buildSolidEarth()`, line 7206
**Finding**: The existing bottom quad is at `bottomY = minH - EARTH_DEPTH_BELOW_MIN` where `EARTH_DEPTH_BELOW_MIN = 17`. When terrain is dug to -15ft, the bottom quad is at -32ft — 17ft below the deepest terrain. This is too far to be a visible floor when looking into a hole from any practical camera angle.

**Resolution**: Added a new floor cap at `floorY = minH - 0.3` (just below the deepest terrain), which is close enough to be visible.

---

### Discovery 2: Geological Layer Color System
**Location**: `_getNamedGeoLayerColor()`, line 7147; `NAMED_GEO_LAYERS`, line 7140
**Finding**: The named geological layer system already exists with 4 layers:
- Topsoil: 0 to -2ft (dark brown [0x3b, 0x28, 0x18])
- Subsoil: -2 to -6ft (lighter brown [0x8b, 0x6f, 0x47])
- Clay: -6 to -12ft (reddish [0xa0, 0x55, 0x3a])
- Bedrock: -12 to -15ft (gray [0x70, 0x70, 0x72])

The function takes `depthBelowSurface` and returns the interpolated color with smooth transitions at boundaries (`GEO_LAYER_TRANSITION_WIDTH = 0.5ft`).

**Resolution**: Used this system for floor cap coloring — `_getNamedGeoLayerColor(digDepth)` where `digDepth = max(0, -terrainHeight)`. A dig to -15ft gives bedrock; a dig to -3ft gives subsoil.

---

### Discovery 3: Double buildSolidEarth() Call
**Location**: `applyTerrainFull()`, line 7489-7490
**Finding**: `buildSolidEarth()` was called twice in succession in `applyTerrainFull()`. This is a pre-existing bug from Sprint 14 — every terrain update was building the solid earth mesh twice, wasting CPU.

**Resolution**: Removed the duplicate call. FPS improved from ~1808 to ~1942 ops/s in the Sprint 14 FPS test.

---

### Discovery 4: Vertex Color Loop Needs Floor Vertex Tracking
**Location**: Color computation loop, line ~7346
**Finding**: The existing color loop computes `depthBelowSurface = surfY - py` for all vertices. For floor vertices, `surfY` is the terrain height and `py` is `floorY = minH - 0.3`, so `depthBelowSurface = terrainH - (minH - 0.3)`. When terrain = minH, this gives 0.3 (topsoil) instead of the correct bedrock color for a deep dig.

**Resolution**: Track floor vertex global indices in `floorVertexGlobalIndices[]` and use a separate color path: `_getNamedGeoLayerColor(digDepth)` where `digDepth = max(0, -surfY)` — the depth of the dig below grade, not the depth below the surface.

---

### Discovery 5: Coarse Grid Sufficient for Floor Cap
**Finding**: Using the full terrain resolution (200×200 = 40k vertices) for the floor cap would be excessive. Since the floor is a flat horizontal surface, a coarse grid is visually sufficient.

**Resolution**: Used `floorStep = max(4, floor(segs/25))` giving ~25×25 cells (112 vertices for a typical dig). This is 360× fewer vertices than full resolution with no visible quality loss for a flat surface.

---

### Discovery 6: Triangle Winding for Upward Normals
**Finding**: The existing bottom quad uses winding `bv0, bv2, bv1` / `bv0, bv3, bv2` which faces downward. For the floor cap, we need upward-facing normals so the surface is visible (and lit) when looking down into a hole.

**Resolution**: Used winding `v00, v10, v11` / `v00, v11, v01` which faces upward. The material is `DoubleSide` so both sides render, but correct winding ensures proper lighting.

---

### Discovery 7: Spread Operator Stack Overflow
**Finding**: Using `Math.min(...state.terrain)` with 40,401 elements causes a stack overflow/hang in Playwright's `page.evaluate()`. The spread operator has a limit on argument count.

**Resolution**: Used a manual `for` loop to find the minimum terrain height in test code. (The production code already uses a loop.)

---

### Test Results Summary
- Sprint 14 Quality Gate: **41/41 passed** (no regressions)
- Sprint 15 Bottom Cap Tests: **8/8 passed**
- Total: **49/49 passed**
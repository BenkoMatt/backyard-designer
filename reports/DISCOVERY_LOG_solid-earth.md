# Sprint 14 — Agent 2: Discovery Log

## Working Copy
- Path: `/root/byd14-solid-earth/index.html`
- Starting lines: 17,068
- Git: initialized, base commit `bb9bcd3` (Sprint 13 merge)

## Key Code Locations (in original file)

| Feature | Line (approx) | Description |
|--------|---------------|-------------|
| `EARTH_DEPTH_BELOW_MIN` | 7131 | Depth of earth below min terrain height |
| `GEOLOGICAL_LAYERS` | 7134 | Array of 8 depth-ratio color stops |
| `_getGeologicalLayerColor()` | 7144 | Color lookup by depth ratio (0-1) |
| `buildSolidEarth()` | 7163 | Builds 4 boundary walls + bottom |
| `getSolidEarthBottomY()` | 7265 | Returns bottom Y of solid earth |
| `terrainSegs` | 4243 | Terrain grid resolution |
| `MAX_TERRAIN_HEIGHT` | 4249 | Maximum terrain elevation |
| `MIN_TERRAIN_HEIGHT` | 4250 | Minimum terrain elevation |
| `VOXEL_DEPTH` | 4276 | Voxel grid depth |
| `terrainClipPlane` | 4284 | Y-axis cutaway clip plane |
| `renderer.localClippingEnabled` | 4320 | Already true from Sprint 12 |
| `createTerrainMaterial()` | 4560 | MeshStandardMaterial with vertexColors |
| `initWithYard()` | 6392 | Yard initialization |
| `ensureTerrainArray()` | 7081 | Initializes terrain Float32Array |
| `applyTerrainFull()` | ~7950 | Full terrain update, calls buildSolidEarth |
| Cutaway handler | ~10765 | terrainCutawayInput event handler |
| Cross-section toggle | ~10923 | crossSectionToggleBtn handler |
| Window exports | ~15296 | `window._byd*` debugging API |

## Discoveries

1. **Code is in ES module** — All code is inside a `<script type="module">` tag. Variables are module-scoped, not global. Testing requires using `window._byd*` exposed APIs.

2. **`buildSolidEarth()` already had vertex coloring** — Sprint 12 added geological layer colors based on `(0 - py) / EARTH_DEPTH_BELOW_MIN` (depth below Y=0). Sprint 14 enhances this to use depth below terrain surface instead.

3. **`renderer.localClippingEnabled = true`** was already set at line 4320 (Sprint 12). No change needed.

4. **Terrain initialization** — `initWithYard()` does NOT initialize `state.terrain`. The terrain array is created lazily via `ensureTerrainArray()` when terrain painting starts. `buildSolidEarth()` only runs when `state.terrain` exists.

5. **Wall vertex structure** — `addWallStrip()` creates 4 vertices per strip segment: 2 top (terrain height) + 2 bottom (bottomY). Each vertex has an XZ position that can be used to look up terrain surface height.

6. **Existing clip plane system** — `terrainClipPlane` is a Y-axis cutaway plane. The cross-section clip plane must coexist with it. Three.js supports multiple clipping planes per material via the `clippingPlanes` array.

7. **Cross-section mode existed** — There was already a `crossSectionMode` (click-two-points) feature. The new clipping plane cross-section is an additional, complementary feature in the excavate panel.

8. **VOXEL_DEPTH should match EARTH_DEPTH_BELOW_MIN** — Updated from 32 to 17 for consistency, though voxels are being deprecated.

## Issues Encountered

- **Initial test failure: variables undefined** — Because code is in an ES module, `page.evaluate("EARTH_DEPTH_BELOW_MIN")` returned undefined. Fixed by exposing variables via `window._byd*` API.
- **Solid earth not building** — `initWithYard()` doesn't initialize terrain. Fixed test by calling `ensureTerrainArray()` + `applyTerrainFull()` after init.
- **bv0-bv3 variables** — Removing `const` from the bottom vertex declarations caused implicit globals. Fixed by using `let`.
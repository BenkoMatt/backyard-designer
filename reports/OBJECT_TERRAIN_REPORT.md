# Object-Terrain Conformance Report

**Sprint 10 — Agent 2 (Builder)**  
**Date:** 2026-08-23  
**Working Directory:** `/root/byd10-object-conformance/`

## Summary

All objects in Backyard Designer 3D now conform to the terrain surface. Trees, fences, patios, sheds, and all 18 object types sample terrain height at their position and place themselves at the correct Y elevation. Objects embed slightly into the ground (eliminating visible gaps), flat objects on slopes get visible foundation walls, and heavy objects can flatten terrain to create level building pads.

## Problem Solved

**Before:** Every object was placed at `position.y = 0` (or whatever Y was saved). On deformed terrain, trees floated above hills, patios clipped through slopes, and furniture hovered in valleys.

**After:** Objects sample `getTerrainHeight(x, z)` on placement, drag, and load. They sit at the terrain surface with per-type embedding offsets. Flat objects use 9-point footprint averaging. Foundation walls appear on slopes. Heavy objects can create level pads.

## Implementation Details

### Core Function: `getTerrainHeight(worldX, worldZ)`
Already existed with bilinear interpolation. No changes needed — it correctly interpolates between the 4 nearest heightfield vertices.

### New: `getTerrainHeightAvg(worldX, worldZ, halfW, halfD)`
9-point sampling (center + 4 corners + 4 edge midpoints) for wide/flat objects. Returns the average terrain height across the footprint so patios and decks sit on the mean surface rather than clipping on one side.

### Object Embedding: `EMBED_OFFSETS`
| Object Type | Embed (ft) | Rationale |
|-------------|-----------|-----------|
| tree_deciduous | 0.5 | Trunk sinks into ground |
| tree_evergreen | 0.5 | Trunk sinks into ground |
| bush | 0.2 | Shrub base embeds slightly |
| hedge | 0.2 | Hedge row base embeds |
| fence_privacy | 0.3 | Posts embed into ground |
| fence_picket | 0.3 | Posts embed into ground |
| pergola | 0.2 | Posts embed slightly |
| retaining_wall | 0.5 | Wall base embeds into slope |
| fire_pit | 0.2 | Ring embeds into ground |
| raised_bed | 0.1 | Frame sits on ground |
| patio | 0.0 | Sits flush on surface |
| deck | 0.0 | Sits flush on surface |
| shed | 0.0 | Sits on level pad |
| pool_inground | 0.0 | Excavated into ground |
| hot_tub | 0.0 | Sits on pad |
| walkway | 0.0 | Sits flush on surface |
| chair, table, lounge, grill | 0.0 | Rests on surface |
| lawn | 0.0 | Sits on surface |

### Foundation Walls: `updateFoundationWalls(id)`
For flat objects (`patio`, `deck`, `walkway`, `shed`, `raised_bed`) on sloped terrain where the gap between object base and terrain exceeds 0.3ft:
- Creates 4 concrete-colored BoxGeometry walls around the perimeter
- Wall height = gap + 0.2ft (capped at 8ft)
- Walls extend downward from the object base to the terrain surface
- Only appears when terrain is deformed (not on flat ground)
- Cleaned up on object removal and during compare mode

### Terrain Deformation: `flattenTerrainForObject(obj)`
For heavy objects (`shed`, `pool_inground`, `retaining_wall`):
- Samples average terrain height at object center as pad level
- Flattens all heightfield vertices within the object's rotated footprint (plus 1ft margin)
- Updates terrain mesh and recomputes deformation flag
- Creates a level building pad so the object sits on flat ground

### Updated: `updateObjectHeight(id)`
- Uses `getTerrainHeightAvg` for `FLAT_OBJECT_TYPES` with footprint > 3ft half-width
- Uses `getTerrainHeight` (center point) for vertical objects (trees, bushes, fences, furniture)
- Applies `EMBED_OFFSETS[type]` to sink object base into ground
- Calls `updateFoundationWalls(id)` after positioning
- Called on: object add, object drag end, arrow-key move, terrain modification, load

### Updated: `addObject()`
Changed from `if (state.terrain && pos.y === 0)` to `if (state.terrain)` — always conform to terrain when terrain exists, regardless of initial Y value.

### Updated: Drag Undo/Redo
Changed from `buildSceneObject(dragObject.id)` to `updateObjectHeight(dragObject.id)` in both desktop and touch drag handlers. This ensures Y is recomputed from terrain after undo/redo, preventing objects from retaining stale Y values if terrain changed between operations.

### Save/Load Migration
**Save:** `serializeDesign()` stores the terrain-conformant `position.y` for each object. No changes needed — the Y value is already correct.

**Load:** `loadDesign()` calls `updateObjectHeight(sanitizedObj.id)` after building each object (line 5366). This means old saves with `y=0` are automatically migrated: the object is built at y=0, then `updateObjectHeight` samples the terrain and sets the correct Y. This works for all old saves regardless of terrain state.

## Test Results

**Playwright test suite: `test_terrain_conformance.py` — 38/38 passing**

| Test Category | Tests | Status |
|--------------|-------|--------|
| Function existence | 8 | ✅ All pass |
| Flat terrain sampling | 5 | ✅ All pass |
| Deformed terrain sampling | 3 | ✅ All pass |
| Object on flat (with embed) | 3 | ✅ All pass |
| Object on hill | 3 | ✅ All pass |
| Object in valley | 3 | ✅ All pass |
| Patio on slope (avg height) | 2 | ✅ All pass |
| Foundation walls on slope | 2 | ✅ All pass |
| No foundation walls on flat | 1 | ✅ All pass |
| Save/Load preserves Y | 1 | ✅ All pass |
| Old save migration | 1 | ✅ All pass |
| Terrain deformation | 3 | ✅ All pass |
| Furniture on terrain | 2 | ✅ All pass |
| No console errors | 1 | ✅ All pass |

## What Was NOT Changed
- **Voxel carving system** — underground voxel system untouched, only surface terrain conformance modified
- **`getTerrainHeight` core function** — already correct, no changes needed
- **Terrain brush tools** — raise/lower/smooth/erode modes untouched
- **Terrain presets** — untouched
- **`startCompare`/`endCompare`** — compare mode still flattens to y=0 for visualization; `endCompare` restores via `updateObjectHeight`
- **All existing features** — no regressions; the only change to existing code was strengthening conditions and using `updateObjectHeight` instead of `buildSceneObject` in undo/redo

## Files Modified
- `index.html` — all code changes (6 patches applied)
- `test_terrain_conformance.py` — new Playwright test suite
- `DISCOVERY_LOG.md` — detailed discovery and implementation log
- `OBJECT_TERRAIN_REPORT.md` — this report
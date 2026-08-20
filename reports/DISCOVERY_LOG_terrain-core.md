# Terrain Core Engine Rebuild — Discovery Log

**Agent:** Agent 1 (Builder)
**Date:** August 20, 2026
**Focus:** Terrain Core Engine

---

## Bugs Found & Fixed

### Bug 1: Objects sink/float on deformed terrain — no visual indication of what's buried
**Status:** FIXED
**Discovery:** Objects placed on flat ground become "buried" when terrain is raised around (but not under) them. The `paintTerrain` function does call `updateObjectHeight` for nearby objects, but only within `radius + 5` of the paint center. Objects outside that range that are still affected by the terrain change don't get updated.
**Fix:** Added `isObjectBuried()` function that samples terrain height at the object's footprint corners and compares to the object's base Y. Added a red wireframe outline (`LineSegments`) around buried objects, plus a "⚠ Object is partially buried by terrain" badge in the properties panel. Added `updateAllBuriedIndicators()` called after every terrain modification (paint, flatten, undo, redo, load).

### Bug 2: Raycast misses on deformed terrain — getGroundPointFromEvent() falls back to flat groundPlane at Y=0
**Status:** FIXED
**Discovery:** When the raycast against `yardMesh` misses (e.g., camera angle causes the ray to graze the terrain edge), the fallback uses `groundPlane` at Y=0, which gives wrong coordinates on deformed terrain. The same bug exists in `_getGroundPointFromScreen()` (mobile helper).
**Fix:** Both `getGroundPointFromEvent()` and `_getGroundPointFromScreen()` now do a two-stage fallback: first intersect the Y=0 plane to get rough XZ, then compute `getTerrainHeight()` at that XZ and re-intersect against an elevated plane at that Y value. This gives much more accurate coordinates on deformed terrain.

### Bug 3: Object selection breaks when terrain occludes
**Status:** FIXED
**Discovery:** `onPointerDown()` only raycasted object meshes, not `yardMesh`. When terrain deformed and occluded an object, clicking on the object through the terrain would either miss entirely or select the wrong object. The mobile `_raycastFromScreenPoint()` had the same issue.
**Fix:** Both `onPointerDown()` and `_getMeshesForRaycast()` now include `yardMesh` in the raycast target list. The hit processing uses `hits.find()` to locate the closest hit that belongs to an object (has `userData.objectId`), skipping yardMesh hits. If only terrain is hit, the object is deselected.

### Bug 4: Drag coordinates wrong on deformed terrain
**Status:** FIXED
**Discovery:** `onPointerMove()` during drag already used `getTerrainHeight()` for Y, but the fallback when `yardMesh` raycast missed used `groundPlane` at Y=0, giving wrong XZ coordinates on deformed terrain.
**Fix:** Added terrain-aware fallback to `onPointerMove()` — same two-stage approach as `getGroundPointFromEvent()`: rough XZ from Y=0 plane, then refined intersection at terrain height. Y is always set via `getTerrainHeight()` to ensure the object follows the ground surface.

### Bug 5: Terrain array and mesh can diverge
**Status:** FIXED
**Discovery:** `applyTerrainToMesh()` was not called after all code paths that modify `state.terrain`. Specifically:
- `initWithYard()` recreates the yardMesh geometry but doesn't call `applyTerrainToMesh()` — if called independently (not from `loadDesign`), terrain data is lost from the mesh.
- The flatten button's redo handler set `state.terrain = null` and then called `applyTerrainToMesh()`, which returns early because `state.terrain` is null — the mesh vertices were set to 0 manually, which works, but is inconsistent with the "single source of truth" pattern.
**Fix:** 
- Added `applyTerrainToMesh()` call at the end of `initWithYard()` when `state.terrain` exists.
- All undo/redo handlers now call `applyTerrainToMesh()` after setting `state.terrain`.
- `loadDesign()` calls `_recomputeTerrainDeformed()` then `applyTerrainToMesh()` after restoring terrain data.

### Bug 6: Undo/redo doesn't call applyTerrainToMesh() (verify)
**Status:** VERIFIED & ENHANCED
**Discovery:** The terrain paint undo/redo handlers at lines ~3394 already called `applyTerrainToMesh()`. The flatten undo/redo also called it. However, they didn't update the `terrainDeformed` flag or buried indicators.
**Fix:** All undo/redo handlers now also call `_recomputeTerrainDeformed()` and `updateAllBuriedIndicators()` to keep everything in sync.

### Bug 7: Object-terrain interaction — objects should sit ON surface, buried indicator
**Status:** FIXED
**Discovery:** When terrain is raised under an object, `paintTerrain()` calls `updateObjectHeight()` which moves the object to the new terrain height — this works correctly. When terrain is lowered, the object follows down. However, when terrain is raised AROUND an object (not directly under it), the object can become partially buried with no visual indication.
**Fix:** 
- `updateObjectHeight()` now also calls `updateBuriedIndicator()` for the object.
- `isObjectBuried()` samples terrain at 5 points (center + 4 corners of footprint) and checks if any surrounding terrain is >0.5 units higher than the object base.
- Red wireframe `LineSegments` outline around buried objects.
- "⚠ Object is partially buried by terrain" badge in properties panel with CSS styling.
- `updateAllBuriedIndicators()` called after every terrain modification.
- `removeObject()` cleans up buried indicator meshes.
- `buildSceneObject()` updates buried indicator when object is rebuilt.

### Bug 8: hasTerrainDeformation() is O(n²)
**Status:** FIXED
**Discovery:** `hasTerrainDeformation()` iterated all 2601 vertices (51×51) of the yardMesh geometry every call. This was called from the flatten button handler. While not a hot path, it's wasteful.
**Fix:** Added `state.terrainDeformed` boolean flag. `paintTerrain()` sets it to `true`. Flatten sets it to `false`. `_recomputeTerrainDeformed()` scans the array only when restoring from save/undo (necessary because we can't know the state without checking). `hasTerrainDeformation()` now just returns the flag — O(1).

---

## Additional Bugs Found (Beyond Original List)

### Discovery A: _getGroundPointFromScreen() had same Y=0 fallback bug
**Status:** FIXED
The mobile touch helper `_getGroundPointFromScreen()` had the exact same fallback-to-Y=0 bug as `getGroundPointFromEvent()`. Fixed with the same terrain-aware two-stage fallback.

### Discovery B: Mobile touch selection didn't include yardMesh
**Status:** FIXED
`_getMeshesForRaycast()` only collected object meshes, not yardMesh. This meant mobile tap-to-select couldn't detect terrain clicks for deselection, and terrain occlusion would break selection on mobile too. Fixed by adding yardMesh to the mesh list.

### Discovery C: removeObject() didn't clean up buried indicators
**Status:** FIXED
When an object with a buried indicator was deleted, the indicator mesh would remain in the scene as an orphan. Fixed by adding cleanup in `removeObject()`.

### Discovery D: initWithYard() loses terrain on independent calls
**Status:** FIXED
When `initWithYard()` is called from the wizard (not from `loadDesign`), it recreates the yardMesh but doesn't re-apply terrain. If terrain data exists in `state.terrain`, it's lost from the visual mesh. Fixed by adding `applyTerrainToMesh()` and `updateObjectHeight()` calls at the end of `initWithYard()`.

### Discovery E: Brush cursor doesn't follow terrain height properly
**Status:** NOTED (already works)
The `moveBrushCursor()` function already uses `getTerrainHeight()` for Y placement, so the brush cursor follows deformed terrain. No fix needed.

---

## Ideas Discovered

### Idea 1: Terrain contour lines
**Status:** IDEA (not implemented)
Adding contour lines (like topographic maps) to the terrain mesh would help users visualize elevation changes. Could be implemented as a `LineSegments` overlay that samples terrain heights at regular intervals.

### Idea 2: Terrain height labels
**Status:** IDEA (not implemented)
Showing numeric height labels at key points on the terrain would help users understand elevation. Could be implemented with Three.js `CSS2DRenderer` or sprite-based labels.

### Idea 3: "Snap to surface" mode for object placement
**Status:** IDEA (not implemented)
A toggle that makes objects snap precisely to the terrain surface at their center point, vs. floating at their current Y. This would help when terrain is modified after objects are placed.

### Idea 4: Terrain erosion brush
**Status:** IDEA (not implemented)
A brush mode that simulates natural erosion — lowering high areas and filling low areas based on slope. Would create more natural-looking terrain.

### Idea 5: Terrain presets (hill, valley, slope, plateau)
**Status:** IDEA (not implemented)
Quick-apply terrain shape presets would be useful for users who don't want to sculpt manually. Could be buttons in the terrain controls panel.

### Idea 6: Object "float" indicator (opposite of buried)
**Status:** IDEA (not implemented)
When terrain is lowered under an object, the object could end up floating. A blue indicator (similar to the red buried indicator) would show floating objects.

### Idea 7: Terrain height min/max display
**Status:** IDEA (not implemented)
Showing the current min/max terrain heights in the terrain controls panel would give users feedback about their sculpting.

### Idea 8: Raycast threshold for terrain edge cases
**Status:** IDEA (not implemented)
When the camera is nearly parallel to the terrain, raycasts can miss even on flat terrain. A threshold-based fallback that uses the last known good ground point could improve UX.

---

## Edge Cases Explored

### Edge Case 1: Painting terrain at yard boundary
**Behavior:** `getTerrainIndex()` correctly clamps to [0, segs] range. Painting at the very edge works but the bell curve falloff means less effect at boundaries. No fix needed.

### Edge Case 2: Rapid undo/redo of terrain changes
**Behavior:** Each terrain paint stroke creates an undo command with before/after `Float32Array` copies. Rapid undo/redo correctly restores terrain state and calls `applyTerrainToMesh()`. The `_recomputeTerrainDeformed()` call ensures the flag is correct.

### Edge Case 3: Object dragged outside yard bounds
**Behavior:** `onPointerMove()` clamps XZ coordinates to yard bounds. The `getTerrainHeight()` returns 0 for out-of-bounds positions. No fix needed.

### Edge Case 4: L-shaped yard with terrain
**Behavior:** When yard shape is 'L', `initWithYard()` uses `ShapeGeometry` instead of `PlaneGeometry`. This means the vertex layout is different and `applyTerrainToMesh()` may not work correctly for L-shapes. This is a pre-existing limitation — the terrain system was designed for rectangular yards. Flagging as a known issue.

### Edge Case 5: Multiple objects at same position
**Behavior:** `updateAllBuriedIndicators()` iterates all objects and creates indicators independently. Multiple objects at the same position would each get their own indicator. No conflict.

### Edge Case 6: Terrain deformation flag after load
**Behavior:** `loadDesign()` calls `_recomputeTerrainDeformed()` after restoring terrain data. If the loaded design has all-zero terrain, the flag is correctly set to false. If any non-zero values exist, it's set to true.

---

## Prototypes Built

### Prototype 1: Buried Object Indicator System
**Status:** IMPLEMENTED
Red wireframe outline around buried objects + badge in properties panel. Uses `EdgesGeometry` of a `BoxGeometry` sized to the object's footprint. Samples terrain at 5 points (center + 4 corners) to determine burial.

### Prototype 2: Terrain-Aware Ground Point Fallback
**Status:** IMPLEMENTED
Two-stage fallback: rough XZ from Y=0 plane, then refined intersection at terrain height. Used in `getGroundPointFromEvent()`, `_getGroundPointFromScreen()`, and `onPointerMove()` drag handler.

### Prototype 3: O(1) Terrain Deformation Flag
**Status:** IMPLEMENTED
`state.terrainDeformed` boolean replaces O(n²) vertex scan. Set by `paintTerrain()`, cleared by flatten, recomputed by `_recomputeTerrainDeformed()` during undo/redo/load.

---

## Test Results
All 18 Playwright tests pass:
1. App loads without console errors
2. Three.js scene initialized
3. terrainDeformed flag exists in state
4. hasTerrainDeformation() returns false initially (O(1))
5. paintTerrain sets terrainDeformed flag
6. getTerrainHeight returns non-zero after painting
7. Mesh and array are in sync after paintTerrain
8. isObjectBuried detects buried object (surrounding terrain raised)
9. _recomputeTerrainDeformed correctly updates flag
10. serializeDesign includes terrain data
11. Flatten clears terrainDeformed flag and terrain array
12. yardMesh is in scene for raycast inclusion
13. Undo/redo: applyTerrainToMesh syncs mesh with array
14. updateAllBuriedIndicators runs without error
15. getGroundPointFromEvent is exposed
16. Full terrain workflow runs without errors
17. Object height follows terrain when painted underneath
18. Terrain data persists after operations
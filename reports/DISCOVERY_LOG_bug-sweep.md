# Backyard Designer 3D — Discovery Log
**Agent 3 (Builder) — Bug Testing Team**
**Date: August 20, 2026**

## Discoveries

### D1: TYPE_ABBREV Key Mismatch (CRITICAL BUG — FIXED)
- **Found**: The `TYPE_ABBREV` mapping used shortened keys (`pool`, `hottub`, `raisedbed`, `retainingwall`, `firepit`) that didn't match the actual CATALOG keys (`pool_inground`, `hot_tub`, `raised_bed`, `retaining_wall`, `fire_pit`).
- **Impact**: Share/QR encoding fell back to full type names (longer URLs), and more critically, the reverse mapping couldn't decode abbreviated types. The pool cost was also $0 because `COST_TABLE` used `pool` but `computeObjectCost` looked up `pool_inground`.
- **Fix**: Updated all TYPE_ABBREV and COST_TABLE keys to match CATALOG keys.

### D2: Tape Measure Ignores Terrain (MEDIUM BUG — FIXED)
- **Found**: The tape measure tool's `getGroundPoint()` function raycasted against an invisible flat plane at y=0, ignoring the deformed yard mesh. On sloped terrain, all measurement points were placed at y=0, making distance measurements inaccurate.
- **Impact**: Users measuring distance on hilly terrain got flat horizontal distance, not true surface distance.
- **Fix**: Added raycasting against `yardMesh` first, with fallback to flat plane.
- **Feature idea**: Could add a "surface distance" mode that calculates the actual 3D path length along the terrain surface.

### D3: Terrain + Walk Mode Conflict (LOW BUG — FIXED)
- **Found**: Both terrain editing mode and walk mode could be active simultaneously, causing potential input conflicts. The terrain painting pointer events and walk mode drag controls would compete for the same input.
- **Fix**: Added guard to prevent activating terrain mode while in walk mode.

### D4: Test Harness Stale References (LOW BUG — FIXED)
- **Found**: The `window._test` object captured direct references to `yardMesh`, `gridHelper`, and `boundaryLines` at initialization time. When `initWithYard()` replaced these with new objects, the test harness retained references to old (disposed) meshes.
- **Impact**: Any test that checked mesh positions after `initWithYard()` was called would check the wrong mesh, leading to false failures.
- **Fix**: Changed to getter properties that always return the current value.

### D5: Yard Resize Terrain Data Persistence (KNOWN LIMITATION — DOCUMENTED)
- **Found**: When yard dimensions change via `initWithYard()`, the terrain `Float32Array` data survives but the mesh geometry is recreated. For rectangle shapes with the same segment count, this works fine. But for L-shape yards (which use `ShapeGeometry` instead of `PlaneGeometry`), the vertex layout is completely different, so terrain data doesn't map correctly.
- **Impact**: Terrain data is preserved in state but may not correctly apply to the mesh after a yard shape change.
- **Status**: Documented as a known limitation. A full fix would require remapping terrain values to the new geometry's vertex layout or clearing terrain on shape change.

### D6: Object Height Updates During Terrain Painting (WORKING CORRECTLY)
- **Found**: The `paintTerrain()` function correctly updates object heights for all objects within the brush radius plus a 5-foot margin. This works for both visible and hidden (layer-hidden) objects.
- **Status**: No bug — working as designed.

### D7: Cost Estimator Terrain Independence (WORKING CORRECTLY)
- **Found**: The cost estimator is correctly independent of terrain deformation. Costs are based on object parameters (size, material, etc.), not terrain height. Deforming terrain under an object does not change its cost.
- **Status**: No bug — working as designed.

### D8: Terrain in 2D View (WORKING CORRECTLY)
- **Found**: Terrain data survives 2D/3D view switches without any data loss. The terrain array persists in state and is correctly applied when switching back to 3D.
- **Status**: No bug — working as designed.

### D9: Walk Mode Terrain Following (WORKING CORRECTLY)
- **Found**: Walk mode correctly follows terrain height. The camera Y position is set to `getTerrainHeight(walkPos.x, walkPos.z) + 5.5` (5.5 ft eye height above ground). This means walking up a hill raises the camera and walking into a valley lowers it.
- **Status**: No bug — working as designed. Nice feature!

### D10: Share/QR Terrain Encoding (WORKING CORRECTLY after fix)
- **Found**: After fixing the TYPE_ABBREV keys, terrain data correctly survives the encode/decode roundtrip. The terrain Float32Array is serialized to a regular array in the compact JSON, base64-encoded, and correctly restored on decode.
- **Status**: Working correctly after Bug #1 fix.

### D11: Chaos Testing Results (ALL PASS)
- **Found**: Rapid terrain painting (500 calls) produces no NaN/Infinity values and doesn't crash. View toggles during editing work fine. Undo during painting doesn't corrupt state. The terrain system is robust under chaotic conditions.
- **Status**: No bugs found in chaos testing.

### D12: Mobile Terrain Painting (WORKING CORRECTLY)
- **Found**: Terrain painting works correctly on mobile via touch events. The brush size slider and terrain mode buttons are accessible on mobile. Terrain survives pinch-zoom operations.
- **Status**: No bug — working as designed.

## Feature Ideas

1. **Surface Distance Tape Measure**: Calculate the actual 3D path length along the terrain surface rather than straight-line distance. This would be more useful for real-world planning on sloped terrain.

2. **Terrain Slope Safety Warnings**: Add safety warnings when objects are placed on steep slopes (e.g., "Pool placed on slope > 15° — consider leveling the area"). Currently safety warnings only check object type, not terrain slope.

3. **Terrain Profile View**: A cross-section view showing the terrain elevation profile along a drawn line, useful for drainage planning.

4. **Terrain Contour Lines**: Display contour lines on the terrain in 2D view, showing elevation changes at regular intervals.
# Sprint 6 Discovery Log — Performance & Stability Testing

## Session Info
- **Date**: August 22, 2026
- **Agent**: Agent 2 (Builder) — Performance & Stability Tester
- **Working Directory**: /root/byd6-perf-tester/
- **App**: Backyard Designer 3D (Three.js v0.160.0, single index.html, 11,445 lines)

---

## Discoveries

### D-001: walkLoop Unconditional rAF (MEDIUM)
- **Time**: T+15min
- **Line**: 6989
- **Finding**: `walkLoop()` called `requestAnimationFrame(walkLoop)` unconditionally every frame even when `walkMode=false`. This created a permanent competing rAF loop.
- **Code**: `function walkLoop() { if (walkMode) updateWalkCamera(); requestAnimationFrame(walkLoop); }`
- **Fix**: Only schedule next rAF when `walkMode` is true. Wrapped `enterWalkMode`/`exitWalkMode` to start/stop the loop.
- **Status**: ✅ FIXED

### D-002: sunAnimate Double applySunPosition Call (MEDIUM)
- **Time**: T+20min
- **Line**: 6471-6472
- **Finding**: `sunAnimate()` set `document.getElementById('sun-time').value = t` which triggered the `input` event listener (line 6520, calling `applySunPosition()`), and then explicitly called `applySunPosition()` again — doubling the work per animation frame.
- **Code**: `document.getElementById('sun-time').value = t; applySunPosition();`
- **Fix**: Added `_suppressSunInput` flag to prevent the event listener from firing during programmatic value updates.
- **Status**: ✅ FIXED

### D-003: updateWalkCamera Per-Frame Allocations (MEDIUM)
- **Time**: T+25min
- **Line**: 6895-6896
- **Finding**: `updateWalkCamera()` allocated 4 new `THREE.Vector3`/`THREE.Euler` objects every frame: `new THREE.Vector3(0, 0, -1).applyEuler(new THREE.Euler(0, walkYaw, 0))` — 2 Vector3 + 2 Euler per frame.
- **Fix**: Pre-allocated reusable `_walkFwdVec`, `_walkRightVec`, `_walkEuler` objects outside the function. Used `.set()` instead of `new`.
- **Status**: ✅ FIXED

### D-004: Fence Picket Geometry Proliferation (HIGH)
- **Time**: T+30min
- **Line**: 2241
- **Finding**: `createFence()` created a new `BoxGeometry` for each picket — up to 2000 pickets = 2000 separate geometries. Also created new geometries for each post (up to 100) and rail (2).
- **Code**: `const picket = new THREE.Mesh(new THREE.BoxGeometry(picketW, picketH, 0.12), picketMat);`
- **Fix**: Created shared `picketGeo`, `postGeo`, `railGeo` before the loop and reused across all instances.
- **Impact**: Fence now uses 3 geometries instead of up to 2003.
- **Status**: ✅ FIXED

### D-005: Pergola Geometry Proliferation (HIGH)
- **Time**: T+32min
- **Line**: 2263, 2270, 2278
- **Finding**: `createPergola()` created new BoxGeometry for each post (4), beam (2), and slat (up to 100).
- **Fix**: Shared `postGeo`, `beamGeo`, `slatGeo` across all instances.
- **Status**: ✅ FIXED

### D-006: Patio Line Geometry Proliferation (MEDIUM)
- **Time**: T+34min
- **Line**: 2517, 2522, 2529
- **Finding**: `createPatio()` created new geometries for each paver line and decorative line. Also created a new material for each of the 3 decorative lines.
- **Fix**: Shared line geometries and materials across all instances.
- **Status**: ✅ FIXED

### D-007: Deck Plank/Post Geometry Proliferation (HIGH)
- **Time**: T+36min
- **Line**: 2547, 2555
- **Finding**: `createDeck()` created new `BoxGeometry` for each plank (up to 16 per 16ft depth) and each post (4).
- **Fix**: Shared `plankGeo` and `postGeo` across all instances.
- **Status**: ✅ FIXED

### D-008: Walkway Line Geometry Proliferation (MEDIUM)
- **Time**: T+38min
- **Line**: 2583
- **Finding**: `createWalkway()` created new `BoxGeometry` for each line segment.
- **Fix**: Shared `lineGeo` across all instances.
- **status**: ✅ FIXED

### D-009: Chair/Table/Lounge/Grill Leg Geometry Proliferation (MEDIUM)
- **Time**: T+40min
- **Lines**: 2657, 2675, 2697, 2728
- **Finding**: Chair, table, lounge, and grill factories all created new geometries for each leg (4 per object).
- **Fix**: Shared leg geometries across all legs in each factory.
- **Status**: ✅ FIXED

### D-010: Raised Bed Wall Material Proliferation (LOW)
- **Time**: T+42min
- **Line**: 2602
- **Finding**: `createRaisedBed()` created a new `MeshLambertMaterial` for each of the 4 walls.
- **Fix**: Shared single `wallMat` across all walls.
- **Status**: ✅ FIXED

### D-011: Retaining Wall Geometry Proliferation (LOW)
- **Time**: T+44min
- **Line**: 2621
- **Finding**: `createRetainingWall()` created new `BoxGeometry` for each tier (up to 50 tiers for 50ft walls).
- **Fix**: Shared `tierGeo` and used `scale.y` for actual tier height.
- **Status**: ✅ FIXED

### D-012: saveDesign Pretty-Print Overhead (LOW)
- **Time**: T+50min
- **Line**: 3795
- **Finding**: `saveDesign()` used `JSON.stringify(data, null, 2)` with pretty-printing, adding unnecessary whitespace overhead for large designs.
- **Fix**: Changed to compact `JSON.stringify(data)`.
- **Impact**: ~20% faster serialization for 500 objects (530ms → 420ms).
- **Status**: ✅ FIXED

### D-013: Voxel Mesh Per-Face Rendering (HIGH)
- **Time**: T+60min
- **Line**: 5042-5099
- **Finding**: `buildVoxelMesh()` created one quad (4 vertices, 2 triangles) per exposed voxel face. With 50% carving, this produced 78,750 faces = 315,000 vertices. Build time: 266ms.
- **Fix**: Implemented greedy face merging — for each face direction, scan the voxel grid slice-by-slice and merge adjacent coplanar exposed faces into larger quads.
- **Impact**: 95% vertex reduction (315,000 → 15,000 for 50% carved). Build time: 152ms (43% faster).
- **Status**: ✅ FIXED

### D-014: console.log in Production (LOW)
- **Time**: T+65min
- **Line**: 11441
- **Finding**: A `console.log` statement was left in production code: `console.log('[IA] Tool Dock Navigation System initialized — 6 groups, 30+ features reorganized');`
- **Fix**: Commented out.
- **Status**: ✅ FIXED

### D-015: Walk Button Binding After Monkey-Patch (MEDIUM)
- **Time**: T+70min
- **Line**: 6960
- **Finding**: The walk button's event listener was bound to the original `enterWalkMode` function reference at line 6960. When the walkLoop fix monkey-patched `enterWalkMode` at line 7035, the button still pointed to the old function, so the fix wouldn't take effect when clicking.
- **Fix**: Re-bind the walk button and exit button to the wrapped functions after the monkey-patch.
- **Status**: ✅ FIXED

### D-016: Polling Timers Run Forever (LOW)
- **Time**: T+75min
- **Lines**: 9800, 11045
- **Finding**: `_innovStatsPollTimer` (500ms interval) and `_geoLayerUpdateTimer` (5s interval) run forever via `setInterval`. They do check active state internally, so the actual work is minimal, but the timers never stop.
- **Fix**: Added `typeof` guard for `buildGeoLayerMeshes`. Documented that the intervals already check active state internally. No functional change needed.
- **Status**: ✅ DOCUMENTED (minimal impact)

### D-017: Memory Leak Test — No Leaks Found (PASS)
- **Time**: T+80min
- **Finding**: After creating and deleting 100 objects, JS heap remained at 11.3MB with 0.0MB delta. Geometry count stayed at 8, texture count at 1. After 5 repeat cycles, cumulative leak was 0.0MB.
- **Status**: ✅ PASS (no action needed)

### D-018: Disposal Audit — All Resources Properly Disposed (PASS)
- **Time**: T+85min
- **Finding**: The `disposeGroup()` function at line 2192 correctly traverses the group and disposes all geometries, materials, and textures. The `removeObject()` function also cleans up buried indicator meshes. Renderer info shows geometry/texture counts return to baseline after create/delete cycles.
- **Status**: ✅ PASS (no action needed)

### D-019: Long Session Stability — No Degradation (PASS)
- **Time**: T+90min
- **Finding**: After 25 cycles of rapid add/delete operations over 60 seconds, FPS remained at 60.5 (0.0% degradation) and heap stayed at 11.3MB (0.0MB delta).
- **Status**: ✅ PASS (no action needed)

### D-020: addEventListener vs removeEventListener Imbalance (INFO)
- **Time**: T+95min
- **Finding**: 198 `addEventListener` calls vs only 2 `removeEventListener` calls in the codebase. Most event listeners are added once and never removed. This is typical for single-page apps where the DOM elements persist for the app lifetime, but could be an issue if elements are dynamically created/destroyed.
- **Assessment**: Not a leak in practice — listeners are on persistent elements (window, document, canvas). The 2 removeEventListener calls are for walk mode device orientation, which is correctly cleaned up.
- **Status**: ℹ️ INFO (no action needed)

---

## Summary

| Category | Found | Fixed | Pass |
|----------|-------|-------|------|
| Performance Issues | 9 | 9 | — |
| Memory Leaks | 0 | 0 | 1 |
| Disposal Issues | 0 | 0 | 1 |
| Stability Issues | 0 | 0 | 1 |
| Info/Documented | 2 | 1 | — |
| **Total** | **11** | **10** | **3** |
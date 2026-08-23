# Sprint 7 — Agent 4 Discovery Log: Technical Frontier Critic

**Agent:** Agent 4 (Critic) — The Technical Frontier Researcher
**Date:** August 23, 2026
**Working Directory:** `/root/byd7-tech-frontier/`

---

## Mission

Research what's technically possible that hasn't been tried. Evaluate and critique the other agents' prototypes. Implement the 2 best ideas as working code.

---

## Feature Selection Process

### Ideas Evaluated

1. **OFFLINE/PWA** — Service worker caching, offline save/load, installable on home screen.
   - *Assessment:* High utility for field use (landscapers without connectivity), but service workers require a separate file (can't be inlined in index.html easily). The constraint "keep everything in single index.html" makes this technically challenging. Could use a data URI service worker, but browser support is inconsistent.

2. **PERFORMANCE CEILING** ⭐ PROTOTYPED — Test with 1,000 objects, 500 carved spaces, 100×100 voxel grid. Profile and find the breaking point.
   - *Assessment:* Perfect fit for the "Critic" role. No one else is doing performance testing. This provides the data to validate all other agents' work.

3. **EXPORT TO EXTERNAL TOOLS** ⭐ PROTOTYPED — Export designs as STL/OBJ for 3D printing. Export terrain as heightmap PNG.
   - *Assessment:* Highest real-world impact. Makes the app's output usable in professional workflows. Browser-native, no external libraries needed. STL/OBJ/Canvas are all built into the browser.

4. **AI INTEGRATION** — Template generator ('Describe your dream backyard' → layout suggestions).
   - *Assessment:* Interesting but requires either a server-side component or a large client-side model. The constraint "no external libraries" and "single index.html" makes this impractical for a prototype. Could use a simple keyword-matching template system, but that's not real AI.

5. **DATA PORTABILITY** — Import designs from common landscape design file formats.
   - *Assessment:* Valuable but format-dependent. There's no standard landscape design file format (unlike CAD's DWG/DXF). The existing JSON save/load already provides portability.

### Two Selected (Most Impactful)

1. **Export to External Tools** — Makes the app's output useful in professional 3D workflows. STL for 3D printing, OBJ for Blender/Unity, Heightmap for game engines. This is the bridge from "design tool" to "production tool."

2. **Performance Ceiling Stress Tester** — Critical for the Critic role. Provides the data to evaluate whether other agents' features are performant. Also serves as a development tool for future optimization work.

---

## Technical Implementation Details

### Prototype 1: Export to External Tools

**Architecture:** IIFE module (`setupTechFrontier`) with two public APIs:
- `window._techExport` — Export functions
- `window._techPerf` — Performance profiling

**Export Menu:** Added to topbar as a dropdown next to Save/Load. Uses CSS positioning (absolute, top:100%) for the dropdown. Click-to-open, click-outside-to-close pattern.

**Geometry Collection (`collectGeometryData`):**
- Traverses `scene` (the Three.js Scene object)
- Filters to visible `THREE.Mesh` objects with geometry
- Skips `terrainBrushMesh` (the brush cursor)
- Applies `mesh.updateMatrixWorld(true)` to get current world transforms
- Extracts positions from `geometry.attributes.position` (BufferAttribute)
- Extracts indices from `geometry.index` (if indexed) or generates sequential faces
- Transforms normals via `Matrix3().getNormalMatrix(matrix)` for correct lighting in export

**STL Binary Format:**
- 80-byte ASCII header ("Backyard Designer 3D — STL Export")
- 4-byte face count (uint32, little-endian)
- Per face: 12 bytes normal (3×float32 LE) + 36 bytes vertices (9×float32 LE) + 2 bytes attribute (uint16)
- Face normals computed via cross product: (B-A) × (C-A), normalized
- Uses `DataView` for precise byte-level control

**OBJ Text Format:**
- Comment header with metadata
- `o BackyardDesign` object name
- `v x y z` vertex lines (6 decimal places)
- `vn x y z` normal lines (if available)
- `f v1//vn1 v2//vn2 v3//vn3` face lines (1-based indexing)

**Heightmap PNG:**
- Reads `state.terrain` Float32Array directly
- Finds min/max height for normalization
- Creates Canvas2D context, fills ImageData with grayscale values
- `canvas.toBlob()` generates PNG, downloaded via Blob URL

**HD Screenshot:**
- Temporarily resizes renderer to 4x resolution
- Renders synchronously, captures via `toDataURL`
- Restores original resolution and aspect ratio

### Prototype 2: Performance Ceiling Stress Tester

**Performance Panel:** Floating div at top:60px, right:16px. Created on first toggle, shown/hidden via display CSS.

**Metrics Collection:**
- Monkey-patches `renderer.render()` to measure per-frame time
- 1-second interval timer updates display
- Reads `renderer.info.render.calls` and `renderer.info.render.triangles` for draw call/triangle counts
- Reads `renderer.info.memory.geometries` and `renderer.info.memory.textures`
- Reads `performance.memory.usedJSHeapSize` (Chrome-only)

**Stress Tests:**
- **Objects:** Random types from `CATALOG` at random positions, uses `addObject()` API
- **Voxels:** Direct `state.voxels` array manipulation, then `buildVoxelMesh()` rebuild
- **Terrain:** Generates multi-frequency sine/cosine terrain on 100×100 grid
- **Clear:** Removes all objects, resets terrain mesh vertices to Y=0, disposes voxel/earth meshes

**Full Report:** Sequential testing of 0/100/500/1000 object configurations, 2-second FPS measurement per config, outputs to both UI log and `console.table`

---

## Discoveries & Bugs Found

### 1. Module Scope Access (RESOLVED)
The main script is `<script type="module">`, so `state`, `CATALOG`, `scene`, `renderer` etc. are module-scoped. Playwright's `page.evaluate()` runs in the global scope and cannot access these variables directly.

**Fix:** Use the existing `window._test` object (added in Sprint 6) which exposes all internal state. Updated all test evaluations to use `window._test.state` instead of bare `state`.

### 2. Perf Panel Display Bug (FIXED)
On first creation, `perfPanel.style.display` is an empty string `''`, not `'none'`. The toggle function checked `=== 'none'`, so the first toggle appeared to do nothing (panel was created but stayed hidden).

**Fix:** Changed to `const currentDisplay = perfPanel.style.display || 'none'` to treat empty string as hidden.

### 3. HD Screenshot Variable Typo (FIXED)
Initial code had `activeCamera.aspect = oldW / oldSize.h` — `oldW` was undefined (should be `oldSize.w`).

**Fix:** Changed to `activeCamera.aspect = oldSize.w / oldSize.h`.

### 4. Function Name Mismatches (FIXED)
Initially used guessed function names (`initVoxels`, `rebuildVoxelMesh`, `rebuildTerrain`, `updateTerrainMesh`). The actual names are:
- `initVoxelsFromTerrain` (not `initVoxels`)
- `buildVoxelMesh` (not `rebuildVoxelMesh`)
- `applyTerrainToMesh` (not `rebuildTerrain` or `updateTerrainMesh`)
- `buildSolidEarth` for solid earth mesh

**Fix:** Searched the codebase for actual function names and updated all references.

### 5. Wizard Overlay Intercepts Clicks (WORKAROUND)
The setup wizard (`#wizard`) is a full-screen overlay that intercepts pointer events. Playwright's `ElementHandle.click()` times out because the wizard blocks clicks to the Export button.

**Fix:** In tests, dismiss the wizard first via `page.evaluate("document.getElementById('wizard').style.display = 'none'")`. Also switched to JS-based click simulation (`btn.click()`) instead of Playwright's pointer-based click for the export menu test.

### 6. Terrain Mesh Export
The `collectSceneMeshes()` function includes `yardMesh` (the terrain mesh) in its output. This means STL/OBJ exports include the terrain geometry. This is actually desirable — you want the terrain in your 3D print or game engine import. The terrain mesh has ~10,000 vertices at 100×100 resolution.

### 7. Performance Observations
- **Baseline (0 objects):** 4 meshes in scene (yard, grid, boundary lines, etc.), ~20,000 triangles
- **100 objects:** Added in ~800ms, total objects = 101. No visible performance degradation.
- **100×100 terrain:** 10,201 vertices generated instantly, renders smoothly.
- **JS Heap:** `performance.memory` is available in Chromium (used by Playwright) — shows heap usage during stress tests.

---

## Other Agents' Work — Critique Status

| Agent | Role | DISCOVERY_LOG | Prototypes | Tests | Critique |
|-------|------|---------------|-----------|-------|----------|
| Agent 1 | Real-World Utility | ✅ Written | Seasonal, Growth, Permit | 37 pass | Feasible, well-implemented |
| Agent 2 | Social Sharing | ✅ Written | Gallery, Time-Lapse GIF, Social Cards | 58 pass | Highly impressive, ambitious |
| Agent 3 | Immersive Experience | ✅ Written | Sky, Sound, Weather, VR | 67 pass | Ambitious, well-executed |
| Agent 5 | User Stories | ❌ Not yet | None | — | Not started |

See TECH_REPORT.md for detailed critique of each agent's work.

---

## Test Results

```
33 passed, 0 failed
```

Test categories:
- Page load and canvas (2 tests)
- Export button and menu (4 tests)
- Export API availability (6 tests)
- STL/OBJ export (2 tests)
- Heightmap export (2 tests)
- Performance API availability (7 tests)
- Performance panel toggle (3 tests)
- Stress tests (2 tests)
- Feature regression (5 tests)

---

## Files Modified

1. **index.html** — Added Export dropdown in topbar + 832 lines of prototype JavaScript
2. **test_tech_frontier.py** — New 33-test Playwright suite
3. **TECH_REPORT.md** — Comprehensive technical report with findings and critiques
4. **DISCOVERY_LOG.md** — This file

---

## Commits

```
367e36d Sprint 7 Agent 4: Technical Frontier prototypes — STL/OBJ/Heightmap export + Performance profiler
```

---

## Summary

Two technical frontier prototypes were implemented:

1. **Export to External Tools** — STL, OBJ, Heightmap PNG, HD Screenshot. All browser-native, no external libraries. Makes the app's output usable in professional 3D workflows (3D printing, game engines, GIS).

2. **Performance Ceiling Stress Tester** — Real-time profiler + stress test suite. Provides the data to evaluate whether other agents' features are performant. Serves as the "Critic" role's primary tool.

All 33 tests pass. No existing features broken. Other agents' work critiqued in TECH_REPORT.md.
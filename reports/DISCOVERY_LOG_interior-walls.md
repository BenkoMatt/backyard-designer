# Sprint 15 Agent 1: Interior Earth Walls — Discovery Log

## Date: 2026-08-24

## Key Code Locations Discovered

| Item | Location | Notes |
|------|----------|-------|
| `buildSolidEarth()` | ~line 7190 | Main function for building solid earth mesh with boundary walls |
| `_getNamedGeoLayerColor()` | ~line 7147 | Returns geological layer color based on depth below surface |
| `NAMED_GEO_LAYERS` | ~line 7140 | Topsoil (0-2ft), Subsoil (2-6ft), Clay (6-12ft), Bedrock (12-15ft) |
| `EARTH_DEPTH_BELOW_MIN` | ~line 7105 | Value: 17 — depth below min terrain height for bottom of earth mesh |
| `state.terrain` | Float32Array | Indexed by `iz*(segs+1)+ix`, stores height in feet |
| `terrainAt(ix, iz)` | ~line 7221 | Helper to get terrain height at grid position |
| `addWallStrip()` | ~line 7224 | Builds wall strips for boundary edges |
| `applyTerrainFull()` | ~line 7363 | Full terrain rebuild, calls buildSolidEarth() |
| `_debouncedApplyTerrainFull()` | ~line 7402 | 80ms debounce wrapper for painting |
| `solidEarthMesh` | ~line 4284 | Module-level variable, not global scope |
| `window._test` | ~line 12664 | Test API exposing internal functions for Playwright access |

## Architecture Notes

### Terrain Grid
- Grid size: `(segs+1) × (segs+1)` where `segs = state.terrainSegs` (200)
- Total vertices: 40,401
- World coordinate mapping: `x = (ix/segs)*width - halfW`, `z = (iz/segs)*depth - halfD`
- Yard dimensions: 50ft wide × 100ft deep (default)
- Cell size: width/segs = 0.25ft, depth/segs = 0.5ft

### Solid Earth Mesh Structure
- Bottom quad: 4 vertices at `bottomY = minH - EARTH_DEPTH_BELOW_MIN`
- 4 boundary wall strips: 1 per yard edge, each with `segs` segments × 4 vertices = 800 per strip
- Total boundary vertices: 4 + 4×200×4 = 3204
- Material: `MeshStandardMaterial` with `vertexColors: true`, `DoubleSide`, `roughness: 0.9`
- Geological layer colors applied per-vertex based on depth below terrain surface

### Interior Wall Implementation
- Added after boundary wall strips, before geometry creation
- Scans right (ix+1) and down (iz+1) neighbors only — avoids duplicate edges
- Threshold: 1.0ft height difference
- Only builds where terrain < 0 (dug areas)
- Wall quad: 2 top vertices at higher terrain height, 2 bottom at bottomY
- `surfaceHeights` tracks the higher vertex height for geological color calculation

### Discovery: Duplicate buildSolidEarth() Calls
- Found `buildSolidEarth()` called TWICE in `applyTerrainFull()` (lines ~7397-7398) — wasted CPU
- Found `buildSolidEarth()` called TWICE in `stressTestGenerate()` (lines ~15302-15303)
- Both duplicates fixed in this sprint

### Discovery: window._test API
- `buildSolidEarth`, `solidEarthMesh`, and other internal variables are NOT in global scope
- They're inside a module closure and only accessible via `window._test` object
- `window._test` exposes: `state`, `buildSolidEarth`, `solidEarthMesh` (getter), `applyTerrainFull`, `activeCamera`, `requestRender`, `ensureTerrainArray`, and many more

### Discovery: Terrain Initialization
- `state.terrain` starts as `null` — must call `ensureTerrainArray()` to initialize
- `ensureTerrainArray()` creates `Float32Array((segs+1)*(segs+1))` filled with zeros
- Terrain must be modified to have height differences > 1ft for interior walls to appear
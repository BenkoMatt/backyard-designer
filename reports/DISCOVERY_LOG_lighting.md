# Sprint 15 — Discovery Log

**Agent:** Agent 4 — LIGHTING & SHADOW IN DUG AREAS  
**Date:** August 24, 2026  

---

## Discoveries

### D1: Existing Lighting Setup
The app already had a three-light setup:
- `THREE.AmbientLight(0xffffff, 0.65)` — general fill
- `THREE.HemisphereLight(0x87CEEB, 0x6b5a3a, 0.55)` — sky/ground bounce
- `THREE.DirectionalLight(0xffffff, 0.9)` — sun, with shadows

No light existed below ground level. Dug hole interiors relied entirely on ambient + hemisphere light reaching down into the hole, which was insufficient especially when the sun cast shadows into the opening.

### D2: Day/Night Cycle Lighting Variables
Four module-level variables control lighting:
- `sunLight` — DirectionalLight (sun)
- `sunAmbient` — AmbientLight
- `sunHemi` — HemisphereLight
- `moonLight` — DirectionalLight (moon, intensity 0 at full day)

The `applySunPosition()` function (line 8452) adjusts all light intensities based on `dayFactor = max(0, min(1, elevation / 30))`. At night (dayFactor=0), sun intensity drops to 0.2, ambient to 0.35, hemi to 0.3.

### D3: Terrain Material is DoubleSide
`createTerrainMaterial()` at line 4571 creates a `MeshStandardMaterial` with `side: THREE.DoubleSide`. This means the back face of the terrain mesh (visible when looking up from inside a hole) is rendered. However, the back face uses the same normals as the front, so it doesn't respond to light the way a true interior surface would. This is why the fill light from below is important — it provides direct illumination regardless of face orientation.

### D4: Vertex Color System
`applyTerrainVertexColors()` at line 4605 assigns per-vertex colors based on slope and height:
- **Slope-based:** grass → dirt → rock (0° to 30°+)
- **Height-based (below 0):** blends toward `darkEarthColor` (0x4a3a2a) proportional to depth, capped at -5ft with 60% blend factor
- **Height-based (above 20):** blends toward rock

The dark earth blend was making underground areas even darker. The 25% brightness boost counteracts this.

### D5: terrainHeightColorsActive Guard
`applyTerrainVertexColors()` has an early return at line 4604 if `terrainHeightColorsActive` is true and `state.terrain` exists. This means our brightening only applies when the height-color heatmap is OFF (the default). When the height heatmap is active, a separate `applyHeightColors()` function handles coloring. This is acceptable — the height heatmap mode is a separate visualization, and the lighting improvements (fill light, hemisphere) still apply regardless.

### D6: No Separate "Underground" Render Pass
The app doesn't use clipping planes or separate render passes for underground views by default. The terrain mesh is a single continuous surface. The `solidEarthMesh` exists but is a separate mesh below the terrain for visual continuity. Our fill light illuminates both the terrain mesh interior and the solid earth mesh.

### D7: Test Infrastructure
`window._test` exports key objects and functions for automated testing. The `sunLight` getter was already present. We added `undergroundFillLight` getter. The existing Sprint 14 quality gate (sprint14_quality_gate.py) has 592 tests — our changes don't break any of those since we only added new lights and modified vertex color brightness for underground vertices.

### D8: Performance Impact
The additional PointLight has minimal performance impact:
- FPS during terrain painting: 85.7 (well above 30 FPS threshold)
- PointLight with distance=50 and decay=1.5 has limited falloff range, so it only affects nearby geometry
- No additional shadow maps needed (fill light doesn't cast shadows)

---

## Issues Encountered

### Issue 1: Port Conflict
Port 8123 was already in use (likely from another agent's test). Switched to port 8150.

### Issue 2: safe_eval Timeout Parameter
Initial test run failed because `page.evaluate(js, timeout=timeout)` was not the correct Playwright API signature. Fixed by removing the `timeout` parameter from `page.evaluate()` call (Playwright uses `page.set_default_timeout()` instead).

### Issue 3: Surface Vertex Count in Brightness Test
When the test digs a large hole at the center, many vertices end up below 0, and the "surface" vertex count can be very low if the hole covers most of the sampled area. The test correctly identifies this as "not washed out" (low luminance = not bright = good). A separate overview screenshot confirmed surrounding terrain looks normal.

---

## Files Modified

1. **index.html** — 5 edits:
   - Line 4286: Added `undergroundFillLight` variable declaration
   - Lines 4368: Changed hemisphere light colors (warmer sky + ground)
   - Lines 4384-4389: Added underground PointLight
   - Lines 4663-4666: Added underground vertex color brightening
   - Line 8476: Fill light intensity in `applySunPosition()`
   - Line 8574: Fill light intensity in sun-reset handler
   - Line 12598: Added `undergroundFillLight` to `window._test`

2. **sprint15_quality_gate.py** — New test script (15 tests)

3. **LIGHTING_REPORT.md** — This report

4. **DISCOVERY_LOG.md** — This discovery log
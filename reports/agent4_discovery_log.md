# Sprint 4 Discovery Log — Backyard Designer 3D
## Agent 4 (Critic) — UX Issues Found & Fixed/Logged

### Issues FIXED

#### D-001: No Grid Level Control (FIXED)
- **Severity:** Medium
- **Description:** Grid was always at Y=0 with no UI to change it. Users couldn't set a reference elevation for sloped lots.
- **Fix:** Added grid level slider (-20 to +20 ft) in terrain controls, with visual badge and persistence in save/load.
- **Status:** ✅ Fixed

#### D-002: "Ground Level" vs "Terrain Height" Confusion (FIXED)
- **Severity:** Medium
- **Description:** The terms "ground level" and "terrain height" were never explained. Users wouldn't know the grid plane is separate from the sculpted terrain surface.
- **Fix:** Added explanatory hint text below the grid level slider: "Ground level = where the grid sits (default Y=0). Terrain height = the actual surface shape you sculpt with the brush."
- **Status:** ✅ Fixed

#### D-003: No Visual Cue When Grid Not at Y=0 (FIXED)
- **Severity:** Low
- **Description:** When grid level changes, there was no on-screen indicator showing the current grid elevation.
- **Fix:** Added purple badge at top-center of viewport: "Grid at Y=X ft" — only visible when gridLevel != 0.
- **Status:** ✅ Fixed

#### D-004: Carving Tools Not Discoverable (FIXED)
- **Severity:** High
- **Description:** No dedicated carving tools existed. Users had to use the generic "Excavate" brush mode, which is manual and lacks shape presets. No way to carve specific shapes (box, cylinder, trench).
- **Fix:** Added dedicated "Carving Tools" section to terrain controls with three shape buttons (Box, Round, Trench), adjustable depth/width/length, live preview, and commit button.
- **Status:** ✅ Fixed

#### D-005: No Carving Preview (FIXED)
- **Severity:** High
- **Description:** Users couldn't see what they were going to carve before committing. No visual feedback during carving setup.
- **Fix:** Added live preview mesh (semi-transparent purple with wireframe overlay) that follows the mouse and shows the carving shape with exact dimensions. Updates in real-time as sliders change.
- **Status:** ✅ Fixed

#### D-006: No "Clear All Carvings" Option (FIXED)
- **Severity:** Medium
- **Description:** No quick way to reset all terrain carvings. Users had to manually use "Flatten All Terrain" which is in a different section.
- **Fix:** Added "Clear All Carvings" button in carving tools section that resets all terrain to 0, with undo support and cutaway reset.
- **Status:** ✅ Fixed

#### D-007: Cannot Navigate Below Grid (FIXED)
- **Severity:** High
- **Description:** Camera `maxPolarAngle` was set to `π/2 - 0.05`, preventing users from looking upward or navigating underground. Carved spaces were invisible from below.
- **Fix:** Added "Go Underground" button in view controls that sets `maxPolarAngle = π`, positions camera to look into carved spaces, makes terrain semi-transparent, and shows a depth gauge.
- **Status:** ✅ Fixed

#### D-008: No Depth Feedback Underground (FIXED)
- **Severity:** Low
- **Description:** When navigating underground, users had no indication of how deep they were.
- **Fix:** Added depth gauge overlay (top-right) that shows camera Y position as depth below ground. Updates in real-time as camera moves.
- **Status:** ✅ Fixed

#### D-009: Voxel Faces Not Clearly Defined (FIXED)
- **Severity:** Low
- **Description:** Terrain mesh faces blended together without visible edges. The polygonal aesthetic didn't read as intentional.
- **Fix:** Added edge highlighting via `THREE.EdgesGeometry` with 15-degree threshold. Subtle dark green lines (25% opacity) along terrain edges. Auto-updates with terrain changes.
- **Status:** ✅ Fixed

#### D-010: Grid Level Not Persisted (FIXED)
- **Severity:** Medium
- **Description:** Grid level was not saved or loaded with designs. Changing grid level and saving would lose the setting.
- **Fix:** Added `gridLevel` to `state`, `serializeDesign()` (version 3), and `loadDesign()`. Grid level restored on load.
- **Status:** ✅ Fixed

### Issues LOGGED (Not Fixed — Out of Scope)

#### D-011: Carving Preview Intercepts All Viewport Clicks (LOGGED)
- **Severity:** Low
- **Description:** When carving mode is active, the pointerdown handler with `capture: true` intercepts all viewport clicks, preventing object selection. This is by design (carving mode is exclusive) but could confuse users who expect to select objects while a carving shape is selected.
- **Workaround:** Deselect the carving shape button to return to normal interaction.
- **Status:** 📝 Logged — acceptable trade-off for carving mode exclusivity

#### D-012: Edge Highlight Performance on Large Terrains (LOGGED)
- **Severity:** Low
- **Description:** `EdgesGeometry` rebuilds on every `applyTerrainToMesh()` call. For 100x100 terrain grids (10,201 vertices), this creates ~20K edge line segments. Performance impact is minimal on desktop but could affect low-end devices during rapid terrain painting.
- **Status:** 📝 Logged — could add throttling if performance becomes an issue

#### D-013: Underground View Doesn't Auto-Detect Carved Areas (LOGGED)
- **Severity:** Low
- **Description:** The "Go Underground" camera preset positions based on min terrain height, but doesn't auto-focus on the largest carved area. Users may need to manually orbit to find carved spaces.
- **Status:** 📝 Logged — future enhancement could auto-frame the largest excavation
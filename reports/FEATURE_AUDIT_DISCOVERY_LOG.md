# Sprint 17 — Discovery Log

## Agent 1: Total Feature Audit and Fine-Tune

### Initial State
- Working copy: /root/byd17-feature-audit/index.html (16,566 lines)
- Git initialized at baseline 6b05f5f (Sprint 16, commit 0967d14)
- 676 tests passing at baseline
- HTTP server on port 8765

### Discovery Process

1. **Page Load Analysis**
   - Page loads successfully with no critical console errors
   - Canvas renders correctly (6 canvas elements)
   - WebGL initializes properly (no WebGL error overlay)
   - `yardMesh` (terrain mesh) present and initialized

2. **Terrain Tools (dock → Terrain tab)**
   - All 7 terrain mode buttons present and working: raise, lower, smooth, erode, flatten, dig, fill
   - Brush size slider works (verified 15ft value update)
   - Strength slider works (verified 0.10 value update)
   - Dig depth slider works (visible in dig mode, value 8ft)
   - All 6 terrain presets work: flat, slope, hill, valley, terraced, poolslope
   - Flatten All Terrain button works
   - Smooth Terrain Pass button works
   - Height Colors overlay toggle works
   - Drainage overlay toggle works

3. **Underground Tools (dock → Underground tab)**
   - Dock panel opens correctly
   - Cutaway slider works
   - Opacity slider works
   - Wireframe toggle works
   - Cross-section toggle works (clip controls appear)
   - Buried Objects panel present

4. **Analysis Tools (dock → Analyze tab)**
   - All 6 toggle controls work: slope heatmap, elevation heatmap, contour lines, cut/fill volume, water flow, ghost view
   - Cross-section profile button works
   - Before/After Compare button works

5. **Pro Tools (dock → Pro Tools tab)**
   - Pool Excavation Wizard works
   - Pool width/length/depth sliders all update correctly
   - Precision Flatten Tool works
   - Flatten height slider works
   - Elevation Markers Tool works
   - Precision Slope Tool works
   - Terrain Stats Tool works
   - Retaining Wall Scan button found (id: innov-retwall-btn)

6. **Sun & Shadow (dock → Sun tab)**
   - Sun dock panel opens correctly
   - Time slider works (18:00 display verified)
   - Play Day Cycle button works
   - Reset button works

7. **Measure (dock → Measure tab)**
   - Dock panel opens correctly
   - Tape Measure (viewport button) toggles correctly (aria-pressed: true)
   - Tape Measure (dock button) works

8. **Atmosphere (dock → Atmosphere tab)**
   - All toggles work: sky enhanced, moonlight
   - All 4 weather types work: clear, rain, snow, fog
   - Weather intensity slider works
   - Sound master toggle works
   - Star intensity slider works

9. **Topbar**
   - Undo/Redo buttons present
   - Bird's-eye view toggle works
   - Save Design produces valid JSON download (my-backyard-design.json)
   - Load Design button works
   - Screenshot produces PNG download (~1.2MB)
   - Help modal opens (uses .visible class)
   - Layers panel opens
   - Cost panel opens
   - Walk mode button works
   - Share modal opens with QR code
   - Export menu opens
   - Season panel opens with 4 season buttons (all work)
   - Growth Timeline panel opens
   - Permit Checker panel opens
   - Templates modal opens
   - Label button works
   - Print button works
   - Gallery modal opens
   - Time-Lapse button works
   - Social Card button works

10. **View Controls**
    - Zoom in/out/reset all work
    - Underground view button works (aria-pressed: true)

11. **Object Library**
    - 21 items found in library
    - Clicking first item adds an object to the scene (verified: objects count = 1)

12. **Keyboard Shortcuts**
    - 1→raise, 2→lower, 3→smooth, 4→erode — all working
    - **BUG FOUND**: 5→flatten (should be 5→dig), 6→dig (should be 6→fill)
    - [ and ] brush size — working (8→9→8 verified)
    - X terrain toggle — working
    - Ctrl+Z undo — working
    - Ctrl+Y redo — working
    - Ctrl+S save — working (triggers download)
    - Ctrl+K command palette — working (visible)
    - Ctrl+D duplicate — working
    - V 3D view — working
    - B bird's eye — working
    - W walk mode — working
    - R reset view — working
    - G grid toggle — working
    - T terrain — working

13. **Save/Load**
    - Save produces valid JSON with keys: version, yard, objects, nextId, terrain, terrainSegs, gridLevel, labels
    - Load function exists (loadDesign) but is in script scope (not accessible from page.evaluate, but works via button click)

14. **Console Errors**
    - No critical console errors during full feature exercise
    - Only WebGL performance warnings (GPU stall due to ReadPixels) — expected in headless environment

### Bugs Found

1. **BUG: Keyboard shortcut 5-6 mapping incorrect**
   - `brushModes` array was `['raise', 'lower', 'smooth', 'erode', 'flatten', 'dig']`
   - Should be `['raise', 'lower', 'smooth', 'erode', 'dig', 'fill']`
   - Key 5 was activating `flatten` instead of `dig`
   - Key 6 was activating `dig` instead of `fill`
   - The `fill` mode had NO keyboard shortcut
   - **FIX**: Changed array to correct mapping at line 16471

### Files Modified
- `index.html` line 16471: Fixed `brushModes` array

### Test Artifacts
- audit_test4.py — comprehensive Playwright audit script
- audit4_output.txt — full audit output
- deep_check2.py — deep error checking script
# DISCOVERY_LOG.md — Agent 5 (Critic/Innovation)
## Sprint 4 — Backyard Designer 3D

### Working Directory
`/root/byd4-innovation-4/`

### Brainstorm Session Start
- **Date**: 2026-08-20
- **Focus**: Features enabled by 3D volume terrain and voxel carving

---

## DISCOVERIES

### D1: Codebase Architecture Understanding
- **Found**: index.html is 8,404 lines (before S4 changes). Three.js v0.160.0 via importmap.
- **Key state**: `state.terrain` is a `Float32Array` of height values (100x100 grid = 1ft cells on 100ft yard). `state.terrainSegs` = 100.
- **Solid earth mesh**: `buildSolidEarth()` creates a solid block below terrain surface for excavation visualization — walls + flat bottom. Uses `EARTH_DEPTH_BELOW_MIN = 15` ft below lowest terrain point.
- **Existing tools**: Pool excavation wizard, precision flatten, elevation markers, precision slope tool, terrain stats dashboard, auto retaining wall. All in the Innovation Lab panel.
- **Clipping plane**: `terrainClipPlane` used for cutaway view. Opacity slider exists. Wireframe toggle exists.
- **Key functions**: `excavatePool()`, `paintTerrain()`, `getTerrainHeight()`, `getTerrainIndex()`, `applyTerrainToMesh()`, `buildSolidEarth()`, `getSolidEarthBottomY()`, `makeTextSprite()`.
- **Implication**: The terrain is a heightmap, not a true voxel grid. We can simulate voxel-like behavior by carving regions and coloring the solid earth mesh at different depths.

### D2: Innovation Panel Pattern
- **Found**: Innovation tools follow a pattern: HTML button+panel → JS mode management via `innovSetMode()` → click handler on viewport → prototype function.
- **Pattern**: Each tool has: a button with SVG icon, optional sliders for parameters, info text, and JS logic.
- **Implication**: New prototypes should follow this same pattern for consistency.

### D3: Terrain Data Structure Enables Volume Analysis
- **Found**: The Float32Array terrain allows direct computation of volume by integrating height differences. The solid earth mesh creates visual depth.
- **Volume computation**: `(original_height - current_height) * cell_area` summed over all grid cells = excavation volume.
- **Implication**: We can build a real-time excavation volume calculator, surface area estimator, and depth-to-bedrock indicator using existing terrain data.

### D4: ES Module Scope & Function Reassignment
- **Found**: The file uses `<script type="module">`, so variables and function declarations are in module scope. Functions declared with `function foo()` CAN be reassigned in module scope. However, event listeners that capture the original function reference will still call the original.
- **Pitfall**: Trying to replace `innovSetMode` by reassignment doesn't update already-bound listeners. Better to modify the original function directly.
- **Resolution**: Added the `ugstruct` mode case directly in the original `innovSetMode` function, plus a wrapper for cleanup only.

### D5: Object Reference in Test Exports
- **Found**: When exporting arrays/objects on `window._testS4`, passing them as direct properties captures the reference at that point in time. If the array is reassigned (`undergroundRooms = []`), the exported property still points to the old array.
- **Resolution**: Use getter properties (`get undergroundRooms() { return undergroundRooms; }`) so the test always reads the current value.

### D6: Test Results — Volume Calculator Accuracy
- **Found**: Placing a 12x16x8ft underground room excavates 589 cells. The volume calculator reports 65.0 yd³ cut, 69 ft² wall surface, $975 estimated cost, 7 truck loads. This is consistent with expected values (12*16*8 = 1536 ft³ = 56.9 yd³ plus edge blend volume).

---

## BRAINSTORMED FEATURES (14)

1. **Underground Structure Generator** — Carve rooms with dimensions (basement, root cellar, storm shelter, wine cellar). Click to place rectangular underground rooms with walls and floor visible in cutaway.

2. **Utility Pipe Routing** — Carve trenches and place pipes (water, gas, electrical, drainage). Visualize as colored tubes running underground with depth indicators.

3. **Geological Layer Visualization** — Different colored earth layers at different depths (topsoil, clay, sandstone, bedrock). Shown in cross-section and cutaway views.

4. **Water Table Display** — Show a semi-transparent blue plane at user-set water table depth. Objects below water table are highlighted as "below water".

5. **Excavation Volume Calculator** — Real-time computation of cut/fill volumes. Count cells where terrain < 0 (cut) and > 0 (fill). Display in cubic yards.

6. **Exploded View Mode** — Lift terrain surface upward to reveal underground structures, pipes, and geological layers. Animated transition.

7. **Transparent Earth / X-Ray Mode** — Make terrain semi-transparent to see buried objects and underground features without cutaway.

8. **Voxel Painting System** — Paint voxels/regions different colors representing soil types, rock, water. Stored as overlay data on the terrain grid.

9. **Multi-Level Terrace Designer** — Create terraced underground levels at different depths. Each level is a flat area connected by ramps or stairs.

10. **Depth-to-Bedrock Indicator** — Virtual bedrock plane at configurable depth. Excavation approaching bedrock triggers warning.

11. **Drainage Pipe Network** — Design underground drainage with slope-based pipe routing. Water flows visualized through the network.

12. **Septic System Designer** — Place septic tank and leach field underground. Shows required setbacks and soil compatibility.

13. **Export Carved Volume as STL** — Generate STL file from excavated geometry for 3D printing or external analysis.

14. **Excavation Plan PDF Export** — Generate a simple PDF with cross-section diagrams, volume calculations, and depth annotations.

---

## SELECTED FOR PROTOTYPING

### Prototype 1: Underground Structure Generator ✅
- Carve rectangular rooms underground with user-specified dimensions
- Room types: Basement, Root Cellar, Storm Shelter, Wine Cellar
- Walls and floor rendered as distinct colored meshes with door gap
- Visible through cutaway view
- Shows room volume in cubic feet via toast
- Full undo/redo support

### Prototype 2: Geological Layer Visualization ✅
- Color-coded depth layers: Topsoil (brown), Clay (dark goldenrod), Sandstone (peru), Bedrock (dim gray)
- Shown as translucent planes at configurable depths
- Cross-section reveals layered geology
- User can adjust layer boundary depths via sliders
- Auto-refreshes when terrain changes

### Prototype 3: Excavation Volume Calculator ✅
- Real-time computation of cut/fill volumes from terrain data
- Counts cells where terrain deviates from flat baseline
- Reports in cubic yards, truck loads, wall surface area, max depth
- Shows excavation cost estimate ($15/yd³ cut, $8/yd³ fill)
- Updates every 500ms when active

---

## AI-DISCOVERED IDEAS (Prototyped)

### AI-Discovered 1: Exploded View Animation ✅
- **Discovery**: The solid earth mesh and terrain mesh are separate objects. Animating their Y-offset creates an "exploded view" that reveals underground features.
- **Implementation**: Slider lifts `yardMesh.position.y` and all objects' Y positions while solid earth and underground structures stay in place, revealing the gap.

### AI-Discovered 2: Water Table Visualization ✅
- **Discovery**: A semi-transparent blue plane at a configurable depth creates an intuitive water table visualization. Excavations below it can be detected and warned about.
- **Implementation**: THREE.PlaneGeometry with transparent blue material. Slider for depth. Warning toast when excavation cells are below water table level.

### AI-Discovered 3: Underground Structure Ghost Preview ✅
- **Discovery**: When placing underground structures, showing a semi-transparent ghost preview at hover location helps users understand placement before committing.
- **Implementation**: Raycast to get hover position, show transparent green box mesh with wireframe overlay, commit on click via the underground structure generator.
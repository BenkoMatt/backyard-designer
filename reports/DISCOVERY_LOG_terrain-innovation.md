# Discovery Log — Agent 5 (Critic / Terrain Innovation)

## Session: 2026-08-20

### Discovery 1: Contour Line Saddle Case
**When:** During contour line implementation
**What:** When implementing the marching squares algorithm for contour lines, I discovered that the "saddle case" (where all 4 edges of a cell cross the contour level) requires checking the center value to determine which pair of edges to connect. Getting this wrong produces broken/crossing contour lines.
**Significance:** This is a well-known topology issue in marching squares. The fix is to compare the cell center average to the contour level and connect the appropriate edge pairs.
**Status:** Implemented correctly in `marchContourLevel()`.

### Discovery 2: Slope Calculation at Grid Boundaries
**When:** During slope heatmap implementation
**What:** At grid boundaries (ix=0, iz=0, ix=segs, iz=segs), the central difference formula for slope fails because there are no neighbors on one side. The `getTerrainIndex` function returns null for out-of-bounds, and the fallback returns 0, which underestimates slope at edges.
**Significance:** Edge slopes appear artificially flat. For a prototype this is acceptable, but a production version should use one-sided differences at boundaries.
**Status:** Noted as known limitation. Edge cells show slightly lower slope than reality.

### Discovery 3: Real-Time Overlay Updates During Terrain Painting
**When:** While hooking applyTerrainToMesh for live overlay updates
**What:** By wrapping `applyTerrainToMesh` to also rebuild contour/slope overlays, the analysis layers update in real-time as the user paints terrain. This creates a "magic" feel — you sculpt and watch the contours and slope colors shift live. This was an intentional design choice but the emergent UX is better than expected.
**Significance:** Real-time feedback during terrain editing is a major UX win. Users can immediately see how their edits affect slope safety and drainage patterns.
**Status:** Implemented as the `applyTerrainToMesh` wrapper.

### Discovery 4: Cut/Fill Volume as a Design Constraint
**When:** While implementing the cut/fill calculator
**What:** The cut/fill volume calculator doesn't just show numbers — it creates a design constraint. Users can see in real-time how much earth they're moving. This transforms terrain editing from "make it look nice" to "make it look nice AND minimize earthwork costs." The net volume (cut minus fill) is the key number: if it's close to zero, you're balancing cut and fill on-site, which saves money on hauling.
**Significance:** This is a professional landscaping concept (balanced earthwork) that's usually only in CAD tools. Bringing it to a consumer app is a differentiator.
**Status:** Implemented and working.

### Discovery 5: Cross-Section as a Communication Tool
**When:** While testing the cross-section profile
**What:** The cross-section profile graph isn't just for the designer — it's a communication tool. A homeowner could show this to a contractor: "Here's the elevation profile from my patio to the fence line, and here's where it drops 3 feet." The stats (max slope, avg slope, elevation change) are exactly what a contractor needs to estimate retaining wall height or step count.
**Significance:** Transforms the app from a solo design tool to a client-contractor communication tool.
**Status:** Implemented with stats display.

### Discovery 6: Contour Interval as a Precision Tool
**When:** While testing the contour interval input
**What:** The adjustable contour interval is more powerful than expected. At 1ft intervals, you see fine detail. At 5ft intervals, you see the macro topography. This dual use makes it valuable for both detailed grading work and big-picture site analysis. The 5th contour is darker (index contour) following cartographic convention.
**Significance:** Following standard cartographic conventions (index contours) makes the tool feel professional and familiar to anyone who's read a topo map.
**Status:** Implemented with 1ft default, adjustable 0.1-10ft.

### Discovery 7: Potential Idea — Terrain Stamp/Template Tool
**When:** While brainstorming during implementation
**What:** While building contour lines, I realized a "terrain stamp" tool would be valuable: predefined terrain shapes (hill, valley, ridge, plateau, terrace) that you click to stamp onto the terrain at a location with a given size. This is like a brush but for shapes rather than incremental edits.
**Significance:** Would dramatically speed up common terrain sculpting tasks. Instead of painting a hill stroke by stroke, stamp a perfect Gaussian hill in one click.
**Status:** Logged as future feature idea.

### Discovery 8: Potential Idea — Water Flow Visualization
**When:** While implementing slope analysis
**What:** The slope heatmap shows WHERE water would flow fast, but not WHERE it would GO. A flow accumulation map (simulating raindrops flowing downhill) would show drainage paths and pooling areas. This is computationally feasible: for each grid cell, trace the steepest descent path.
**Significance:** Would be the single most valuable feature for drainage planning — a core homeowner concern.
**Status:** PROTOTYPED as "Water Flow Simulation" feature. Droplets launched from sparse grid, traced downhill via steepest descent, pooling points marked with blue rings.

### Discovery 9: Elevation vs Slope — Complementary Views
**When:** While implementing the elevation heatmap after the slope heatmap
**What:** Coloring by ELEVATION (where am I in height?) is fundamentally different from coloring by SLOPE (how steep is it here?). Both are useful but for different reasons:
- Elevation heatmap: shows the overall landform shape, where the high points and low points are, useful for site planning
- Slope heatmap: shows danger zones, where you need retaining walls, where ADA compliance fails
They're complementary, not redundant. A user might check elevation to understand the landform, then switch to slope to identify problem areas.
**Significance:** Having both views available gives users a complete analytical toolkit. Professional GIS tools have both; bringing this to a consumer app is a differentiator.
**Status:** Both implemented as toggleable overlays.

### Discovery 10: Erosion Brush — Natural Terrain Formation
**When:** While implementing the erosion brush from terrain-core agent's Idea 4
**What:** The erosion brush doesn't just smooth terrain — it creates natural-looking terrain by simulating physical processes. Material flows from high to low areas, creating realistic gullies and deposition fans. The 20% material loss (runoff) is a nice physical touch — not all eroded material stays on site.
**Significance:** This is a "generative" terrain tool — the user doesn't sculpt directly, they guide a natural process. This is a fundamentally different interaction paradigm than raise/lower/smooth. It's more like gardening than sculpting.
**Status:** Implemented as 4th brush mode. Material moves to lowest neighbor with 80% retention.

### Discovery 11: Ghost Mode — Simpler Than Cutaway
**When:** While implementing the buried object ghost view from terrain-viz agent's E7
**What:** The terrain-viz agent implemented a full cutaway slider system (clipping planes, opacity, wireframe). My ghost mode is much simpler — just change object materials to transparent red when buried. Both solve the same problem (seeing buried objects) but ghost mode is:
- Simpler to implement (no clipping planes)
- Always-on (no slider adjustment needed)
- Less disorienting (terrain stays solid)
- Less informative (can't see HOW deep objects are buried)
**Significance:** There's a design lesson here: sometimes the simpler solution is better for the consumer use case. The cutaway is a professional tool; ghost mode is a consumer-friendly indicator.
**Status:** Implemented as toggle in analysis panel.

### Discovery 12: Cross-Section Dual Purpose
**When:** While reviewing terrain-viz agent's E6 discovery about cross-section as diagnostic tool
**What:** The terrain-viz agent independently discovered that cross-section views serve double duty: they're both a buried-object visualization tool AND a terrain analysis tool. Their implementation even overlays objects on the profile. My implementation focuses on the terrain analysis side (slope stats, elevation change). The combination of both approaches would be ideal.
**Significance:** When two independent agents discover the same feature from different angles, it validates the feature's importance. The cross-section profile is clearly a high-value feature.
**Status:** Both agents implemented cross-section independently. My version focuses on terrain stats; their version focuses on buried objects.

### Discovery 13: ES Module Scope — Function Reassignment Fails Silently
**When:** While testing overlay updates during terrain painting
**What:** I initially wrapped `applyTerrainToMesh` with `const _orig = applyTerrainToMesh; applyTerrainToMesh = function() {...}` to update overlays. This silently failed — the wrapper was never called. The terrain-viz agent discovered the same issue (E2): in `<script type="module">`, function declarations create immutable bindings. Reassignment either silently fails or throws in strict mode.
**Significance:** This is a critical gotcha for any agent working in this codebase. Any monkey-patching approach will fail. The fix is to modify the original function body directly or use a callback/event system.
**Status:** Fixed by integrating overlay update calls directly into the `applyTerrainToMesh` function body.

### Discovery 14: _test Object Staleness — yardMesh Captured by Value
**When:** While debugging why applyTerrainToMesh wasn't updating the mesh
**What:** The `window._test` object captured `yardMesh` by value (a reference to the mesh object at creation time). When `initWithYard()` recreates the yardMesh (e.g., after wizard finish), `_test.yardMesh` still points to the OLD, disposed mesh. This caused all terrain tests to appear to fail — the mesh was being updated on the wrong object. The terrain-viz agent found and fixed the same issue (E3).
**Significance:** Any test that checks mesh state via `_test.yardMesh` will get wrong results if the yard has been reinitialized. The fix is to use getter properties: `get yardMesh() { return yardMesh; }`.
**Status:** Fixed by changing `yardMesh`, `scene`, `gridHelper`, `boundaryLines` to getters in the `_test` object.

### Discovery 15: Before/After Compare as a Demonstration Tool
**When:** While implementing the before/after compare from terrain-ux agent's D7
**What:** The "hold to compare" pattern is different from undo. Undo is for reverting changes. Compare is for demonstrating changes — you hold the button to see "before," release to see "after." This is a presentation tool, not an editing tool. It's specifically useful for:
- Real estate agents showing what a hillside lot looks like before/after grading
- Contractors showing clients the impact of proposed terrain work
- Homeowners evaluating their own sculpting decisions
The implementation is simple (save/restore terrain state) but the UX concept is novel for 3D design tools.
**Significance:** Differentiates from competitors by adding a presentation/demonstration dimension. Most tools focus on creation; this adds communication.
**Status:** Implemented as hold-to-compare button with mouse and touch support.
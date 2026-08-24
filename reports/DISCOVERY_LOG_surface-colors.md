# Sprint 15 Agent 2 — Discovery Log

## Investigation Process

### Step 1: Read applyTerrainVertexColors() (line 4599)
- Found the function at line 4599 in index.html
- Current below-grade logic (lines 4651-4662): `heightT = Math.max(0, Math.min(1, -py / 5))` then `tmpHeight.lerpColors(tmpSlope, darkEarthColor, heightT * 0.6)`
- Problem: `tmpSlope` is slope-based (flat terrain = grassColor), so blending 60% toward dark earth at -5ft still keeps 40% green
- Result: flat dug terrain looks dark green, not brown

### Step 2: Read _getNamedGeoLayerColor() (line 7147)
- Found at line 7147, takes `depthBelowSurface` parameter
- Returns {r, g, b} for the geological layer at that depth
- NAMED_GEO_LAYERS at line 7140: topsoil (0-2ft), subsoil (2-6ft), clay (6-12ft), bedrock (12-15ft)
- GEO_LAYER_TRANSITION_WIDTH = 0.5ft for smooth boundaries
- Already has smoothstep-based transitions between layers

### Step 3: Read smoothstep() (line 4678)
- Confirmed smoothstep is defined at line 4678
- Standard implementation: `t*t*(3-2*t)`

### Step 4: Apply the fix
- Added `tmpGeo` THREE.Color temporary
- Replaced the `py < 0` branch with two branches:
  - `py < -0.5`: Full geological layer color via `_getNamedGeoLayerColor(-py)`
  - `-0.5 ≤ py < 0`: Transition zone blending geo color to slope color via smoothstep

### Step 5: Testing setup
- Discovered app uses ES modules (`<script type="module">`) — all variables scoped to module
- `window.state` exposed at line 16656 but only for `state`, not other functions
- Added window exports for: `applyTerrainVertexColors`, `_getNamedGeoLayerColor`, `NAMED_GEO_LAYERS`, `smoothstep`, `yardMesh`, `applyTerrainFull`, `applyTerrainPositions`
- Headless Chromium needs `--use-gl=swiftshader --enable-unsafe-swiftshader` for WebGL (software rendering)
- Without swiftshader: module fails with "Cannot read properties of undefined (reading 'addEventListener')" because renderer.domElement is null

### Step 6: Verification
- Test 1: Single hole at -8ft → clay color (reddish), grass still green at 0ft ✓
- Test 2: Multiple holes at -1, -3, -5, -8, -13 ft → topsoil (dark brown), subsoil (brown), clay (reddish), bedrock (gray) ✓
- All transitions smooth, no page errors

## Key Findings
1. The geological layer color system (`_getNamedGeoLayerColor`, `NAMED_GEO_LAYERS`) already existed but was only used for the solid earth side walls, not the terrain surface
2. The fix was straightforward: replace the lerpColors blend with direct geological layer color for py < -0.5, with a 0.5ft smoothstep transition at y=0
3. ES module scope isolation requires explicit window exports for Playwright testing
4. SwiftShader software rendering is required for WebGL in headless Chromium
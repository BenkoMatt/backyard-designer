# Visual Review Report — Sprint 10, Agent 5 (Critic)

## Backyard Designer 3D — Terrain UX & Visual Review

**Agent:** Agent 5 (Critic) — Terrain UX & Visual Reviewer  
**Date:** 2026-08-23  
**Working Directory:** `/root/byd10-visual-reviewer/`

---

## Executive Summary

The terrain system in Backyard Designer 3D is **visually solid**. The terrain uses smooth shading (indexed geometry with per-vertex normals), high resolution (10,201 vertices, 0.5ft cells), and proper lighting. Two visual issues were found and fixed: edge seams and smoothing kernel quality. The terrain now looks clean and professional.

### Issues Found: 4
### Issues Fixed: 3
### Issues Noted (outside scope): 1

---

## 1. Visual Quality

### Terrain Geometry
| Property | Value | Assessment |
|----------|-------|------------|
| Vertex count | 10,201 | ✅ High detail |
| Triangle count | 20,000 | ✅ Smooth surface |
| Grid resolution | 100×100 segments | ✅ 0.5ft cells |
| Indexed geometry | Yes | ✅ Shared vertices |
| Per-vertex normals | Yes (10,201 = vertex count) | ✅ Smooth shading |
| Flat shading | No (`flatShading: false`) | ✅ No facets |
| Normal recomputation | `computeVertexNormals()` after every `applyTerrainToMesh()` | ✅ Correct |
| UV coordinates | Present | ✅ Texture-ready |
| Double-sided | Yes (`DoubleSide`) | ✅ No invisible triangles |

### Material
| Property | Value | Assessment |
|----------|-------|------------|
| Type | MeshLambertMaterial | ✅ Good for diffuse terrain |
| Color | #6b8a4a (grass green) | ✅ Natural |
| Transparent | Yes (opacity 1.0) | ✅ Ready for excavation view |
| Vertex colors | Disabled (until height colors toggle) | ✅ Clean default |
| Texture map | None | ⚠️ Flat appearance (Agent 3 addressing) |

### Lighting
| Light | Type | Intensity | Purpose |
|-------|------|-----------|---------|
| Ambient | AmbientLight | 0.5 | Base illumination |
| Hemisphere | HemisphereLight | 0.4 | Sky/ground color blending |
| Sun | DirectionalLight | 0.9 | Primary light + shadows |
| Fill | DirectionalLight | 0.1 | Shadow area fill |

### Atmospheric Effects
- **Fog**: Present (`THREE.Fog`) — provides depth cueing
- **Shadows**: Terrain receives and casts shadows

### Verdict: ✅ No visible facets, seams, or artifacts on the terrain surface itself

---

## 2. Sculpting Feel

### Brush Falloff
- **Function**: `Math.pow(1 - t², 2)` where `t = distance / brushRadius`
- **Shape**: Polynomial bell curve — smooth from center (1.0) to edge (0.0)
- **Test**: Single stroke at center → peak 1.0, symmetric falloff, only 2 minor discontinuities at brush edge
- **Verdict**: ✅ Natural, smooth falloff

### Brush Modes
| Mode | Function | Assessment |
|------|----------|------------|
| Raise | `terrain[vi] += strength * falloff * edgeFactor` | ✅ Works |
| Lower | `terrain[vi] -= strength * falloff * edgeFactor` | ✅ Works |
| Smooth | 5×5 Gaussian-weighted average | ✅ Improved (was 3×3 box) |
| Erode | Finds lowest neighbor, transfers material | ✅ Works |

### Smoothing Effectiveness
| Metric | Before Fix | After Fix |
|--------|-----------|-----------|
| Kernel size | 3×3 box | 5×5 Gaussian |
| Roughness before | 109.69 | 109.69 |
| Roughness after 20 passes | 36.87 (66.4% reduction) | 32.82 (70.1% reduction) |
| Improvement | 66.4% | 70.1% |

**Verdict**: ✅ Smoothing works well, now produces smoother results with Gaussian weighting

### Responsiveness
- `paintTerrain()` is called on every pointer move during sculpting
- `applyTerrainToMesh()` updates the GPU buffer and recomputes normals immediately
- `requestRender()` triggers a frame draw
- **Verdict**: ✅ Terrain updates in real-time during sculpting

---

## 3. Object Placement

### Test Results
All objects placed at 6 different terrain configurations:

| Location | Object | Terrain Height | Object Y | Height Diff | Sits Well? |
|----------|--------|---------------|----------|-------------|------------|
| Flat area | tree_deciduous | 0.06 | 0.06 | 0.00 | ✅ |
| Hill top | tree_evergreen | 5.00 | 5.00 | 0.00 | ✅ |
| Valley | bush | -2.40 | -2.40 | 0.00 | ✅ |
| Slope | chair | 1.50 | 1.50 | 0.00 | ✅ |
| Terrain edge | hedge | 0.00 | 0.00 | 0.00 | ✅ |
| Steep slope | tree_deciduous | 2.50 | 2.50 | 0.00 | ✅ |

**Verdict**: ✅ All objects sit exactly on the terrain surface with zero height difference

### Edge Cases
- **Steep slopes**: Objects follow terrain height at their center point — no floating or sinking
- **Terrain edges**: Objects at boundary sit at height 0 (edge feathering ensures this)
- **Carved terrain**: Objects update height when terrain is modified nearby (within `radius + 5`)

---

## 4. Before/After Comparison

### Issue 1: Edge Seams

**Before** (sculpting at x=20, z=20 with brush size 15):
- 27 non-zero edge vertices
- Maximum edge height: 0.79ft
- Visible cliff at yard boundary

**After** (with edge feathering):
- 0 non-zero edge vertices
- Maximum edge height: 0.00ft
- Smooth transition to ground level at boundaries

Screenshots:
- `screenshots/07_edge_sculpt.png` — Before fix (edge cliff visible)
- `screenshots/10_after_edge_feather.png` — After fix (smooth edge)

### Issue 2: Smoothing Quality

**Before** (3×3 box kernel):
- Roughness reduction: 66.4%
- Slightly blocky smoothing pattern

**After** (5×5 Gaussian kernel):
- Roughness reduction: 70.1%
- Smooth, natural Gaussian blur effect

### Issue 3: Preset Edge Clamping

**Before**:
- Slope preset: non-zero heights at edges (linear slope extends to boundary)
- Terraced preset: steps start at non-zero height at one edge
- Pool slope: non-zero at all edges

**After** (with edge feathering):
- All presets: maxEdge = 0.000
- Smooth transition at all boundaries

Screenshots:
- `screenshots/11_after_hill_preset_feathered.png` — Hill preset with feathered edges
- `screenshots/12_after_slope_preset_feathered.png` — Slope preset with feathered edges
- `screenshots/13_after_terraced_preset.png` — Terraced preset with feathered edges
- `screenshots/14_objects_on_feathered_hill.png` — Objects on feathered hill

---

## 5. Mobile Visual (375px)

| Property | Value | Assessment |
|----------|-------|------------|
| App initialization | Success | ✅ |
| Terrain geometry | Same as desktop (10,201 vertices) | ✅ |
| Smooth shading | Yes | ✅ |
| FPS (headless) | ~40 FPS | ✅ (software rendering; real GPU would be higher) |
| Console errors | 0 | ✅ |

Screenshots:
- `screenshots/08_mobile_flat.png` — Flat terrain on mobile
- `screenshots/09_mobile_sculpted.png` — Sculpted terrain on mobile

**Verdict**: ✅ Terrain looks good on mobile, same visual quality as desktop

---

## 6. Walk Mode on Terrain

| Test | Result | Assessment |
|------|--------|------------|
| Walk mode activation | Activates via button click | ✅ |
| Walk controls visible | Yes | ✅ |
| Camera follows terrain | Yes — cameraY = terrainHeight + 5.5ft eye height | ✅ |
| Walking forward (W key) | Camera moves in look direction | ✅ |
| Terrain following | cameraY=15.49, terrainH=9.99, eyeHeight=5.5ft | ✅ |

**Verdict**: ✅ Walk mode correctly follows terrain height. You can walk up a hill and the camera rises with the terrain. The eye height (5.5ft) is realistic for a person.

---

## 7. Issues Summary

### Fixed (3 issues)

| # | Issue | Severity | Fix |
|---|-------|----------|-----|
| 1 | Edge seams — terrain cliffs at yard boundaries | Medium | Edge feathering in `paintTerrain()` (10% feather zone) |
| 2 | Preset edge seams — non-zero heights at boundaries | Medium | Edge feathering in `applyTerrainPreset()` (8% feather zone) |
| 3 | Smoothing quality — 3×3 box kernel too coarse | Low-Medium | Upgraded to 5×5 Gaussian-weighted kernel |

### Noted (1 issue, outside scope)

| # | Issue | Severity | Note |
|---|-------|----------|------|
| 4 | No texture map on terrain | Low | Agent 3 (Terrain Material) is addressing with vertex colors and procedural texture |

### False Positives (2 items initially flagged, verified correct)

| # | Initial Finding | Verification |
|---|----------------|-------------|
| - | "Normals not recomputed after sculpt" | False positive — test sampled corner vertices instead of sculpt center. Normals ARE recomputed (110/121 changed near sculpt site). |
| - | "Terrain presets produce flat terrain" | False positive — test used wrong preset names. Correct names: flat, slope, hill, valley, terraced, poolslope. All work correctly. |

---

## 8. Cross-Agent Findings

### Agent 1 (Terrain Smoothing)
- Upgraded terrainSegs to 200 (40,401 vertices) — 4× more detail
- Changed to MeshStandardMaterial
- Changed brush falloff to cosine curve
- Also independently upgraded to 5×5 smoothing
- **Compatibility**: My edge feathering works with any terrainSegs value

### Agent 2 (Object Conformance)
- Added footprint-averaged height sampling for wide objects
- Added embedding offsets (trees sink 0.5ft into ground)
- Added foundation walls for flat objects on slopes
- Added terrain flattening for heavy objects
- **Compatibility**: My edge feathering doesn't interfere with object placement

### Agent 3 (Terrain Material)
- Added vertex colors (grass/dirt blending)
- Added procedural texture
- Fixed Three.js Color API issue
- **Compatibility**: My edge feathering applies to terrain heights, not colors — compatible

---

## 9. Conclusion

The terrain in Backyard Designer 3D **looks good visually**. The key strengths are:
1. **Smooth shading** — no visible facets or artifacts
2. **High resolution** — 0.5ft cell size provides excellent detail
3. **Proper normals** — recomputed after every terrain modification
4. **Good lighting** — 4-light setup with shadows and fog
5. **Objects sit naturally** — zero height difference on all terrain types
6. **Walk mode works** — camera follows terrain with realistic eye height

The fixes applied (edge feathering + Gaussian smoothing) improve the visual quality at yard boundaries and make the smoothing brush more effective. The terrain is ready for production use.
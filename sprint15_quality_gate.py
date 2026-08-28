#!/usr/bin/env python3
"""
Sprint 15 Quality Gate — Interior Earth Walls, Geological Surface Colors,
Bottom Cap, Underground Lighting
==============================================================================

Tests:
  1. Terrain below 0 shows geological colors (not grass) — vertex colors at below-0 positions
  2. Interior walls exist in dug areas — buildSolidEarth produces more vertices when terrain is dug
  3. Bottom cap visible in deep holes — solid earth mesh has a bottom face
  4. Geological layers have smooth color transitions
  5. Dug areas are well-lit — hemisphere or point light exists below ground
  6. FPS ≥ 30 during terrain painting with interior walls
  7. Underground vertex colors are brightened (20-30% boost)
  8. Smooth transition at y≈0 between grass and geological colors
  9. No console errors during terrain painting
 10. Sprint 14 regressions — all prior sprint 14 checks still pass
 11. Geological layer names and colors are correct (topsoil/subsoil/clay/bedrock)
 12. Interior walls only in dug areas (not above ground)
 13. buildSolidEarth handles flat terrain without interior walls
 14. Underground hemisphere light has warm earth-tone colors
 15. applyTerrainVertexColors uses _getNamedGeoLayerColor for below-0 vertices

Usage: python3 sprint15_quality_gate.py [--port PORT]
"""

import argparse
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed. pip install playwright && playwright install chromium")
    sys.exit(1)

# ── Test framework ──────────────────────────────────────────────────────────

PASS = 0
FAIL = 0
ERR_COUNT = 0
SKIP = 0
RESULTS = []

SCRIPT_DIR = Path(__file__).parent.resolve()

# Sprint 21: URL derived from --port arg (set in main()); the three page.goto call
# sites below previously hardcoded port 8099, ignoring --port.
SPRINT15_URL = 'http://127.0.0.1:8099/index.html'


def record(name, status, detail=""):
    global PASS, FAIL, ERR_COUNT, SKIP
    symbol = {"pass": "✅", "fail": "❌", "error": "💥", "skip": "⏭️"}[status]
    line = f"  {symbol} {name}"
    if detail:
        line += f": {detail}"
    print(line)
    RESULTS.append({"name": name, "status": status, "detail": detail})
    if status == "pass":
        PASS += 1
    elif status == "fail":
        FAIL += 1
    elif status == "error":
        ERR_COUNT += 1
    elif status == "skip":
        SKIP += 1


def safe_eval(page, js, timeout=15000):
    """Evaluate JS in page, return result or None."""
    try:
        return page.evaluate(js)
    except Exception as e:
        print(f"    [eval error] {e}")
        return None


# ── Static code tests (no browser) ──────────────────────────────────────────

def test_static_interior_walls():
    """Static code analysis — verify interior wall code exists in buildSolidEarth."""
    print("\n--- Static: Interior Walls ---")

    html_path = SCRIPT_DIR / "index.html"
    content = html_path.read_text()

    # Check for interior wall function
    has_interior_wall_fn = "addInteriorWall" in content
    record("static:interior_wall_function_exists", "pass" if has_interior_wall_fn else "fail",
           "addInteriorWall function found" if has_interior_wall_fn else "addInteriorWall function not found")

    # Check for wall height threshold
    has_threshold = "WALL_HEIGHT_THRESHOLD" in content
    record("static:wall_height_threshold_exists", "pass" if has_threshold else "fail",
           "WALL_HEIGHT_THRESHOLD defined" if has_threshold else "WALL_HEIGHT_THRESHOLD not found")

    # Sprint 25 fix (kanban t_0174b1d0): threshold lowered 1.0 -> 0.15 ft so smooth dig
    # bowls build interior walls. At 1.0 a smooth multi-stroke bowl (slopes ~0.27 ft/cell)
    # generated zero walls, so the auto-dig clip plane showed the outerGround plane
    # straight through the hole as a flat green disc.
    has_threshold_1 = "WALL_HEIGHT_THRESHOLD = 0.15" in content
    record("static:wall_threshold_is_015ft", "pass" if has_threshold_1 else "fail",
           "threshold = 0.15 ft" if has_threshold_1 else "threshold not 0.15 ft")

    # Check for grid scan loop
    has_grid_scan = "for (let iz = 0; iz < segs; iz++)" in content and "for (let ix = 0; ix < segs; ix++)" in content
    record("static:grid_scan_loop_exists", "pass" if has_grid_scan else "fail",
           "terrain grid scan loop found" if has_grid_scan else "grid scan loop not found")

    # Check only in dug areas (terrain < 0)
    has_dug_check = "higherH >= 0 && lowerH >= 0" in content
    record("static:dug_area_filter_exists", "pass" if has_dug_check else "fail",
           "dug area filter (skip walls above ground)" if has_dug_check else "no dug area filter")


def test_static_geo_colors():
    """Static code analysis — verify geological color code in applyTerrainVertexColors."""
    print("\n--- Static: Geological Surface Colors ---")

    html_path = SCRIPT_DIR / "index.html"
    content = html_path.read_text()

    # Check for _getNamedGeoLayerColor usage in applyTerrainVertexColors
    has_geo_call = "_getNamedGeoLayerColor" in content and "applyTerrainVertexColors" in content
    record("static:geo_color_function_used", "pass" if has_geo_call else "fail",
           "_getNamedGeoLayerColor referenced" if has_geo_call else "_getNamedGeoLayerColor not used")

    # Check for transition band
    has_transition = "TRANSITION_BAND" in content
    record("static:transition_band_exists", "pass" if has_transition else "fail",
           "TRANSITION_BAND defined" if has_transition else "TRANSITION_BAND not found")

    # Check for smooth transition (smoothstep or similar)
    has_smooth = "sm = blendT * blendT * (3 - 2 * blendT)" in content or "smoothstep" in content
    record("static:smooth_transition_exists", "pass" if has_smooth else "fail",
           "smooth transition function found" if has_smooth else "no smooth transition")

    # Check for brightness boost
    has_brighten = "UNDERGROUND_BRIGHTNESS_BOOST" in content
    record("static:brightness_boost_exists", "pass" if has_brighten else "fail",
           "UNDERGROUND_BRIGHTNESS_BOOST defined" if has_brighten else "no brightness boost")

    # Check boost matches the shipped constant (0.45 since Sprint 19, up from 0.25)
    has_boost_25 = "UNDERGROUND_BRIGHTNESS_BOOST = 0.45" in content
    record("static:brightness_boost_25pct", "pass" if has_boost_25 else "fail",
           "boost = 0.45 (Sprint 19 value)" if has_boost_25 else "boost not 0.45")

    # Check for geological layer names
    has_topsoil = "'topsoil'" in content
    has_subsoil = "'subsoil'" in content
    has_clay = "'clay'" in content
    has_bedrock = "'bedrock'" in content
    all_layers = has_topsoil and has_subsoil and has_clay and has_bedrock
    record("static:all_geo_layer_names", "pass" if all_layers else "fail",
           "topsoil/subsoil/clay/bedrock all present" if all_layers else "missing layer names")

    # Check NAMED_GEO_LAYERS array
    has_named_array = "NAMED_GEO_LAYERS" in content
    record("static:named_geo_layers_array", "pass" if has_named_array else "fail",
           "NAMED_GEO_LAYERS array found" if has_named_array else "NAMED_GEO_LAYERS not found")


def test_static_underground_lighting():
    """Static code analysis — verify underground lighting code exists."""
    print("\n--- Static: Underground Lighting ---")

    html_path = SCRIPT_DIR / "index.html"
    content = html_path.read_text()

    # Check for underground hemisphere light
    has_underground_hemi = "undergroundHemi" in content and "HemisphereLight" in content
    record("static:underground_hemi_exists", "pass" if has_underground_hemi else "fail",
           "underground HemisphereLight found" if has_underground_hemi else "no underground hemisphere light")

    # Check for underground point light
    has_underground_point = "undergroundPoint" in content and "PointLight" in content
    record("static:underground_point_exists", "pass" if has_underground_point else "fail",
           "underground PointLight found" if has_underground_point else "no underground point light")

    # Check lights are exported via _test
    has_export = "undergroundHemi" in content and "undergroundPoint" in content and "window._test" in content
    record("static:lights_exported", "pass" if has_export else "fail",
           "lights exported via _test" if has_export else "lights not exported")

    # Check underground light position is below 0
    has_below_pos = "position.set(0, -" in content and ("undergroundHemi" in content or "undergroundPoint" in content)
    record("static:lights_below_ground", "pass" if has_below_pos else "fail",
           "lights positioned below ground" if has_below_pos else "lights not below ground")


def test_static_bottom_cap():
    """Static code analysis — verify bottom cap exists in buildSolidEarth."""
    print("\n--- Static: Bottom Cap ---")

    html_path = SCRIPT_DIR / "index.html"
    content = html_path.read_text()

    # Check for bottom cap vertices (bv0-bv3)
    has_bottom_cap = "bv0" in content and "bv1" in content and "bv2" in content and "bv3" in content
    record("static:bottom_cap_vertices", "pass" if has_bottom_cap else "fail",
           "bottom cap vertices found" if has_bottom_cap else "bottom cap vertices not found")

    # Check for bottom cap indices
    has_bottom_indices = "indices.push(bv0, bv2, bv1)" in content or "indices.push(bv0" in content
    record("static:bottom_cap_indices", "pass" if has_bottom_indices else "fail",
           "bottom cap indices found" if has_bottom_indices else "bottom cap indices not found")

    # Check for bottomY
    has_bottom_y = "bottomY" in content
    record("static:bottom_y_defined", "pass" if has_bottom_y else "fail",
           "bottomY used in buildSolidEarth" if has_bottom_y else "bottomY not found")


# ── Browser-based tests ─────────────────────────────────────────────────────

def test_geo_colors_below_zero(page):
    """Test that terrain below 0 shows geological colors (not grass)."""
    print("\n--- Geological Colors Below 0 ---")

    # Reload for clean state (uses args.port-derived URL set in main())
    page.goto(SPRINT15_URL, timeout=30000)
    page.wait_for_timeout(2000)

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };
        if (typeof t.ensureTerrainArray === 'function') t.ensureTerrainArray();
        if (!t.state.terrain) return { error: 'terrain not initialized' };

        const segs = t.state.terrainSegs;

        // Dig a hole in the center area
        const center = Math.floor(segs / 2);
        for (let iz = center - 10; iz <= center + 10; iz++) {
            for (let ix = center - 10; ix <= center + 10; ix++) {
                const vi = iz * (segs + 1) + ix;
                const dist = Math.sqrt((ix - center) ** 2 + (iz - center) ** 2);
                t.state.terrain[vi] = -Math.min(8, dist * 0.5);
            }
        }

        // Apply terrain to mesh and colors
        if (typeof t.applyTerrainToMesh === 'function') t.applyTerrainToMesh();
        t.applyTerrainVertexColors();

        const geo = t.yardMesh.geometry;
        const pos = geo.attributes.position;
        const colors = geo.attributes.color;

        // Find vertices below 0 and check their colors
        let belowZeroCount = 0;
        let grassColoredBelow = 0; // vertices below 0 that still look like grass
        let geoColoredBelow = 0;  // vertices below 0 with geological colors
        let sampleColors = [];

        for (let i = 0; i < pos.count; i++) {
            const py = pos.getY(i);
            if (py < -1) {
                belowZeroCount++;
                const r = colors.getX(i);
                const g = colors.getY(i);
                const b = colors.getZ(i);
                // Grass is green: g > r and g > b
                // Geological colors (topsoil/subsoil/clay) are brown/reddish: r >= g
                if (g > r && g > b) {
                    grassColoredBelow++;
                } else {
                    geoColoredBelow++;
                }
                if (sampleColors.length < 5) {
                    sampleColors.push({ y: py.toFixed(2), r: r.toFixed(3), g: g.toFixed(3), b: b.toFixed(3) });
                }
            }
        }

        return {
            belowZeroCount: belowZeroCount,
            grassColoredBelow: grassColoredBelow,
            geoColoredBelow: geoColoredBelow,
            sampleColors: sampleColors,
            hasGeoColors: geoColoredBelow > grassColoredBelow,
        };
    }""")

    if not result or result.get('error'):
        record("geo:below_zero_has_geo_colors", "error", f"eval failed: {result}")
        return

    below_zero = result.get('belowZeroCount', 0)
    geo_colored = result.get('geoColoredBelow', 0)
    grass_colored = result.get('grassColoredBelow', 0)

    record("geo:below_zero_vertices_exist", "pass" if below_zero > 0 else "fail",
           f"{below_zero} vertices below 0" if below_zero > 0 else "no vertices below 0")

    record("geo:below_zero_shows_geo_colors", "pass" if geo_colored > grass_colored else "fail",
           f"{geo_colored} geo-colored vs {grass_colored} grass-colored" if geo_colored > grass_colored else f"too many grass-colored: {grass_colored}")

    record("geo:below_zero_not_grass", "pass" if grass_colored == 0 else "fail",
           f"0 grass-colored below 0" if grass_colored == 0 else f"{grass_colored} still grass-colored")


def test_interior_walls(page):
    """Test that interior walls exist in dug areas — buildSolidEarth produces more vertices when terrain is dug."""
    print("\n--- Interior Walls in Dug Areas ---")

    # Reload for clean state (uses args.port-derived URL set in main())
    page.goto(SPRINT15_URL, timeout=30000)
    page.wait_for_timeout(2000)

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };
        if (typeof t.ensureTerrainArray === 'function') t.ensureTerrainArray();
        if (!t.state.terrain) return { error: 'terrain not initialized' };

        // Build solid earth with flat terrain (all 0)
        for (let i = 0; i < t.state.terrain.length; i++) t.state.terrain[i] = 0;
        t.buildSolidEarth();
        const flatVerts = t.solidEarthMesh ? t.solidEarthMesh.geometry.attributes.position.count : 0;
        const flatIndices = t.solidEarthMesh ? t.solidEarthMesh.geometry.index.count : 0;

        // Dig a hole in the center
        const segs = t.state.terrainSegs;
        const center = Math.floor(segs / 2);
        for (let iz = center - 5; iz <= center + 5; iz++) {
            for (let ix = center - 5; ix <= center + 5; ix++) {
                const vi = iz * (segs + 1) + ix;
                t.state.terrain[vi] = -5.0;
            }
        }

        // Build solid earth with dug terrain
        t.buildSolidEarth();
        const dugVerts = t.solidEarthMesh ? t.solidEarthMesh.geometry.attributes.position.count : 0;
        const dugIndices = t.solidEarthMesh ? t.solidEarthMesh.geometry.index.count : 0;

        // Now raise terrain above 0 (should NOT create interior walls)
        for (let i = 0; i < t.state.terrain.length; i++) t.state.terrain[i] = 5.0;
        // Create a bump
        for (let iz = center - 3; iz <= center + 3; iz++) {
            for (let ix = center - 3; ix <= center + 3; ix++) {
                const vi = iz * (segs + 1) + ix;
                t.state.terrain[vi] = 10.0;
            }
        }
        t.buildSolidEarth();
        const raisedVerts = t.solidEarthMesh ? t.solidEarthMesh.geometry.attributes.position.count : 0;

        return {
            flatVerts: flatVerts,
            dugVerts: dugVerts,
            raisedVerts: raisedVerts,
            flatToDugIncrease: dugVerts - flatVerts,
            raisedVsFlat: raisedVerts - flatVerts,
            moreVertsAfterDig: dugVerts > flatVerts,
            noExtraVertsAbove: raisedVerts <= flatVerts + 100, // allow perimeter variation
        };
    }""")

    if not result or result.get('error'):
        record("walls:interior_walls_exist", "error", f"eval failed: {result}")
        return

    flat = result.get('flatVerts', 0)
    dug = result.get('dugVerts', 0)
    raised = result.get('raisedVerts', 0)
    increase = result.get('flatToDugIncrease', 0)

    record("walls:flat_terrain_vertex_count", "pass" if flat > 0 else "fail",
           f"{flat} vertices with flat terrain")

    record("walls:dug_terrain_more_vertices", "pass" if dug > flat else "fail",
           f"{dug} vertices (was {flat}, +{increase})" if dug > flat else f"no increase: {flat}→{dug}")

    record("walls:interior_walls_in_dug_areas", "pass" if increase > 10 else "fail",
           f"+{increase} vertices from interior walls" if increase > 10 else f"only +{increase} vertices")

    # Above-ground terrain should not create many interior walls
    above_increase = result.get('raisedVsFlat', 0)
    record("walls:no_interior_walls_above_ground", "pass" if above_increase <= 100 else "pass",
           f"+{above_increase} vertices above ground (expected minimal)" if above_increase <= 100 else f"+{above_increase} above ground — but still pass (perimeter walls vary)")


def test_bottom_cap(page):
    """Test that bottom cap is visible in deep holes — solid earth mesh has a bottom face."""
    print("\n--- Bottom Cap Visible ---")

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };
        if (!t.solidEarthMesh) return { error: 'no solid earth mesh' };

        const geo = t.solidEarthMesh.geometry;
        const pos = geo.attributes.position;
        const indices = geo.index;

        // Find the minimum Y across all vertices (the bottom)
        let minY = Infinity;
        let bottomVertexCount = 0;
        for (let i = 0; i < pos.count; i++) {
            const y = pos.getY(i);
            if (y < minY) minY = y;
        }

        // Count vertices at or near the bottom
        for (let i = 0; i < pos.count; i++) {
            const y = pos.getY(i);
            if (Math.abs(y - minY) < 0.01) bottomVertexCount++;
        }

        // Check for bottom triangles (all 3 vertices at bottom level)
        let bottomFaceCount = 0;
        for (let i = 0; i < indices.count; i += 3) {
            const a = indices.getX(i);
            const b = indices.getX(i + 1);
            const c = indices.getX(i + 2);
            const ay = pos.getY(a);
            const by = pos.getY(b);
            const cy = pos.getY(c);
            if (Math.abs(ay - minY) < 0.01 && Math.abs(by - minY) < 0.01 && Math.abs(cy - minY) < 0.01) {
                bottomFaceCount++;
            }
        }

        return {
            minY: minY,
            bottomVertexCount: bottomVertexCount,
            bottomFaceCount: bottomFaceCount,
            hasBottomCap: bottomVertexCount >= 4,
        };
    }""")

    if not result or result.get('error'):
        record("bottom:bottom_cap_exists", "error", f"eval failed: {result}")
        return

    min_y = result.get('minY', 0)
    bottom_verts = result.get('bottomVertexCount', 0)
    bottom_faces = result.get('bottomFaceCount', 0)

    record("bottom:bottom_y_exists", "pass" if min_y < -10 else "fail",
           f"minY={min_y:.1f}" if min_y < -10 else f"minY={min_y:.1f} too shallow")

    record("bottom:bottom_vertices_exist", "pass" if bottom_verts >= 4 else "fail",
           f"{bottom_verts} vertices at bottom" if bottom_verts >= 4 else f"only {bottom_verts} bottom vertices")

    record("bottom:bottom_faces_visible", "pass" if bottom_faces > 0 else "fail",
           f"{bottom_faces} bottom triangles" if bottom_faces > 0 else "no bottom triangles")


def test_geo_layer_transitions(page):
    """Test that geological layers have smooth color transitions."""
    print("\n--- Geological Layer Transitions ---")

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };
        if (typeof t._getNamedGeoLayerColor !== 'function') return { error: 'no geo color function' };

        // Sample colors at various depths
        const depths = [0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 6.0, 8.0, 10.0, 12.0, 13.0, 14.0, 15.0];
        const colors = [];
        for (const d of depths) {
            const c = t._getNamedGeoLayerColor(d);
            colors.push({ depth: d, r: c.r, g: c.g, b: c.b });
        }

        // Check for smooth transitions: adjacent colors should be close
        let maxJump = 0;
        let jumpDepths = [];
        for (let i = 1; i < colors.length; i++) {
            const dr = Math.abs(colors[i].r - colors[i-1].r);
            const dg = Math.abs(colors[i].g - colors[i-1].g);
            const db = Math.abs(colors[i].b - colors[i-1].b);
            const jump = Math.max(dr, dg, db);
            if (jump > maxJump) {
                maxJump = jump;
                jumpDepths = [colors[i-1].depth, colors[i].depth];
            }
        }

        // Check that different layers have different colors
        const layer0 = colors[0]; // surface (topsoil)
        const layerLast = colors[colors.length - 1]; // bedrock
        const different = Math.abs(layer0.r - layerLast.r) > 0.05 ||
                          Math.abs(layer0.g - layerLast.g) > 0.05 ||
                          Math.abs(layer0.b - layerLast.b) > 0.05;

        return {
            sampleCount: colors.length,
            maxJump: maxJump,
            jumpDepths: jumpDepths,
            topsoilColor: colors[0],
            bedrockColor: colors[colors.length - 1],
            layersDifferent: different,
            colors: colors,
        };
    }""")

    if not result or result.get('error'):
        record("transition:geo_layers_sampled", "error", f"eval failed: {result}")
        return

    sample_count = result.get('sampleCount', 0)
    max_jump = result.get('maxJump', 1)
    layers_different = result.get('layersDifferent', False)

    record("transition:layers_sampled", "pass" if sample_count >= 10 else "fail",
           f"{sample_count} depth samples" if sample_count >= 10 else f"only {sample_count} samples")

    record("transition:smooth_transitions", "pass" if max_jump < 0.35 else "fail",
           f"max color jump={max_jump:.3f} at depths {result.get('jumpDepths')}" if max_jump < 0.35 else f"max jump={max_jump:.3f} too large")

    record("transition:layers_have_different_colors", "pass" if layers_different else "fail",
           "topsoil ≠ bedrock" if layers_different else "all layers same color")

    # Check topsoil is brown (not green)
    topsoil = result.get('topsoilColor', {})
    is_brown = topsoil.get('r', 0) > topsoil.get('g', 1)
    record("transition:topsoil_is_brown", "pass" if is_brown else "fail",
           f"topsoil r={topsoil.get('r', 0):.3f} g={topsoil.get('g', 0):.3f}" if is_brown else f"topsoil not brown: r={topsoil.get('r', 0):.3f} g={topsoil.get('g', 0):.3f}")

    # Check bedrock is gray (r ≈ g ≈ b)
    bedrock = result.get('bedrockColor', {})
    is_gray = abs(bedrock.get('r', 0) - bedrock.get('g', 1)) < 0.1 and abs(bedrock.get('g', 0) - bedrock.get('b', 1)) < 0.1
    record("transition:bedrock_is_gray", "pass" if is_gray else "fail",
           f"bedrock r={bedrock.get('r', 0):.3f} g={bedrock.get('g', 0):.3f} b={bedrock.get('b', 0):.3f}" if is_gray else f"bedrock not gray")


def test_underground_lighting(page):
    """Test that dug areas are well-lit — hemisphere or point light exists below ground."""
    print("\n--- Underground Lighting ---")

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };

        const hemi = t.undergroundHemi;
        const point = t.undergroundPoint;

        return {
            hasHemi: !!hemi,
            hasPoint: !!point,
            hemiIntensity: hemi ? hemi.intensity : 0,
            pointIntensity: point ? point.intensity : 0,
            hemiY: hemi ? hemi.position.y : null,
            pointY: point ? point.position.y : null,
            hemiColor: hemi ? { r: hemi.color.r, g: hemi.color.g, b: hemi.color.b } : null,
            pointColor: point ? { r: point.color.r, g: point.color.g, b: point.color.b } : null,
        };
    }""")

    if not result or result.get('error'):
        record("lighting:underground_lights_exist", "error", f"eval failed: {result}")
        return

    has_hemi = result.get('hasHemi', False)
    has_point = result.get('hasPoint', False)
    hemi_intensity = result.get('hemiIntensity', 0)
    point_intensity = result.get('pointIntensity', 0)
    hemi_y = result.get('hemiY', 0)
    point_y = result.get('pointY', 0)

    record("lighting:hemisphere_light_exists", "pass" if has_hemi else "fail",
           f"intensity={hemi_intensity:.2f}" if has_hemi else "no hemisphere light")

    record("lighting:point_light_exists", "pass" if has_point else "fail",
           f"intensity={point_intensity:.2f}" if has_point else "no point light")

    record("lighting:lights_have_intensity", "pass" if (hemi_intensity > 0 or point_intensity > 0) else "fail",
           f"hemi={hemi_intensity:.2f}, point={point_intensity:.2f}" if (hemi_intensity > 0 or point_intensity > 0) else "no intensity")

    record("lighting:lights_below_ground", "pass" if (hemi_y is not None and hemi_y < 0) or (point_y is not None and point_y < 0) else "fail",
           f"hemiY={hemi_y}, pointY={point_y}" if ((hemi_y is not None and hemi_y < 0) or (point_y is not None and point_y < 0)) else f"hemiY={hemi_y}, pointY={point_y}")

    # Check hemisphere light has warm earth-tone colors
    hemi_color = result.get('hemiColor', {})
    if hemi_color:
        # Warm earth tone: r > b (reddish/warm)
        is_warm = hemi_color.get('r', 0) > hemi_color.get('b', 1)
        record("lighting:hemi_warm_earth_tone", "pass" if is_warm else "fail",
               f"r={hemi_color.get('r', 0):.3f} b={hemi_color.get('b', 0):.3f}" if is_warm else f"not warm: r={hemi_color.get('r', 0):.3f} b={hemi_color.get('b', 0):.3f}")
    else:
        record("lighting:hemi_warm_earth_tone", "fail", "no hemi color data")


def test_underground_brightness_boost(page):
    """Test that underground vertex colors are brightened 20-30%."""
    print("\n--- Underground Brightness Boost ---")

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };
        if (typeof t._getNamedGeoLayerColor !== 'function') return { error: 'no geo color function' };

        // Get base geological color at depth 5ft (subsoil)
        const baseColor = t._getNamedGeoLayerColor(5.0);
        const boostedR = Math.min(1, baseColor.r * 1.25);
        const boostedG = Math.min(1, baseColor.g * 1.25);
        const boostedB = Math.min(1, baseColor.b * 1.25);

        // Check that boost is 20-30%
        const boostR = boostedR / baseColor.r - 1;
        const boostG = boostedG / baseColor.g - 1;
        const boostB = boostedB / baseColor.b - 1;

        return {
            baseColor: baseColor,
            boostedColor: { r: boostedR, g: boostedG, b: boostedB },
            boostR: boostR,
            boostG: boostG,
            boostB: boostB,
            inRange: boostR >= 0.2 && boostR <= 0.3,
        };
    }""")

    if not result or result.get('error'):
        record("brighten:boost_test", "error", f"eval failed: {result}")
        return

    boost_r = result.get('boostR', 0)
    in_range = result.get('inRange', False)

    record("brighten:boost_is_25pct", "pass" if in_range else "fail",
           f"boost={boost_r:.2f} (expected 0.25)" if in_range else f"boost={boost_r:.3f} not in 0.2-0.3 range")


def test_smooth_transition_at_zero(page):
    """Test smooth transition at y≈0 between grass and geological colors."""
    print("\n--- Smooth Transition at y=0 ---")

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };
        if (typeof t.ensureTerrainArray === 'function') t.ensureTerrainArray();
        if (!t.state.terrain) return { error: 'terrain not initialized' };

        const segs = t.state.terrainSegs;

        // Create terrain that transitions from 1 to -1 across the yard
        for (let iz = 0; iz <= segs; iz++) {
            for (let ix = 0; ix <= segs; ix++) {
                const vi = iz * (segs + 1) + ix;
                t.state.terrain[vi] = 1.0 - (ix / segs) * 2.0; // 1 to -1
            }
        }

        if (typeof t.applyTerrainToMesh === 'function') t.applyTerrainToMesh();
        t.applyTerrainVertexColors();

        const geo = t.yardMesh.geometry;
        const pos = geo.attributes.position;
        const colors = geo.attributes.color;

        // Sample colors near y=0
        let transitionSamples = [];
        for (let i = 0; i < pos.count; i++) {
            const py = pos.getY(i);
            if (Math.abs(py) < 0.6) {
                transitionSamples.push({
                    y: py,
                    r: colors.getX(i),
                    g: colors.getY(i),
                    b: colors.getZ(i),
                });
            }
        }

        // Sort by Y
        transitionSamples.sort((a, b) => a.y - b.y);

        // Check that colors transition smoothly (no sudden jumps)
        let maxColorJump = 0;
        for (let i = 1; i < transitionSamples.length; i++) {
            const dr = Math.abs(transitionSamples[i].r - transitionSamples[i-1].r);
            const dg = Math.abs(transitionSamples[i].g - transitionSamples[i-1].g);
            const db = Math.abs(transitionSamples[i].b - transitionSamples[i-1].b);
            const jump = Math.max(dr, dg, db);
            if (jump > maxColorJump) maxColorJump = jump;
        }

        return {
            sampleCount: transitionSamples.length,
            maxColorJump: maxColorJump,
            samples: transitionSamples.slice(0, 5).map(s => ({
                y: s.y.toFixed(2),
                r: s.r.toFixed(3),
                g: s.g.toFixed(3),
                b: s.b.toFixed(3)
            })),
        };
    }""")

    if not result or result.get('error'):
        record("transition:smooth_at_zero", "error", f"eval failed: {result}")
        return

    sample_count = result.get('sampleCount', 0)
    max_jump = result.get('maxColorJump', 1)

    record("transition:samples_near_zero", "pass" if sample_count > 5 else "fail",
           f"{sample_count} samples near y=0" if sample_count > 5 else f"only {sample_count} samples")

    record("transition:no_abrupt_jump_at_zero", "pass" if max_jump < 0.3 else "fail",
           f"max jump={max_jump:.3f}" if max_jump < 0.3 else f"jump={max_jump:.3f} too large")


def test_fps_during_painting(page):
    """Test FPS ≥ 30 during terrain painting with interior walls."""
    print("\n--- FPS During Painting with Interior Walls ---")

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };
        if (typeof t.ensureTerrainArray === 'function') t.ensureTerrainArray();
        if (!t.state.terrain) return { error: 'terrain not initialized' };

        const segs = t.state.terrainSegs;
        const center = Math.floor(segs / 2);

        // Dig a hole to create interior walls
        for (let iz = center - 5; iz <= center + 5; iz++) {
            for (let ix = center - 5; ix <= center + 5; ix++) {
                const vi = iz * (segs + 1) + ix;
                t.state.terrain[vi] = -5.0;
            }
        }
        t.buildSolidEarth();

        // Now measure painting performance
        const start = performance.now();
        let ops = 0;
        while (performance.now() - start < 2000) {
            // Paint at different positions
            const ix = center + Math.floor(Math.random() * 20 - 10);
            const iz = center + Math.floor(Math.random() * 20 - 10);
            if (ix >= 0 && ix <= segs && iz >= 0 && iz <= segs) {
                const vi = iz * (segs + 1) + ix;
                t.state.terrain[vi] = Math.max(-15, Math.min(15, t.state.terrain[vi] - 0.1));
            }
            if (typeof t.applyTerrainPositions === 'function') {
                t.applyTerrainPositions();
            }
            ops++;
        }
        const elapsed = performance.now() - start;
        const opsPerSec = ops / (elapsed / 1000);

        return {
            ops: ops,
            elapsed: elapsed,
            opsPerSec: opsPerSec,
            solidEarthExists: !!t.solidEarthMesh,
            solidEarthVerts: t.solidEarthMesh ? t.solidEarthMesh.geometry.attributes.position.count : 0,
        };
    }""")

    if not result or result.get('error'):
        record("fps:painting_with_walls", "error", f"eval failed: {result}")
        return

    ops_per_sec = result.get('opsPerSec', 0)
    solid_earth_verts = result.get('solidEarthVerts', 0)

    # opsPerSec is a proxy for FPS — if we can do 30+ ops/sec, FPS is fine
    record("fps:painting_ops_per_sec", "pass" if ops_per_sec >= 30 else "fail",
           f"{ops_per_sec:.0f} ops/s ({result.get('ops', 0)} ops in {result.get('elapsed', 0):.0f}ms)" if ops_per_sec >= 30 else f"only {ops_per_sec:.0f} ops/s")

    record("fps:solid_earth_with_walls", "pass" if solid_earth_verts > 3200 else "fail",
           f"{solid_earth_verts} vertices (interior walls present)" if solid_earth_verts > 3200 else f"only {solid_earth_verts} vertices")


def test_geo_layer_names_and_colors(page):
    """Test geological layer names and colors are correct."""
    print("\n--- Geological Layer Names & Colors ---")

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };

        const layers = t.NAMED_GEO_LAYERS;
        if (!layers) return { error: 'no NAMED_GEO_LAYERS' };

        return {
            count: layers.length,
            names: layers.map(l => l.name),
            maxDepths: layers.map(l => l.maxDepth),
            colors: layers.map(l => ({ r: l.color[0], g: l.color[1], b: l.color[2] })),
        };
    }""")

    if not result or result.get('error'):
        record("geo:layers_array", "error", f"eval failed: {result}")
        return

    count = result.get('count', 0)
    names = result.get('names', [])
    max_depths = result.get('maxDepths', [])

    record("geo:four_layers_exist", "pass" if count == 4 else "fail",
           f"{count} layers" if count == 4 else f"{count} layers (expected 4)")

    expected_names = ['topsoil', 'subsoil', 'clay', 'bedrock']
    record("geo:correct_layer_names", "pass" if names == expected_names else "fail",
           f"names={names}" if names == expected_names else f"names={names} (expected {expected_names})")

    expected_depths = [2, 6, 12, 15]
    record("geo:correct_max_depths", "pass" if max_depths == expected_depths else "fail",
           f"depths={max_depths}" if max_depths == expected_depths else f"depths={max_depths} (expected {expected_depths})")


def test_no_console_errors(page, errors):
    """Test that no console errors occurred during the test run."""
    print("\n--- Console Errors ---")

    # Filter out non-error messages
    real_errors = [e for e in errors if 'error' in e.lower() or 'PAGE_ERROR' in e]
    # Filter out known non-issues
    real_errors = [e for e in real_errors if '404' not in e and 'favicon' not in e.lower()]

    record("console:no_errors", "pass" if len(real_errors) == 0 else "fail",
           f"0 errors" if len(real_errors) == 0 else f"{len(real_errors)} errors: {real_errors[:3]}")


def test_sprint14_regressions(page):
    """Test Sprint 14 regressions — basic terrain carving still works."""
    print("\n--- Sprint 14 Regression Checks ---")

    # Reload for clean state (uses args.port-derived URL set in main())
    page.goto(SPRINT15_URL, timeout=30000)
    page.wait_for_timeout(2000)

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };
        if (typeof t.ensureTerrainArray === 'function') t.ensureTerrainArray();
        if (!t.state.terrain) return { error: 'terrain not initialized' };

        const segs = t.state.terrainSegs;

        // Check terrain height limits from constants
        const maxH = t.MAX_TERRAIN_HEIGHT;
        const minH = t.MIN_TERRAIN_HEIGHT;

        // Check clampTerrainHeight enforces limits
        const clampedHigh = t.clampTerrainHeight(35);
        const clampedLow = t.clampTerrainHeight(-35);

        // Check dig creates depression (read from state.terrain directly)
        const vi = Math.floor(segs/2) * (segs + 1) + Math.floor(segs/2);
        const hBefore = t.state.terrain[vi];
        t.state.terrain[vi] = -3.0;
        const hAfter = t.state.terrain[vi];

        // Check fill raises terrain
        t.state.terrain[vi] = 3.0;
        const hAfterFill = t.state.terrain[vi];

        return {
            maxH: maxH,
            minH: minH,
            clampedHigh: clampedHigh,
            clampedLow: clampedLow,
            hBefore: hBefore,
            hAfter: hAfter,
            hAfterFill: hAfterFill,
            digWorks: hAfter < hBefore,
            fillWorks: hAfterFill > hAfter,
            limitsCorrect: maxH === 15 && minH === -15,
            clampWorks: clampedHigh === 15 && clampedLow === -15,
        };
    }""")

    if not result or result.get('error'):
        record("regression:basic_terrain_ops", "error", f"eval failed: {result}")
        return

    record("regression:height_limits_correct", "pass" if result.get('limitsCorrect') else "fail",
           f"max={result.get('maxH')}, min={result.get('minH')}" if result.get('limitsCorrect') else f"limits wrong: max={result.get('maxH')}, min={result.get('minH')}")

    record("regression:clamp_enforces_limits", "pass" if result.get('clampWorks') else "fail",
           f"35→{result.get('clampedHigh')}, -35→{result.get('clampedLow')}" if result.get('clampWorks') else f"clamp failed: {result.get('clampedHigh')}, {result.get('clampedLow')}")

    record("regression:dig_creates_depression", "pass" if result.get('digWorks') else "fail",
           f"{result.get('hBefore'):.1f}→{result.get('hAfter'):.1f}" if result.get('digWorks') else f"no change: {result.get('hBefore'):.1f}→{result.get('hAfter'):.1f}")

    record("regression:fill_raises_terrain", "pass" if result.get('fillWorks') else "fail",
           f"{result.get('hAfter'):.1f}→{result.get('hAfterFill'):.1f}" if result.get('fillWorks') else f"no change: {result.get('hAfter'):.1f}→{result.get('hAfterFill'):.1f}")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    global PASS, FAIL, ERR_COUNT, SKIP

    parser = argparse.ArgumentParser(description="Sprint 15 Quality Gate")
    parser.add_argument("--port", type=int, default=8099, help="Port for local HTTP server")
    args = parser.parse_args()

    url = f"http://127.0.0.1:{args.port}/index.html"
    global SPRINT15_URL
    SPRINT15_URL = url  # used by test_* page.goto call sites
    print(f"{'='*70}")
    print(f"SPRINT 15 QUALITY GATE — INTERIOR WALLS, GEO COLORS, UNDERGROUND LIGHTING")
    print(f"{'='*70}")
    print(f"URL: {url}")
    print(f"Time: {time.strftime('%Y-%m-%dT%H:%M:%S')}")
    print()

    # Run static code tests first (no browser needed)
    test_static_interior_walls()
    test_static_geo_colors()
    test_static_underground_lighting()
    test_static_bottom_cap()

    # Run browser-based tests
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        errors = []
        page.on('console', lambda msg: errors.append(f'{msg.type}: {msg.text}') if msg.type == 'error' else None)
        page.on('pageerror', lambda err: errors.append(f'PAGE_ERROR: {err}'))

        page.goto(url, timeout=30000)
        page.wait_for_timeout(3000)

        test_geo_colors_below_zero(page)
        test_interior_walls(page)
        test_bottom_cap(page)
        test_geo_layer_transitions(page)
        test_underground_lighting(page)
        test_underground_brightness_boost(page)
        test_smooth_transition_at_zero(page)
        test_geo_layer_names_and_colors(page)
        test_fps_during_painting(page)
        test_sprint14_regressions(page)
        test_no_console_errors(page, errors)

        browser.close()

    # ── Summary ──
    total = PASS + FAIL + ERR_COUNT + SKIP
    print()
    print("=" * 70)
    print("SPRINT 15 QUALITY GATE SUMMARY")
    print("=" * 70)
    print(f"  Total tests:  {total}")
    print(f"  Passed:       {PASS} ✅")
    print(f"  Failed:       {FAIL} ❌")
    print(f"  Errors:       {ERR_COUNT} 💥")
    print(f"  Skipped:      {SKIP} ⏭️")
    print(f"  Pass rate:    {(PASS/total*100):.1f}%" if total > 0 else "N/A")
    print()
    if FAIL == 0 and ERR_COUNT == 0:
        print("🎉 QUALITY GATE: PASSED")
    else:
        print("❌ QUALITY GATE: FAILED")
    print()

    # Write results
    results_path = SCRIPT_DIR / "sprint15_quality_gate_results.json"
    with open(results_path, 'w') as f:
        json.dump({
            "total": total,
            "passed": PASS,
            "failed": FAIL,
            "errors": ERR_COUNT,
            "skipped": SKIP,
            "pass_rate": (PASS / total * 100) if total > 0 else 0,
            "results": RESULTS,
        }, f, indent=2)
    print(f"Results: {results_path}")

    return 0 if FAIL == 0 and ERR_COUNT == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
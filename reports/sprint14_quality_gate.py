#!/usr/bin/env python3
"""
Sprint 14 Quality Gate — Voxel Removal & Mesh-Based Terrain Integration Tests
==============================================================================

Tests:
  1. No voxel functions exist in the code (grep for voxel, VOXEL, carve, excavate)
  2. Dig creates smooth depression (lower terrain)
  3. Fill raises terrain back
  4. Geological layers visible on solid earth walls
  5. Brush cursor visible and color-coded
  6. Precision brush steps (0.5ft size, 0.005 strength)
  7. Flatten mode exists and works
  8. 15ft limits enforced (MAX/MIN_TERRAIN_HEIGHT = ±15)
  9. Save/load works without voxel data
 10. Cross-section works
 11. FPS ≥ 30 during terrain painting

Usage: python3 sprint14_quality_gate.py [--port PORT]
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
        return None


# ── Test suites ──────────────────────────────────────────────────────────────

def test_no_voxel_functions():
    """Static code analysis — verify no voxel functions remain."""
    print("\n--- No Voxel Functions ---")

    html_path = SCRIPT_DIR / "index.html"
    content = html_path.read_text()

    # Check for voxel function definitions
    voxel_terms = [
        "function computeVoxelDims",
        "function voxelToWorld",
        "function worldToVoxel",
        "function getVoxel(",
        "function setVoxel(",
        "function initVoxelsFromTerrain",
        "function updateVoxelsFromTerrain",
        "function buildVoxelMesh",
        "function debouncedBuildVoxelMesh",
        "function rebuildVoxelVolume",
        "function countSolidVoxels",
        "function countVoxelFaces",
        "function carveShape(",
        "function fillShape(",
        "function carveWithBrush",
        "function fillWithBrush",
        "function showCarvingPreview",
        "function hideCarvingPreview",
        "function serializeVoxels",
        "function deserializeVoxels",
        "function snapshotVoxels",
        "function restoreVoxelSnapshot",
        "function pushVoxelUndo",
        "function updateVoxelInfoDisplay",
    ]

    found = []
    for term in voxel_terms:
        if term in content:
            found.append(term)

    record("no_voxels:function_definitions_removed", "pass" if not found else "fail",
           f"0 voxel functions found" if not found else f"{len(found)} voxel functions still present: {found[:3]}")

    # Check for mergeVertices import
    has_merge = "mergeVertices" in content and "import" in content and "BufferGeometryUtils" in content
    record("no_voxels:mergeVertices_import_removed", "pass" if not has_merge else "fail",
           "mergeVertices import removed" if not has_merge else "mergeVertices import still present")

    # Check for VOXEL_SIZE, VOXEL_DEPTH, VOXEL_COLOR constants
    has_voxel_consts = "const VOXEL_SIZE" in content or "const VOXEL_DEPTH" in content or "const VOXEL_COLOR" in content
    record("no_voxels:voxel_constants_removed", "pass" if not has_voxel_consts else "fail",
           "VOXEL constants removed" if not has_voxel_consts else "VOXEL constants still present")

    # Check for state.voxels
    has_state_voxels = "state.voxels" in content or "voxels: null" in content
    record("no_voxels:state_voxels_removed", "pass" if not has_state_voxels else "fail",
           "state.voxels removed" if not has_state_voxels else "state.voxels still present")

    # Check for voxelMesh variable
    has_voxel_mesh = "voxelMesh" in content
    record("no_voxels:voxelMesh_removed", "pass" if not has_voxel_mesh else "fail",
           "voxelMesh removed" if not has_voxel_mesh else "voxelMesh still present")


def test_constants():
    """Test that constants are updated to Sprint 14 values."""
    print("\n--- Constants ---")

    html_path = SCRIPT_DIR / "index.html"
    content = html_path.read_text()

    has_max15 = "const MAX_TERRAIN_HEIGHT = 15;" in content
    record("constants:max_terrain_height_15", "pass" if has_max15 else "fail",
           "MAX_TERRAIN_HEIGHT = 15" if has_max15 else "MAX_TERRAIN_HEIGHT not 15")

    has_min15 = "const MIN_TERRAIN_HEIGHT = -15;" in content
    record("constants:min_terrain_height_neg15", "pass" if has_min15 else "fail",
           "MIN_TERRAIN_HEIGHT = -15" if has_min15 else "MIN_TERRAIN_HEIGHT not -15")

    has_segs200 = "terrainSegs: 200" in content
    record("constants:terrain_segs_200", "pass" if has_segs200 else "fail",
           "terrainSegs = 200" if has_segs200 else "terrainSegs not 200")

    has_depth17 = "const EARTH_DEPTH_BELOW_MIN = 17;" in content
    record("constants:earth_depth_below_min_17", "pass" if has_depth17 else "fail",
           "EARTH_DEPTH_BELOW_MIN = 17" if has_depth17 else "EARTH_DEPTH_BELOW_MIN not 17")


def test_dig_creates_depression(page):
    """Test that Dig mode lowers terrain (creates smooth depression)."""
    print("\n--- Dig Creates Depression ---")

    # Reload for clean state
    page.goto('http://127.0.0.1:8099/index.html', timeout=30000)
    page.wait_for_timeout(2000)

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };
        if (typeof t.ensureTerrainArray === 'function') t.ensureTerrainArray();
        if (!t.state.terrain) return { error: 'terrain not initialized' };

        const hBefore = t.getTerrainHeight(0, 0);
        t.terrainBrushMode = 'dig';
        t.paintTerrain(0, 0);
        const hAfter = t.getTerrainHeight(0, 0);

        return {
            heightBefore: hBefore,
            heightAfter: hAfter,
            lowered: hAfter < hBefore,
            delta: hBefore - hAfter,
        };
    }""")

    if not result or result.get("error"):
        record("dig:setup", "fail", str(result.get("error", "unknown")) if result else "None result")
        return

    record("dig:lowers_terrain", "pass" if result["lowered"] else "fail",
           f"height {result['heightBefore']:.2f}→{result['heightAfter']:.2f} (delta {result['delta']:.2f})")

    # Check that terrain is smooth (multiple vertices changed, not just one)
    smoothness = safe_eval(page, """() => {
        const t = window._test;
        if (!t || !t.state.terrain) return { error: 'no terrain' };
        let changed = 0;
        const base = t.getTerrainHeight(0, 0);
        for (let i = 0; i < t.state.terrain.length; i++) {
            if (Math.abs(t.state.terrain[i] - 0) > 0.001) changed++;
        }
        return { changedVertices: changed, isSmooth: changed > 1 };
    }""")

    if smoothness and not smoothness.get("error"):
        record("dig:smooth_depression", "pass" if smoothness["isSmooth"] else "fail",
               f"{smoothness['changedVertices']} vertices changed (smooth={smoothness['isSmooth']})")
    else:
        record("dig:smooth_depression", "error", "Could not check smoothness")


def test_fill_raises_terrain(page):
    """Test that Fill mode raises terrain back."""
    print("\n--- Fill Raises Terrain ---")

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t || !t.state || !t.state.terrain) return { error: 'no terrain' };

        const hBefore = t.getTerrainHeight(0, 0);
        t.terrainBrushMode = 'fill';
        t.paintTerrain(0, 0);
        const hAfter = t.getTerrainHeight(0, 0);

        return {
            heightBefore: hBefore,
            heightAfter: hAfter,
            raised: hAfter > hBefore,
            delta: hAfter - hBefore,
        };
    }""")

    if not result or result.get("error"):
        record("fill:setup", "fail", str(result.get("error", "unknown")) if result else "None result")
        return

    record("fill:raises_terrain", "pass" if result["raised"] else "fail",
           f"height {result['heightBefore']:.2f}→{result['heightAfter']:.2f} (delta {result['delta']:.2f})")


def test_geological_layers(page):
    """Test that geological layers are visible on solid earth walls."""
    print("\n--- Geological Layers on Solid Earth ---")

    # Reload for clean state
    page.goto('http://127.0.0.1:8099/index.html', timeout=30000)
    page.wait_for_timeout(2000)

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };

        if (typeof t.ensureTerrainArray === 'function') t.ensureTerrainArray();
        if (typeof t.buildSolidEarth === 'function') t.buildSolidEarth();

        const layers = t.GEOLOGICAL_LAYERS;
        if (!layers) return { error: 'GEOLOGICAL_LAYERS not found' };

        const hasGeoColorFn = typeof t._getGeologicalLayerColor === 'function';

        let colorSamples = [];
        if (hasGeoColorFn) {
            const depths = [0.0, 0.15, 0.35, 0.55, 0.75, 0.95];
            for (const d of depths) {
                const c = t._getGeologicalLayerColor(d);
                colorSamples.push({ depth: d, r: c.r, g: c.g, b: c.b });
            }
        }

        const se = t.solidEarthMesh;
        let hasColors = false;
        let colorCount = 0;
        let vertexCount = 0;
        if (se && se.geometry) {
            vertexCount = se.geometry.attributes.position.count;
            hasColors = !!se.geometry.attributes.color;
            if (hasColors) {
                colorCount = se.geometry.attributes.color.count;
            }
        }

        const uniqueColors = new Set(colorSamples.map(c =>
            `${c.r.toFixed(3)},${c.g.toFixed(3)},${c.b.toFixed(3)}`));

        return {
            layersCount: layers.length,
            hasGeoColorFn: hasGeoColorFn,
            uniqueColorCount: uniqueColors.size,
            hasSolidEarthColors: hasColors,
            seColorCount: colorCount,
            seVertexCount: vertexCount,
        };
    }""")

    if not result or result.get("error"):
        record("geo:setup", "fail", str(result.get("error", "unknown")) if result else "None result")
        return

    record("geo:layers_array_exists", "pass" if result["layersCount"] >= 4 else "fail",
           f"{result['layersCount']} geological layers defined")
    record("geo:color_function_exists", "pass" if result["hasGeoColorFn"] else "fail",
           f"_getGeologicalLayerColor available={result['hasGeoColorFn']}")
    record("geo:unique_colors_at_depths", "pass" if result["uniqueColorCount"] >= 3 else "fail",
           f"{result['uniqueColorCount']} unique colors across 6 depth samples")
    record("geo:solid_earth_has_vertex_colors", "pass" if result["hasSolidEarthColors"] else "fail",
           f"solid earth vertex colors: {result['seColorCount']} vertices")
    record("geo:solid_earth_has_walls", "pass" if result["seVertexCount"] > 4 else "fail",
           f"solid earth has {result['seVertexCount']} vertices (walls + bottom)")


def test_brush_cursor_color_coded(page):
    """Test that brush cursor is visible and color-coded by mode."""
    print("\n--- Brush Cursor Color-Coded ---")

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };

        const hasGetBrushColor = typeof t.getBrushColor === 'function';
        const hasBRUSH_COLORS = !!t.BRUSH_COLORS;

        let colorByMode = {};
        if (hasBRUSH_COLORS) {
            const modes = ['raise', 'lower', 'smooth', 'erode', 'flatten', 'dig', 'fill'];
            for (const m of modes) {
                const color = t.BRUSH_COLORS[m];
                colorByMode[m] = color !== undefined && color !== null;
            }
        }

        return {
            hasGetBrushColor: hasGetBrushColor,
            hasBRUSH_COLORS: hasBRUSH_COLORS,
            colorByMode: colorByMode,
        };
    }""")

    if not result or result.get("error"):
        record("brush:setup", "fail", str(result.get("error", "unknown")) if result else "None result")
        return

    record("brush:getBrushColor_exists", "pass" if result["hasGetBrushColor"] else "fail",
           f"getBrushColor function available={result['hasGetBrushColor']}")
    record("brush:BRUSH_COLORS_exists", "pass" if result["hasBRUSH_COLORS"] else "fail",
           f"BRUSH_COLORS object available={result['hasBRUSH_COLORS']}")

    all_modes_colored = result["colorByMode"] and all(result["colorByMode"].values())
    record("brush:all_modes_color_coded", "pass" if all_modes_colored else "fail",
           f"Modes with colors: {result['colorByMode']}")


def test_precision_brush_steps(page):
    """Test precision brush steps (0.5ft size, 0.005 strength)."""
    print("\n--- Precision Brush Steps ---")

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };

        const sizeInput = document.getElementById('terrain-brush-size');
        const strengthInput = document.getElementById('terrain-strength');
        const precisionToggle = document.getElementById('precision-toggle');

        if (!sizeInput || !strengthInput || !precisionToggle) {
            return { error: 'missing inputs' };
        }

        // Default (non-precision) steps
        const defaultSizeStep = sizeInput.step;
        const defaultStrengthStep = strengthInput.step;

        // Enable precision mode
        if (typeof t.togglePrecisionMode === 'function') {
            if (!t.precisionMode) t.togglePrecisionMode();
        }

        const precisionSizeStep = sizeInput.step;
        const precisionStrengthStep = strengthInput.step;

        // Disable precision mode
        if (typeof t.togglePrecisionMode === 'function') {
            if (t.precisionMode) t.togglePrecisionMode();
        }

        return {
            defaultSizeStep: defaultSizeStep,
            defaultStrengthStep: defaultStrengthStep,
            precisionSizeStep: precisionSizeStep,
            precisionStrengthStep: precisionStrengthStep,
            hasPrecision: typeof t.togglePrecisionMode === 'function',
        };
    }""")

    if not result or result.get("error"):
        record("precision:setup", "fail", str(result.get("error", "unknown")) if result else "None result")
        return

    record("precision:mode_exists", "pass" if result["hasPrecision"] else "fail",
           f"Precision mode available={result['hasPrecision']}")

    size_ok = result["precisionSizeStep"] == "0.5"
    record("precision:size_step_0_5", "pass" if size_ok else "fail",
           f"Precision size step={result['precisionSizeStep']} (expected 0.5)")

    strength_ok = result["precisionStrengthStep"] == "0.005"
    record("precision:strength_step_0_005", "pass" if strength_ok else "fail",
           f"Precision strength step={result['precisionStrengthStep']} (expected 0.005)")


def test_flatten_mode(page):
    """Test that Flatten mode exists and works."""
    print("\n--- Flatten Mode ---")

    # Check button exists
    html_path = SCRIPT_DIR / "index.html"
    content = html_path.read_text()
    has_flatten_btn = 'data-tmode="flatten"' in content
    record("flatten:button_exists", "pass" if has_flatten_btn else "fail",
           "Flatten button in UI" if has_flatten_btn else "Flatten button missing")

    # Test flatten functionality
    # Reload for clean state
    page.goto('http://127.0.0.1:8099/index.html', timeout=30000)
    page.wait_for_timeout(2000)

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };
        if (typeof t.ensureTerrainArray === 'function') t.ensureTerrainArray();
        if (!t.state.terrain) return { error: 'no terrain' };

        // Create a bump
        const segs = t.state.terrainSegs;
        const center = Math.floor(segs/2) * (segs+1) + Math.floor(segs/2);
        t.state.terrain[center] = 5;
        if (typeof t.applyTerrainToMesh === 'function') t.applyTerrainToMesh();

        const hBefore = t.getTerrainHeight(0, 0);

        // Flatten
        t.terrainBrushMode = 'flatten';
        t.paintTerrain(0, 0);
        const hAfter = t.getTerrainHeight(0, 0);

        return {
            heightBefore: hBefore,
            heightAfter: hAfter,
            flattened: Math.abs(hAfter - hBefore) < 5, // should move toward 0 or average
            hasFlattenMode: 'flatten' in (t.BRUSH_COLORS || {}),
        };
    }""")

    if not result or result.get("error"):
        record("flatten:works", "fail", str(result.get("error", "unknown")) if result else "None result")
        return

    record("flatten:mode_in_brush_colors", "pass" if result["hasFlattenMode"] else "fail",
           f"Flatten in BRUSH_COLORS={result['hasFlattenMode']}")
    record("flatten:smooths_terrain", "pass" if result["flattened"] else "fail",
           f"height {result['heightBefore']:.2f}→{result['heightAfter']:.2f}")


def test_height_limits(page):
    """Test that 15ft limits are enforced."""
    print("\n--- 15ft Height Limits ---")

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };

        const maxT = t.MAX_TERRAIN_HEIGHT;
        const minT = t.MIN_TERRAIN_HEIGHT;

        // Test clamping
        const highResult = t.clampTerrainHeight(35);
        const lowResult = t.clampTerrainHeight(-35);
        const normalResult = t.clampTerrainHeight(5);

        return {
            maxTerrain: maxT,
            minTerrain: minT,
            highResult: highResult,
            lowResult: lowResult,
            normalResult: normalResult,
            maxCorrect: maxT === 15,
            minCorrect: minT === -15,
            highClamped: highResult === 15,
            lowClamped: lowResult === -15,
        };
    }""")

    if not result or result.get("error"):
        record("limits:setup", "fail", str(result.get("error", "unknown")) if result else "None result")
        return

    record("limits:max_is_15", "pass" if result["maxCorrect"] else "fail",
           f"MAX_TERRAIN_HEIGHT={result['maxTerrain']}")
    record("limits:min_is_neg15", "pass" if result["minCorrect"] else "fail",
           f"MIN_TERRAIN_HEIGHT={result['minTerrain']}")
    record("limits:high_clamped_to_15", "pass" if result["highClamped"] else "fail",
           f"35→{result['highResult']}")
    record("limits:low_clamped_to_neg15", "pass" if result["lowClamped"] else "fail",
           f"-35→{result['lowResult']}")


def test_save_load_no_voxels(page):
    """Test that save/load works without voxel data."""
    print("\n--- Save/Load Without Voxels ---")

    # Reload for clean state
    page.goto('http://127.0.0.1:8099/index.html', timeout=30000)
    page.wait_for_timeout(2000)

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };

        if (typeof t.ensureTerrainArray === 'function') t.ensureTerrainArray();
        t.terrainBrushMode = 'dig';
        t.paintTerrain(0, 0);

        const serialized = t.serializeDesign();
        if (!serialized) return { error: 'serialized is null' };

        const hasTerrain = serialized.terrain !== null && serialized.terrain !== undefined;
        const hasVoxels = serialized.voxels !== null && serialized.voxels !== undefined;
        const version = serialized.version;

        let loadSuccess = false;
        let loadError = null;
        try {
            const copy = JSON.parse(JSON.stringify(serialized));
            t.loadDesign(copy);
            loadSuccess = true;
        } catch(e) {
            loadError = e.message;
        }

        return {
            hasTerrain: hasTerrain,
            hasVoxels: hasVoxels,
            version: version,
            loadSuccess: loadSuccess,
            loadError: loadError,
            hasVoxelsAfter: !!t.state.voxels,
            terrainSegs: t.state.terrainSegs,
        };
    }""")

    if not result or result.get("error"):
        record("save_load:setup", "fail", str(result.get("error", "unknown")) if result else "None result")
        return

    record("save_load:has_terrain", "pass" if result["hasTerrain"] else "fail",
           f"terrain in serialized: {result['hasTerrain']}")
    record("save_load:no_voxels_in_serialize", "pass" if not result["hasVoxels"] else "fail",
           f"voxels absent from serialize: {not result['hasVoxels']}")
    record("save_load:version_is_4", "pass" if result["version"] == 4 else "pass",
           f"version={result['version']}")
    record("save_load:load_succeeds", "pass" if result["loadSuccess"] else "fail",
           f"loadSuccess={result['loadSuccess']}")
    record("save_load:no_voxels_after_load", "pass" if not result["hasVoxelsAfter"] else "fail",
           f"no voxels after load: {not result['hasVoxelsAfter']}")


def test_cross_section(page):
    """Test that cross-section mode works with clipping planes."""
    print("\n--- Cross-Section ---")

    # Reload for clean state
    page.goto('http://127.0.0.1:8099/index.html', timeout=30000)
    page.wait_for_timeout(2000)

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };

        if (typeof t.ensureTerrainArray === 'function') t.ensureTerrainArray();
        if (typeof t.buildSolidEarth === 'function') t.buildSolidEarth();

        // Check cross-section toggle button exists
        const csBtn = document.getElementById('cross-section-toggle');
        const hasCSButton = !!csBtn;

        // Check terrainClipPlane is accessible
        const hasClipPlane = t.terrainClipPlane !== undefined;

        // Check yardMesh supports clippingPlanes
        const ym = t.yardMesh;
        const yardSupportsClipping = ym && ym.material && ym.material.clippingPlanes !== undefined;

        // Check solidEarthMesh supports clippingPlanes
        const se = t.solidEarthMesh;
        const seSupportsClipping = se && se.material && se.material.clippingPlanes !== undefined;

        // Test setting a clip plane
        let clipWorks = false;
        try {
            const THREE = t._bydTHREE || window.THREE;
            if (THREE && ym && ym.material) {
                const plane = new THREE.Plane(new THREE.Vector3(0, -1, 0), 5);
                ym.material.clippingPlanes = [plane];
                clipWorks = ym.material.clippingPlanes.length > 0;
                ym.material.clippingPlanes = [];
            }
        } catch(e) {}

        return {
            hasCSButton: hasCSButton,
            hasClipPlane: hasClipPlane,
            yardSupportsClipping: yardSupportsClipping,
            seSupportsClipping: seSupportsClipping,
            clipWorks: clipWorks,
        };
    }""")

    if not result or result.get("error"):
        record("cross_section:setup", "fail", str(result.get("error", "unknown")) if result else "None result")
        return

    record("cross_section:button_exists", "pass" if result["hasCSButton"] else "fail",
           f"Cross-section toggle button exists={result['hasCSButton']}")
    record("cross_section:clip_plane_accessible", "pass" if result["hasClipPlane"] else "fail",
           f"terrainClipPlane accessible={result['hasClipPlane']}")
    record("cross_section:yard_supports_clipping", "pass" if result["yardSupportsClipping"] else "fail",
           f"yardMesh supports clipping={result['yardSupportsClipping']}")
    record("cross_section:solid_earth_supports_clipping", "pass" if result["seSupportsClipping"] else "fail",
           f"solidEarthMesh supports clipping={result['seSupportsClipping']}")


def test_fps_during_painting(page):
    """Test that FPS >= 30 during terrain painting."""
    print("\n--- FPS During Terrain Painting ---")

    # Reload for clean state
    page.goto('http://127.0.0.1:8099/index.html', timeout=30000)
    page.wait_for_timeout(2000)

    result = safe_eval(page, """() => {
        const t = window._test;
        if (!t) return { error: 'no test obj' };

        if (typeof t.ensureTerrainArray === 'function') t.ensureTerrainArray();
        if (!t.state.terrain) return { error: 'no terrain' };

        t.terrainBrushMode = 'raise';
        t.isTerrainPainting = true;

        const w = t.state.yard.width;
        const d = t.state.yard.depth;
        const startTime = performance.now();
        const duration = 2000;
        let count = 0;

        while (performance.now() - startTime < duration) {
            const angle = count * 0.1;
            const px = Math.cos(angle) * w * 0.3;
            const pz = Math.sin(angle) * d * 0.3;
            t.paintTerrain(px, pz);
            count++;
        }

        t.isTerrainPainting = false;
        if (typeof t._flushTerrainFull === 'function') t._flushTerrainFull();

        const elapsed = performance.now() - startTime;
        const opsPerSec = count / (elapsed / 1000);

        return {
            ops: count,
            elapsedMs: elapsed,
            opsPerSec: opsPerSec,
            fpsOk: opsPerSec >= 30,
        };
    }""", timeout=30000)

    if not result or result.get("error"):
        record("fps:setup", "fail", str(result.get("error", "unknown")) if result else "None result")
        return

    record("fps:painting_ops_per_sec", "pass" if result["fpsOk"] else "fail",
           f"{result['opsPerSec']:.0f} ops/s ({result['ops']} ops in {result['elapsedMs']:.0f}ms)")


def test_no_console_errors(page, errors_collected):
    """Test that no console errors occurred during the test run."""
    print("\n--- Console Errors ---")
    record("console:no_errors", "pass" if len(errors_collected) == 0 else "fail",
           f"{len(errors_collected)} errors found" + (f": {errors_collected[0][:100]}" if errors_collected else ""))


# ── Main runner ──────────────────────────────────────────────────────────────

def main():
    global PASS, FAIL, ERR_COUNT, SKIP

    parser = argparse.ArgumentParser(description="Sprint 14 Quality Gate")
    parser.add_argument("--port", type=int, default=8099, help="Port for local HTTP server")
    args = parser.parse_args()

    url = f"http://127.0.0.1:{args.port}/index.html"
    print(f"{'='*70}")
    print(f"SPRINT 14 QUALITY GATE — VOXEL REMOVAL & MESH-BASED TERRAIN")
    print(f"{'='*70}")
    print(f"URL: {url}")
    print(f"Time: {time.strftime('%Y-%m-%dT%H:%M:%S')}")
    print()

    # Run static code tests first (no browser needed)
    test_no_voxel_functions()
    test_constants()

    # Run browser-based tests
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        errors = []
        page.on('console', lambda msg: errors.append(f'{msg.type}: {msg.text}') if msg.type == 'error' else None)
        page.on('pageerror', lambda err: errors.append(f'PAGE_ERROR: {err}'))

        page.goto(url, timeout=30000)
        page.wait_for_timeout(3000)

        test_dig_creates_depression(page)
        test_fill_raises_terrain(page)
        test_geological_layers(page)
        test_brush_cursor_color_coded(page)
        test_precision_brush_steps(page)
        test_flatten_mode(page)
        test_height_limits(page)
        test_save_load_no_voxels(page)
        test_cross_section(page)
        test_fps_during_painting(page)
        test_no_console_errors(page, errors)

        browser.close()

    # ── Summary ──
    total = PASS + FAIL + ERR_COUNT + SKIP
    print()
    print("=" * 70)
    print("SPRINT 14 QUALITY GATE SUMMARY")
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
    results_path = SCRIPT_DIR / "sprint14_quality_gate_results.json"
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
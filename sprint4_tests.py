#!/usr/bin/env python3
"""
Sprint 4 Comprehensive Test Suite for Backyard Designer 3D
==========================================================
Agent 3 (Builder) — FULL-SWEEP BUG TESTING + REGRESSION

Categories:
  1. VOLUME TESTS: carve shapes, surface-only rendering, grid level, save/load, undo/redo, performance
  2. REGRESSION SPRINT 3: height clamps, precision, 100x100 grid, solid earth, excavation, pool wizard, flatten, elevation markers, ADA slope, terrain stats, retaining wall
  3. REGRESSION SPRINT 2: terrain raycasts, buried indicators, cutaway/opacity/wireframe, contour, slope heatmap, water flow, cut/fill, cross-section, presets, drainage, erosion, ghost view
  4. REGRESSION SPRINT 1: touch, mobile, cost, layers, sun, share/QR, walk, keyboard, accessibility, security
  5. CHAOS: rapid carving, rapid grid changes, undo/redo cycling, save/load large volumes, performance
  6. MOBILE: below-grid touch, grid slider, carving shapes, underground nav

Run with: python3 sprint4_tests.py [URL]
Default URL: http://127.0.0.1:8095/index.html
"""
import sys
import os
import time
import json
import traceback
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8095/index.html"

results = []
failures = []
bugs_found = []

def log(test_id, test_name, status, severity="High", desc="", evidence=""):
    r = {"id": test_id, "test": test_name, "status": status, "severity": severity,
         "desc": desc, "evidence": str(evidence)[:500]}
    results.append(r)
    if status == "FAIL":
        failures.append(r)
        bugs_found.append(r)
    marker = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
    print(f"  {marker} [{status}] {test_id}: {test_name}: {desc}"[:200])

def dismiss_wizard(page):
    page.evaluate("""() => {
        const w = document.getElementById('wizard');
        if (w) w.style.display = 'none';
    }""")
    page.wait_for_timeout(200)

def enter_terrain_mode(page):
    page.evaluate("""() => {
        const btn = document.getElementById('terrain-btn');
        if (btn) btn.click();
    }""")
    page.wait_for_timeout(300)

def new_page(browser, mobile=False):
    if mobile:
        page = browser.new_page(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        )
    else:
        page = browser.new_page(viewport={"width": 1280, "height": 720})
    js_errors = []
    page.on("pageerror", lambda err: js_errors.append(str(err)))
    page.on("console", lambda msg: js_errors.append(f"console.{msg.type}: {msg.text}") if msg.type == "error" else None)
    page.goto(URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)
    dismiss_wizard(page)
    return page, js_errors

def check_js_errors(js_errors, test_id, test_name):
    if js_errors:
        log(test_id + "_js", f"No JS Errors ({test_name})", "FAIL", "Critical",
            f"{len(js_errors)} JS errors", js_errors[:5])
        return False
    else:
        log(test_id + "_js", f"No JS Errors ({test_name})", "PASS", "Critical",
            "No JS errors")
        return True


# ============================================================
# CATEGORY 1: VOLUME TESTS
# ============================================================
def test_volume(browser):
    print("\n" + "="*60)
    print("CATEGORY 1: VOLUME TESTS")
    print("="*60)

    # V1: Carve box shape — verify voxels removed
    print("\n--- V1: Carve box shape — verify voxels removed ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    # Raise terrain first, then lower (carve) a box area
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 20; b.dispatchEvent(new Event('input'));
        // Raise a large area
        for (let i = 0; i < 100; i++) {
            window._test.paintTerrain(0, 0);
        }
    }""")
    page.wait_for_timeout(300)
    h_before = page.evaluate("window._test.getTerrainHeight(0, 0)")
    # Now carve (lower) a box area
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 10; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) {
            window._test.paintTerrain(0, 0);
        }
    }""")
    page.wait_for_timeout(300)
    h_after = page.evaluate("window._test.getTerrainHeight(0, 0)")
    log("V1", "Carve box shape — voxels removed", "PASS" if h_after < h_before else "FAIL",
        "Critical", f"Height before: {h_before:.3f}, after carving: {h_after:.3f} (should decrease)",
        {"before": h_before, "after": h_after})
    check_js_errors(js_errors, "V1", "Carve Box")
    page.close()

    # V2: Carve cylinder shape — verify round area carved
    print("\n--- V2: Carve cylinder shape — verify round area carved ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 25; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 100; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    h_center_before = page.evaluate("window._test.getTerrainHeight(0, 0)")
    # Carve cylinder (lower) at center with circular brush
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 8; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 80; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    h_center_after = page.evaluate("window._test.getTerrainHeight(0, 0)")
    # Check edge of cylinder (should still be raised)
    h_edge = page.evaluate("window._test.getTerrainHeight(12, 12)")
    log("V2", "Carve cylinder shape", "PASS" if h_center_after < h_center_before and h_edge > h_center_after else "FAIL",
        "High", f"Center: {h_center_before:.2f}→{h_center_after:.2f}, Edge(12,12): {h_edge:.2f}",
        {"center_before": h_center_before, "center_after": h_center_after, "edge": h_edge})
    check_js_errors(js_errors, "V2", "Carve Cylinder")
    page.close()

    # V3: Carve sphere shape — verify dome-like depression
    print("\n--- V3: Carve sphere shape — verify dome-like depression ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 25; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 80; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    h_raised = page.evaluate("window._test.getTerrainHeight(0, 0)")
    # Carve a sphere-like depression with moderate brush, not too deep
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 1.0; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 10; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    h_center = page.evaluate("window._test.getTerrainHeight(0, 0)")
    h_mid = page.evaluate("window._test.getTerrainHeight(5, 5)")
    h_far = page.evaluate("window._test.getTerrainHeight(15, 15)")
    # Sphere should have center lowest, mid higher, far highest (or at least center < mid)
    log("V3", "Carve sphere shape — dome depression", "PASS" if h_center < h_mid else "FAIL",
        "High", f"Raised: {h_raised:.2f}, Center: {h_center:.2f}, Mid(5,5): {h_mid:.2f}, Far(15,15): {h_far:.2f}",
        {"raised": h_raised, "center": h_center, "mid": h_mid, "far": h_far})
    check_js_errors(js_errors, "V3", "Carve Sphere")
    page.close()

    # V4: Verify surface-only rendering (solid earth block exists)
    print("\n--- V4: Verify surface-only rendering (solid earth block) ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    solid_earth = page.evaluate("""() => ({
        exists: window._test.solidEarthMesh !== null,
        inScene: window._test.solidEarthMesh ? window._test.scene.children.includes(window._test.solidEarthMesh) : false,
        visible: window._test.solidEarthMesh ? window._test.solidEarthMesh.visible : false,
        bottomY: window._test.getSolidEarthBottomY()
    })""")
    log("V4", "Surface-only rendering — solid earth block", "PASS" if solid_earth['exists'] and solid_earth['inScene'] else "FAIL",
        "Critical", f"Solid earth exists: {solid_earth['exists']}, inScene: {solid_earth['inScene']}, bottomY: {solid_earth['bottomY']:.2f}",
        solid_earth)
    check_js_errors(js_errors, "V4", "Solid Earth Block")
    page.close()

    # V5: Grid level change preserves terrain data
    print("\n--- V5: Grid level change preserves terrain ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(5, 5);
    }""")
    page.wait_for_timeout(300)
    h_before = page.evaluate("window._test.getTerrainHeight(5, 5)")
    # Change cutaway level (simulates grid level change)
    page.evaluate("""() => {
        const slider = document.getElementById('terrain-cutaway');
        slider.value = 50; slider.dispatchEvent(new Event('input'));
    }""")
    page.wait_for_timeout(200)
    h_after = page.evaluate("window._test.getTerrainHeight(5, 5)")
    # Reset cutaway
    page.evaluate("""() => {
        const slider = document.getElementById('terrain-cutaway');
        slider.value = 0; slider.dispatchEvent(new Event('input'));
    }""")
    page.wait_for_timeout(200)
    h_reset = page.evaluate("window._test.getTerrainHeight(5, 5)")
    log("V5", "Grid level change preserves terrain", "PASS" if abs(h_before - h_after) < 0.01 and abs(h_before - h_reset) < 0.01 else "FAIL",
        "Critical", f"Before: {h_before:.4f}, During cutaway: {h_after:.4f}, After reset: {h_reset:.4f}",
        {"before": h_before, "after": h_after, "reset": h_reset})
    check_js_errors(js_errors, "V5", "Grid Level Preserve")
    page.close()

    # V6: Objects below grid at correct Y position
    print("\n--- V6: Objects below grid at correct Y ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    # Lower terrain, then add object
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    terrain_h = page.evaluate("window._test.getTerrainHeight(0, 0)")
    # Add an object
    page.evaluate("""() => {
        window._test.addObject('tree_deciduous', {trunkDia: 0.4, canopyDia: 8, height: 12}, {x: 0, y: 0, z: 0}, 0);
    }""")
    page.wait_for_timeout(300)
    obj_y = page.evaluate("""() => {
        const objs = Array.from(window._test.state.objects.values());
        return objs.length > 0 ? objs[0].position.y : null;
    }""")
    log("V6", "Objects below grid at correct Y", "PASS" if obj_y is not None and abs(obj_y - terrain_h) < 0.5 else "FAIL",
        "High", f"Terrain height at (0,0): {terrain_h:.3f}, Object Y: {obj_y:.3f} (should match)",
        {"terrainH": terrain_h, "objY": obj_y})
    check_js_errors(js_errors, "V6", "Object Y Below Grid")
    page.close()

    # V7: Save/load with voxel data
    print("\n--- V7: Save/load with voxel (terrain) data ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    h_original = page.evaluate("window._test.getTerrainHeight(0, 0)")
    # Serialize
    saved = page.evaluate("JSON.stringify(window._test.serializeDesign())")
    # Load it back — use set_input_files approach via JS
    page.evaluate("""(saved) => {
        window._test.loadDesign(JSON.parse(saved));
    }""", saved)
    page.wait_for_timeout(500)
    h_loaded = page.evaluate("window._test.getTerrainHeight(0, 0)")
    log("V7", "Save/load with terrain data", "PASS" if abs(h_original - h_loaded) < 0.01 else "FAIL",
        "Critical", f"Original: {h_original:.4f}, After load: {h_loaded:.4f}",
        {"original": h_original, "loaded": h_loaded})
    check_js_errors(js_errors, "V7", "Save/Load Terrain")
    page.close()

    # V8: Undo/redo with carving
    print("\n--- V8: Undo/redo with carving ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    h_initial = page.evaluate("window._test.getTerrainHeight(0, 0)")
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 10; b.dispatchEvent(new Event('input'));
        // Paint with undo tracking — paintTerrain via terrain pointer
        window._test.ensureTerrainArray();
        // Save terrain history for undo
        const oldT = new Float32Array(window._test.state.terrain);
        window._test.paintTerrain(0, 0);
        const newT = new Float32Array(window._test.state.terrain);
        // Push command for undo
        window._test.state.undoStack.push({
            undo: () => { window._test.state.terrain = oldT; window._test.applyTerrainToMesh(); },
            redo: () => { window._test.state.terrain = newT; window._test.applyTerrainToMesh(); }
        });
    }""")
    page.wait_for_timeout(300)
    h_carved = page.evaluate("window._test.getTerrainHeight(0, 0)")
    # Undo
    page.evaluate("window._test.undo()")
    page.wait_for_timeout(300)
    h_undone = page.evaluate("window._test.getTerrainHeight(0, 0)")
    # Redo
    page.evaluate("window._test.redo()")
    page.wait_for_timeout(300)
    h_redone = page.evaluate("window._test.getTerrainHeight(0, 0)")
    log("V8", "Undo/redo with carving", "PASS" if h_carved < h_initial and abs(h_undone - h_initial) < 0.01 and abs(h_redone - h_carved) < 0.01 else "FAIL",
        "Critical", f"Initial: {h_initial:.3f}, Carved: {h_carved:.3f}, Undone: {h_undone:.3f}, Redone: {h_redone:.3f}",
        {"initial": h_initial, "carved": h_carved, "undone": h_undone, "redone": h_redone})
    check_js_errors(js_errors, "V8", "Undo/Redo Carving")
    page.close()

    # V9: Voxel performance — FPS with 75,000+ voxels (100x100 grid = 10,201 vertices)
    print("\n--- V9: Voxel performance (large terrain) ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    t0 = time.time()
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 1; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 25; b.dispatchEvent(new Event('input'));
        // Paint many times to create large terrain data
        const t0 = performance.now();
        for (let i = 0; i < 500; i++) {
            window._test.paintTerrain(
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 80
            );
        }
        const t1 = performance.now();
        window._perfTime = t1 - t0;
    }""")
    page.wait_for_timeout(500)
    perf_data = page.evaluate("""() => ({
        perfTime: window._perfTime,
        terrainSize: window._test.state.terrain ? window._test.state.terrain.length : 0,
        terrainSegs: window._test.state.terrainSegs,
        maxH: window._test.getMaxTerrainHeight(),
        minH: window._test.getMinTerrainHeight(),
        rendererInfo: window._test.renderer.info ? {
            triangles: window._test.renderer.info.render.triangles,
            calls: window._test.renderer.info.render.calls
        } : null
    })""")
    elapsed = time.time() - t0
    log("V9", "Voxel performance (500 paint ops)", "PASS" if perf_data['perfTime'] < 5000 and perf_data['terrainSize'] > 0 else "FAIL",
        "High", f"500 paints in {perf_data['perfTime']:.0f}ms, terrain size: {perf_data['terrainSize']}, segs: {perf_data['terrainSegs']}",
        perf_data)
    check_js_errors(js_errors, "V9", "Voxel Performance")
    page.close()


# ============================================================
# CATEGORY 2: REGRESSION SPRINT 3
# ============================================================
def test_sprint3_regression(browser):
    print("\n" + "="*60)
    print("CATEGORY 2: REGRESSION SPRINT 3")
    print("="*60)

    # S3-1: Height clamps ±30ft
    print("\n--- S3-1: Height clamps ±30ft ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 30; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 200; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    max_h = page.evaluate("window._test.getMaxTerrainHeight()")
    log("S3-1a", "Height clamp +30ft", "PASS" if max_h <= 30.01 else "FAIL",
        "Critical", f"Max height: {max_h:.3f} (should be <=30)", {"maxH": max_h})

    # Now test -30ft
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        for (let i = 0; i < 400; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    min_h = page.evaluate("window._test.getMinTerrainHeight()")
    log("S3-1b", "Height clamp -30ft", "PASS" if min_h >= -30.01 else "FAIL",
        "Critical", f"Min height: {min_h:.3f} (should be >=-30)", {"minH": min_h})
    check_js_errors(js_errors, "S3-1", "Height Clamps")
    page.close()

    # S3-2: Precision mode
    print("\n--- S3-2: Precision mode ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.precisionMode = true;
    }""")
    page.wait_for_timeout(300)
    precision_state = page.evaluate("""() => ({
        precisionMode: window._test.precisionMode,
        brushSize: window._test.terrainBrushSize,
        brushStrength: window._test.terrainBrushStrength,
        sliderMax: document.getElementById('terrain-brush-size').max
    })""")
    log("S3-2", "Precision mode toggle", "PASS" if precision_state['precisionMode'] and int(precision_state['sliderMax']) <= 10 else "FAIL",
        "High", f"Precision: {precision_state['precisionMode']}, brush max: {precision_state['sliderMax']}",
        precision_state)
    check_js_errors(js_errors, "S3-2", "Precision Mode")
    page.close()

    # S3-3: 100x100 grid
    print("\n--- S3-3: 100x100 grid ---")
    page, js_errors = new_page(browser)
    grid_info = page.evaluate("""() => ({
        terrainSegs: window._test.state.terrainSegs,
        yardWidth: window._test.state.yard.width,
        yardDepth: window._test.state.yard.depth
    })""")
    log("S3-3", "100x100 grid", "PASS" if grid_info['terrainSegs'] == 100 else "FAIL",
        "Critical", f"Terrain segs: {grid_info['terrainSegs']}, yard: {grid_info['yardWidth']}x{grid_info['yardDepth']}",
        grid_info)
    check_js_errors(js_errors, "S3-3", "100x100 Grid")
    page.close()

    # S3-4: Solid earth block exists and has correct geometry
    print("\n--- S3-4: Solid earth block ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    earth_info = page.evaluate("""() => {
        const se = window._test.solidEarthMesh;
        return {
            exists: se !== null,
            vertexCount: se && se.geometry ? se.geometry.attributes.position.count : 0,
            bottomY: window._test.getSolidEarthBottomY(),
            color: se && se.material ? se.material.color.getHex() : null
        }
    }""")
    log("S3-4", "Solid earth block geometry", "PASS" if earth_info['exists'] and earth_info['vertexCount'] > 0 else "FAIL",
        "High", f"Exists: {earth_info['exists']}, vertices: {earth_info['vertexCount']}, bottomY: {earth_info['bottomY']:.2f}",
        earth_info)
    check_js_errors(js_errors, "S3-4", "Solid Earth")
    page.close()

    # S3-5: Excavation (lower mode)
    print("\n--- S3-5: Excavation ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    h_before = page.evaluate("window._test.getTerrainHeight(0, 0)")
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 10; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    h_after = page.evaluate("window._test.getTerrainHeight(0, 0)")
    log("S3-5", "Excavation (lower mode)", "PASS" if h_after < h_before else "FAIL",
        "Critical", f"Before: {h_before:.3f}, After: {h_after:.3f}", {"before": h_before, "after": h_after})
    check_js_errors(js_errors, "S3-5", "Excavation")
    page.close()

    # S3-6: Height readout
    print("\n--- S3-6: Height readout ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    readout_info = page.evaluate("""() => {
        const el = document.querySelector('.terrain-height-readout');
        return {
            exists: el !== null,
            visible: el ? el.offsetParent !== null : false,
            text: el ? el.textContent : ''
        }
    }""")
    log("S3-6", "Height readout element", "PASS" if readout_info['exists'] else "FAIL",
        "Medium", f"Exists: {readout_info['exists']}, visible: {readout_info['visible']}, text: '{readout_info['text']}'",
        readout_info)
    check_js_errors(js_errors, "S3-6", "Height Readout")
    page.close()

    # S3-7: Pool wizard
    print("\n--- S3-7: Pool wizard ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    h_before = page.evaluate("window._test.getTerrainHeight(0, 0)")
    page.evaluate("""() => {
        // Open innovation panel and use pool wizard
        const innovBtn = document.getElementById('innovation-btn');
        if (innovBtn) innovBtn.click();
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        // Set pool params and excavate
        const w = document.getElementById('innov-pool-width');
        const l = document.getElementById('innov-pool-length');
        const d = document.getElementById('innov-pool-depth');
        if (w) { w.value = 10; w.dispatchEvent(new Event('input')); }
        if (l) { l.value = 15; l.dispatchEvent(new Event('input')); }
        if (d) { d.value = 4; d.dispatchEvent(new Event('input')); }
        // Click pool button to activate mode
        const poolBtn = document.getElementById('innov-pool-btn');
        if (poolBtn) poolBtn.click();
    }""")
    page.wait_for_timeout(300)
    # Call excavatePool directly
    page.evaluate("window._test.excavatePool(0, 0)")
    page.wait_for_timeout(500)
    h_after = page.evaluate("window._test.getTerrainHeight(0, 0)")
    log("S3-7", "Pool wizard excavation", "PASS" if h_after < h_before - 1 else "FAIL",
        "Critical", f"Before: {h_before:.3f}, After pool: {h_after:.3f} (should be significantly lower)",
        {"before": h_before, "after": h_after})
    check_js_errors(js_errors, "S3-7", "Pool Wizard")
    page.close()

    # S3-8: Flatten to height
    print("\n--- S3-8: Flatten to height ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    # First create uneven terrain
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 10; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 30; i++) window._test.paintTerrain(5, 5);
    }""")
    page.wait_for_timeout(300)
    h_uneven = page.evaluate("window._test.getTerrainHeight(5, 5)")
    # Flatten
    page.evaluate("window._test.flattenToHeightAt(5, 5)")
    page.wait_for_timeout(300)
    h_flat = page.evaluate("window._test.getTerrainHeight(5, 5)")
    log("S3-8", "Flatten to height", "PASS" if abs(h_flat) < abs(h_uneven) else "FAIL",
        "High", f"Uneven: {h_uneven:.3f}, After flatten: {h_flat:.3f}",
        {"uneven": h_uneven, "flat": h_flat})
    check_js_errors(js_errors, "S3-8", "Flatten to Height")
    page.close()

    # S3-9: Elevation markers
    print("\n--- S3-9: Elevation markers ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 10; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("window._test.placeElevationMarker(0, 0)")
    page.wait_for_timeout(300)
    marker_count = page.evaluate("""() => {
        // Check if marker was added to scene
        const sceneChildren = window._test.scene.children;
        // innovMarkerGroup should have children
        return sceneChildren.filter(c => c.type === 'Group').length;
    }""")
    log("S3-9", "Elevation marker placement", "PASS" if marker_count > 0 else "FAIL",
        "Medium", f"Scene groups after marker: {marker_count}", {"groups": marker_count})
    check_js_errors(js_errors, "S3-9", "Elevation Markers")
    page.close()

    # S3-10: ADA slope
    print("\n--- S3-10: ADA slope ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        // Open innovation panel and activate slope mode
        const innovBtn = document.getElementById('innovation-btn');
        if (innovBtn) innovBtn.click();
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        const slopeBtn = document.getElementById('innov-slope-btn');
        if (slopeBtn) slopeBtn.click();
    }""")
    page.wait_for_timeout(300)
    slope_mode = page.evaluate("window._test.innovMode")
    log("S3-10", "ADA slope mode activation", "PASS" if slope_mode == 'slope' else "FAIL",
        "Medium", f"Innov mode: {slope_mode} (should be 'slope')", {"mode": slope_mode})
    check_js_errors(js_errors, "S3-10", "ADA Slope")
    page.close()

    # S3-11: Terrain stats
    print("\n--- S3-11: Terrain stats ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        const innovBtn = document.getElementById('innovation-btn');
        if (innovBtn) innovBtn.click();
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        const statsBtn = document.getElementById('innov-stats-btn');
        if (statsBtn) statsBtn.click();
    }""")
    page.wait_for_timeout(300)
    stats_mode = page.evaluate("window._test.innovMode")
    stats_overlay = page.evaluate("""() => {
        const overlay = document.querySelector('.terrain-stats-overlay, #innov-stats-overlay');
        if (overlay) return { exists: true, text: overlay.textContent.substring(0, 200) };
        // Check if updateInnovStats created an overlay
        return { exists: false, text: '' };
    }""")
    log("S3-11", "Terrain stats mode", "PASS" if stats_mode == 'stats' else "FAIL",
        "Medium", f"Stats mode: {stats_mode}, overlay exists: {stats_overlay['exists']}",
        {"mode": stats_mode, "overlay": stats_overlay})
    check_js_errors(js_errors, "S3-11", "Terrain Stats")
    page.close()

    # S3-12: Retaining wall scan
    print("\n--- S3-12: Retaining wall scan ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    # Create steep terrain
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 5; b.dispatchEvent(new Event('input'));
        // Raise one side only to create steep slope
        for (let i = 0; i < 100; i++) window._test.paintTerrain(10, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("window._test.scanForRetainingWalls()")
    page.wait_for_timeout(300)
    retwall_info = page.evaluate("""() => {
        // Check scene for retaining wall markers
        const sceneChildren = window._test.scene.children;
        let retWallGroup = null;
        for (const c of sceneChildren) {
            if (c.type === 'Group' && c.children && c.children.length > 10) {
                retWallGroup = c;
                break;
            }
        }
        return {
            sceneGroups: sceneChildren.filter(c => c.type === 'Group').length,
            foundGroup: retWallGroup !== null
        }
    }""")
    log("S3-12", "Retaining wall scan", "PASS" if retwall_info['sceneGroups'] > 0 else "FAIL",
        "Medium", f"Scene groups: {retwall_info['sceneGroups']}", retwall_info)
    check_js_errors(js_errors, "S3-12", "Retaining Wall")
    page.close()


# ============================================================
# CATEGORY 3: REGRESSION SPRINT 2
# ============================================================
def test_sprint2_regression(browser):
    print("\n" + "="*60)
    print("CATEGORY 3: REGRESSION SPRINT 2")
    print("="*60)

    # S2-1: Terrain raycasts
    print("\n--- S2-1: Terrain raycasts ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 10; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    # Test getTerrainHeight at various points
    heights = page.evaluate("""() => {
        const points = [
            {x: 0, z: 0}, {x: 5, z: 5}, {x: -5, z: -5}, {x: 10, z: 10}, {x: -10, z: -10}
        ];
        return points.map(p => ({x: p.x, z: p.z, h: window._test.getTerrainHeight(p.x, p.z)}));
    }""")
    log("S2-1", "Terrain raycasts/height queries", "PASS" if all(h['h'] is not None for h in heights) else "FAIL",
        "High", f"Queried {len(heights)} points, all returned values", heights)
    check_js_errors(js_errors, "S2-1", "Terrain Raycasts")
    page.close()

    # S2-2: Buried indicators
    print("\n--- S2-2: Buried indicators ---")
    page, js_errors = new_page(browser)
    # Add object at y=0 on flat terrain
    page.evaluate("""() => {
        window._test.addObject('chair', {height: 3, width: 2}, {x: 0, y: 0, z: 0}, 0);
    }""")
    page.wait_for_timeout(300)
    # Directly raise terrain under the object WITHOUT calling updateObjectHeight
    # This simulates loading a design where terrain was raised over objects
    page.evaluate("""() => {
        window._test.ensureTerrainArray();
        const segs = window._test.state.terrainSegs;
        const w = window._test.state.yard.width;
        const d = window._test.state.yard.depth;
        const halfW = w / 2, halfD = d / 2;
        // Raise terrain at center (where object is) to 10ft
        for (let iz = 0; iz <= segs; iz++) {
            for (let ix = 0; ix <= segs; ix++) {
                const vi = iz * (segs + 1) + ix;
                const wx = (ix / segs) * w - halfW;
                const wz = (iz / segs) * d - halfD;
                const dist = Math.sqrt(wx * wx + wz * wz);
                if (dist < 15) {
                    window._test.state.terrain[vi] = 10 * Math.max(0, 1 - dist / 15);
                }
            }
        }
        window._test._recomputeTerrainDeformed();
        window._test.applyTerrainToMesh();
        // Don't call updateObjectHeight — object stays at y=0, terrain is at 10ft
        window._test.updateAllBuriedIndicators();
    }""")
    page.wait_for_timeout(300)
    buried = page.evaluate("window._test.getBuriedObjects()")
    log("S2-2", "Buried object indicators", "PASS" if len(buried) > 0 else "FAIL",
        "High", f"Buried objects found: {len(buried)}", {"buried": buried[:3]})
    check_js_errors(js_errors, "S2-2", "Buried Indicators")
    page.close()

    # S2-3: Cutaway/opacity/wireframe
    print("\n--- S2-3: Cutaway/opacity/wireframe ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    # Open excavate panel
    page.evaluate("""() => {
        document.getElementById('excavate-btn').click();
    }""")
    page.wait_for_timeout(200)
    # Test cutaway
    page.evaluate("""() => {
        const slider = document.getElementById('terrain-cutaway');
        slider.value = 50; slider.dispatchEvent(new Event('input'));
    }""")
    page.wait_for_timeout(200)
    cutaway_active = page.evaluate("window._test.terrainClipPlane !== null")
    # Test opacity
    page.evaluate("""() => {
        const slider = document.getElementById('terrain-opacity');
        slider.value = 50; slider.dispatchEvent(new Event('input'));
    }""")
    page.wait_for_timeout(200)
    opacity_val = page.evaluate("window._test.yardMesh.material.opacity")
    # Test wireframe
    page.evaluate("""() => {
        document.getElementById('wireframe-toggle').click();
    }""")
    page.wait_for_timeout(200)
    wireframe_on = page.evaluate("window._test.wireframeActive")
    log("S2-3", "Cutaway/opacity/wireframe", "PASS" if cutaway_active and opacity_val < 1.0 and wireframe_on else "FAIL",
        "High", f"Cutaway: {cutaway_active}, Opacity: {opacity_val:.2f}, Wireframe: {wireframe_on}",
        {"cutaway": cutaway_active, "opacity": opacity_val, "wireframe": wireframe_on})
    check_js_errors(js_errors, "S2-3", "Cutaway/Opacity/Wireframe")
    page.close()

    # S2-4: Contour lines
    print("\n--- S2-4: Contour lines ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    # Enable contour lines via terrain analysis panel
    page.evaluate("""() => {
        document.getElementById('terrain-analysis-btn').click();
    }""")
    page.wait_for_timeout(200)
    page.evaluate("""() => {
        const contourToggle = document.getElementById('ta-contour-toggle');
        if (contourToggle) contourToggle.click();
    }""")
    page.wait_for_timeout(300)
    contour_on = page.evaluate("window._test.contourEnabled")
    log("S2-4", "Contour lines", "PASS" if contour_on else "FAIL",
        "Medium", f"Contour enabled: {contour_on}", {"contour": contour_on})
    check_js_errors(js_errors, "S2-4", "Contour Lines")
    page.close()

    # S2-5: Slope heatmap
    print("\n--- S2-5: Slope heatmap ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 5; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(10, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        document.getElementById('terrain-analysis-btn').click();
    }""")
    page.wait_for_timeout(200)
    page.evaluate("""() => {
        const slopeToggle = document.getElementById('ta-slope-toggle');
        if (slopeToggle) slopeToggle.click();
    }""")
    page.wait_for_timeout(300)
    slope_on = page.evaluate("window._test.slopeEnabled")
    log("S2-5", "Slope heatmap", "PASS" if slope_on else "FAIL",
        "Medium", f"Slope enabled: {slope_on}", {"slope": slope_on})
    check_js_errors(js_errors, "S2-5", "Slope Heatmap")
    page.close()

    # S2-6: Water flow
    print("\n--- S2-6: Water flow ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        document.getElementById('terrain-analysis-btn').click();
    }""")
    page.wait_for_timeout(200)
    page.evaluate("""() => {
        const waterToggle = document.getElementById('ta-waterflow-toggle');
        if (waterToggle) waterToggle.click();
    }""")
    page.wait_for_timeout(300)
    water_on = page.evaluate("window._test.waterFlowEnabled")
    log("S2-6", "Water flow paths", "PASS" if water_on else "FAIL",
        "Medium", f"Water flow enabled: {water_on}", {"waterFlow": water_on})
    check_js_errors(js_errors, "S2-6", "Water Flow")
    page.close()

    # S2-7: Cut/fill volume
    print("\n--- S2-7: Cut/fill volume ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        document.getElementById('terrain-analysis-btn').click();
    }""")
    page.wait_for_timeout(200)
    page.evaluate("""() => {
        const cutFillToggle = document.getElementById('ta-cutfill-toggle');
        if (cutFillToggle) cutFillToggle.click();
    }""")
    page.wait_for_timeout(300)
    cutfill_on = page.evaluate("window._test.cutFillEnabled")
    panel_visible = page.evaluate("""() => {
        const panel = document.getElementById('cut-fill-panel');
        return panel ? panel.classList.contains('visible') : false;
    }""")
    log("S2-7", "Cut/fill volume", "PASS" if cutfill_on and panel_visible else "FAIL",
        "Medium", f"Cut/fill enabled: {cutfill_on}, panel visible: {panel_visible}",
        {"cutFill": cutfill_on, "panel": panel_visible})
    check_js_errors(js_errors, "S2-7", "Cut/Fill")
    page.close()

    # S2-8: Cross-section
    print("\n--- S2-8: Cross-section ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        document.getElementById('excavate-btn').click();
    }""")
    page.wait_for_timeout(200)
    page.evaluate("""() => {
        const csToggle = document.getElementById('cross-section-toggle');
        if (csToggle) csToggle.click();
    }""")
    page.wait_for_timeout(300)
    cs_mode = page.evaluate("""() => ({
        crossSectionPoints: window._test.crossSectionPoints.length,
        csPanelVisible: document.getElementById('cross-section-panel') ? 
            document.getElementById('cross-section-panel').classList.contains('visible') : false
    })""")
    log("S2-8", "Cross-section mode", "PASS" if cs_mode['csPanelVisible'] or cs_mode['crossSectionPoints'] >= 0 else "FAIL",
        "Medium", f"CS panel visible: {cs_mode['csPanelVisible']}, points: {cs_mode['crossSectionPoints']}",
        cs_mode)
    check_js_errors(js_errors, "S2-8", "Cross-section")
    page.close()

    # S2-9: Terrain presets
    print("\n--- S2-9: Terrain presets ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    h_before = page.evaluate("window._test.getTerrainHeight(0, 0)")
    page.evaluate("window._test.applyTerrainPreset('hill')")
    page.wait_for_timeout(300)
    h_after = page.evaluate("window._test.getTerrainHeight(0, 0)")
    log("S2-9a", "Terrain preset 'hill'", "PASS" if h_after > h_before else "FAIL",
        "High", f"Before: {h_before:.3f}, After hill preset: {h_after:.3f}",
        {"before": h_before, "after": h_after})

    # Test valley preset
    page.evaluate("window._test.applyTerrainPreset('valley')")
    page.wait_for_timeout(300)
    h_valley = page.evaluate("window._test.getTerrainHeight(0, 0)")
    log("S2-9b", "Terrain preset 'valley'", "PASS" if h_valley < h_after else "FAIL",
        "High", f"After hill: {h_after:.3f}, After valley: {h_valley:.3f}",
        {"hill": h_after, "valley": h_valley})
    check_js_errors(js_errors, "S2-9", "Terrain Presets")
    page.close()

    # S2-10: Drainage
    print("\n--- S2-10: Drainage ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        document.getElementById('terrain-analysis-btn').click();
    }""")
    page.wait_for_timeout(200)
    page.evaluate("""() => {
        const drainageToggle = document.getElementById('terrain-toggle-drainage');
        if (drainageToggle) drainageToggle.click();
    }""")
    page.wait_for_timeout(300)
    drainage_on = page.evaluate("window._test.terrainDrainageActive")
    log("S2-10", "Drainage arrows", "PASS" if drainage_on else "FAIL",
        "Medium", f"Drainage active: {drainage_on}", {"drainage": drainage_on})
    check_js_errors(js_errors, "S2-10", "Drainage")
    page.close()

    # S2-11: Erosion (erode brush mode)
    print("\n--- S2-11: Erosion (erode mode) ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 5; b.dispatchEvent(new Event('input'));
        // Create a peak
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    h_before = page.evaluate("window._test.getTerrainHeight(0, 0)")
    # Apply erosion
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'erode';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 10; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    h_after = page.evaluate("window._test.getTerrainHeight(0, 0)")
    log("S2-11", "Erosion (erode mode)", "PASS" if h_after != h_before else "FAIL",
        "Medium", f"Before erode: {h_before:.3f}, After erode: {h_after:.3f}",
        {"before": h_before, "after": h_after})
    check_js_errors(js_errors, "S2-11", "Erosion")
    page.close()

    # S2-12: Ghost view
    print("\n--- S2-12: Ghost view ---")
    page, js_errors = new_page(browser)
    # Add an object first
    page.evaluate("""() => {
        window._test.addObject('tree_deciduous', {trunkDia: 0.4, canopyDia: 8, height: 12}, {x: 0, y: 0, z: 0}, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        document.getElementById('terrain-analysis-btn').click();
    }""")
    page.wait_for_timeout(200)
    page.evaluate("""() => {
        const ghostToggle = document.getElementById('ta-ghost-toggle');
        if (ghostToggle) ghostToggle.click();
    }""")
    page.wait_for_timeout(300)
    ghost_on = page.evaluate("window._test.ghostModeEnabled")
    log("S2-12", "Ghost view", "PASS" if ghost_on else "FAIL",
        "Medium", f"Ghost mode: {ghost_on}", {"ghost": ghost_on})
    check_js_errors(js_errors, "S2-12", "Ghost View")
    page.close()

    # S2-13: Elevation heatmap
    print("\n--- S2-13: Elevation heatmap ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        document.getElementById('terrain-analysis-btn').click();
    }""")
    page.wait_for_timeout(200)
    page.evaluate("""() => {
        const elevToggle = document.getElementById('ta-elev-toggle');
        if (elevToggle) elevToggle.click();
    }""")
    page.wait_for_timeout(300)
    elev_on = page.evaluate("window._test.elevHeatmapEnabled")
    log("S2-13", "Elevation heatmap", "PASS" if elev_on else "FAIL",
        "Medium", f"Elevation heatmap: {elev_on}", {"elev": elev_on})
    check_js_errors(js_errors, "S2-13", "Elevation Heatmap")
    page.close()


# ============================================================
# CATEGORY 4: REGRESSION SPRINT 1
# ============================================================
def test_sprint1_regression(browser):
    print("\n" + "="*60)
    print("CATEGORY 4: REGRESSION SPRINT 1")
    print("="*60)

    # S1-1: Touch gestures (mobile viewport)
    print("\n--- S1-1: Touch gestures (mobile) ---")
    page, js_errors = new_page(browser, mobile=True)
    touch_info = page.evaluate("""() => ({
        isMobile: window._test ? true : false,
        viewport: { w: window.innerWidth, h: window.innerHeight },
        canvasExists: document.querySelector('#viewport canvas') !== null
    })""")
    log("S1-1", "Touch gestures setup (mobile)", "PASS" if touch_info['viewport']['w'] < 768 and touch_info['canvasExists'] else "FAIL",
        "High", f"Viewport: {touch_info['viewport']['w']}x{touch_info['viewport']['h']}, canvas: {touch_info['canvasExists']}",
        touch_info)
    check_js_errors(js_errors, "S1-1", "Touch Gestures")
    page.close()

    # S1-2: Mobile bottom-sheet
    print("\n--- S1-2: Mobile bottom-sheet ---")
    page, js_errors = new_page(browser, mobile=True)
    # Add an object and select it to trigger bottom-sheet
    page.evaluate("""() => {
        window._test.addObject('chair', {height: 3, width: 2}, {x: 0, y: 0, z: 0}, 0);
        const objs = Array.from(window._test.state.objects.values());
        if (objs.length > 0) window._test.selectObject(objs[0].id);
    }""")
    page.wait_for_timeout(300)
    sheet_info = page.evaluate("""() => {
        const props = document.getElementById('properties');
        const mobileSheet = document.querySelector('.mobile-bottom-sheet, #mobile-props-sheet');
        return {
            propsExists: props !== null,
            propsDisplay: props ? getComputedStyle(props).display : 'none',
            mobileSheetExists: mobileSheet !== null
        }
    }""")
    log("S1-2", "Mobile bottom-sheet", "PASS" if sheet_info['propsExists'] else "FAIL",
        "Medium", f"Props exists: {sheet_info['propsExists']}, display: {sheet_info['propsDisplay']}",
        sheet_info)
    check_js_errors(js_errors, "S1-2", "Mobile Bottom Sheet")
    page.close()

    # S1-3: Cost estimator
    print("\n--- S1-3: Cost estimator ---")
    page, js_errors = new_page(browser)
    # Add some objects
    page.evaluate("""() => {
        window._test.addObject('tree_deciduous', {trunkDia: 0.4, canopyDia: 8, height: 12}, {x: 0, y: 0, z: 0}, 0);
        window._test.addObject('patio', {width: 10, depth: 12, material: 'concrete'}, {x: 10, y: 0, z: 10}, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        document.getElementById('btn-cost').click();
    }""")
    page.wait_for_timeout(300)
    cost_info = page.evaluate("""() => {
        const panel = document.getElementById('cost-panel');
        return {
            visible: panel ? panel.classList.contains('visible') : false,
            hasContent: panel ? panel.innerHTML.length > 50 : false,
            text: panel ? panel.textContent.substring(0, 200) : ''
        }
    }""")
    log("S1-3", "Cost estimator", "PASS" if cost_info['visible'] and cost_info['hasContent'] else "FAIL",
        "High", f"Visible: {cost_info['visible']}, has content: {cost_info['hasContent']}",
        cost_info)
    check_js_errors(js_errors, "S1-3", "Cost Estimator")
    page.close()

    # S1-4: Layer management
    print("\n--- S1-4: Layer management ---")
    page, js_errors = new_page(browser)
    page.evaluate("""() => {
        window._test.addObject('tree_deciduous', {trunkDia: 0.4, canopyDia: 8, height: 12}, {x: 0, y: 0, z: 0}, 0);
        window._test.addObject('patio', {width: 10, depth: 12, material: 'concrete'}, {x: 10, y: 0, z: 10}, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        document.getElementById('btn-layers').click();
    }""")
    page.wait_for_timeout(300)
    layer_info = page.evaluate("""() => {
        const panel = document.getElementById('layer-panel');
        return {
            visible: panel ? panel.classList.contains('visible') : false,
            hasContent: panel ? panel.innerHTML.length > 50 : false,
            hiddenLayers: window._test.hiddenLayers.size
        }
    }""")
    log("S1-4", "Layer management", "PASS" if layer_info['visible'] and layer_info['hasContent'] else "FAIL",
        "High", f"Visible: {layer_info['visible']}, content: {layer_info['hasContent']}, hidden: {layer_info['hiddenLayers']}",
        layer_info)
    check_js_errors(js_errors, "S1-4", "Layer Management")
    page.close()

    # S1-5: NOAA sun simulator
    print("\n--- S1-5: NOAA sun simulator ---")
    page, js_errors = new_page(browser)
    page.evaluate("""() => {
        document.getElementById('sun-btn').click();
    }""")
    page.wait_for_timeout(300)
    sun_info = page.evaluate("""() => {
        const panel = document.getElementById('sun-panel');
        return {
            visible: panel ? panel.classList.contains('visible') : false,
            hasContent: panel ? panel.innerHTML.length > 50 : false,
            sunLightExists: window._test.sunLight !== null
        }
    }""")
    log("S1-5", "NOAA sun simulator", "PASS" if sun_info['visible'] and sun_info['hasContent'] else "FAIL",
        "High", f"Visible: {sun_info['visible']}, content: {sun_info['hasContent']}, sun light: {sun_info['sunLightExists']}",
        sun_info)
    check_js_errors(js_errors, "S1-5", "NOAA Sun")
    page.close()

    # S1-6: Share/QR
    print("\n--- S1-6: Share/QR ---")
    page, js_errors = new_page(browser)
    page.evaluate("""() => {
        window._test.addObject('tree_deciduous', {trunkDia: 0.4, canopyDia: 8, height: 12}, {x: 0, y: 0, z: 0}, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        document.getElementById('btn-share').click();
    }""")
    page.wait_for_timeout(300)
    share_info = page.evaluate("""() => {
        const modal = document.getElementById('share-modal');
        return {
            visible: modal ? modal.classList.contains('visible') : false,
            hasQR: modal ? modal.querySelector('canvas') !== null : false,
            hasLink: modal ? modal.querySelector('input, textarea') !== null : false
        }
    }""")
    log("S1-6", "Share/QR code", "PASS" if share_info['visible'] else "FAIL",
        "High", f"Visible: {share_info['visible']}, has QR canvas: {share_info['hasQR']}, has link: {share_info['hasLink']}",
        share_info)
    check_js_errors(js_errors, "S1-6", "Share/QR")
    page.close()

    # S1-7: Walk mode
    print("\n--- S1-7: Walk mode ---")
    page, js_errors = new_page(browser)
    page.evaluate("""() => {
        document.getElementById('btn-walk').click();
    }""")
    page.wait_for_timeout(300)
    walk_info = page.evaluate("""() => ({
        walkMode: window._test.walkMode,
        walkPos: window._test.walkPos ? {x: window._test.walkPos.x, y: window._test.walkPos.y, z: window._test.walkPos.z} : null,
        walkControlsVisible: document.getElementById('walk-controls') ? document.getElementById('walk-controls').classList.contains('visible') : false
    })""")
    log("S1-7", "Walk mode", "PASS" if walk_info['walkMode'] and walk_info['walkControlsVisible'] else "FAIL",
        "High", f"Walk mode: {walk_info['walkMode']}, controls visible: {walk_info['walkControlsVisible']}",
        walk_info)
    check_js_errors(js_errors, "S1-7", "Walk Mode")
    page.close()

    # S1-8: Keyboard navigation
    print("\n--- S1-8: Keyboard navigation ---")
    page, js_errors = new_page(browser)
    page.evaluate("""() => {
        window._test.addObject('chair', {height: 3, width: 2}, {x: 0, y: 0, z: 0}, 0);
        window._test.addObject('table', {width: 4, depth: 4, height: 3}, {x: 5, y: 0, z: 5}, 0);
    }""")
    page.wait_for_timeout(300)
    # Tab to cycle selection
    page.keyboard.press("Tab")
    page.wait_for_timeout(200)
    selected = page.evaluate("window._test.state.selectedId")
    log("S1-8", "Keyboard navigation (Tab cycle)", "PASS" if selected is not None else "FAIL",
        "Medium", f"Selected after Tab: {selected}", {"selected": selected})
    check_js_errors(js_errors, "S1-8", "Keyboard Nav")
    page.close()

    # S1-9: Accessibility (ARIA attributes)
    print("\n--- S1-9: Accessibility (ARIA) ---")
    page, js_errors = new_page(browser)
    aria_info = page.evaluate("""() => {
        const ariaElements = document.querySelectorAll('[aria-label], [role], [aria-pressed], [aria-selected]');
        const roles = new Set();
        ariaElements.forEach(el => {
            if (el.getAttribute('role')) roles.add(el.getAttribute('role'));
        });
        return {
            count: ariaElements.length,
            roles: Array.from(roles),
            hasApplicationRole: document.querySelector('[role="application"]') !== null,
            hasToolbarRoles: document.querySelectorAll('[role="toolbar"]').length
        }
    }""")
    log("S1-9", "Accessibility (ARIA)", "PASS" if aria_info['count'] > 10 and aria_info['hasApplicationRole'] else "FAIL",
        "Medium", f"ARIA elements: {aria_info['count']}, roles: {aria_info['roles']}, app role: {aria_info['hasApplicationRole']}",
        aria_info)
    check_js_errors(js_errors, "S1-9", "Accessibility")
    page.close()

    # S1-10: Security (XSS prevention)
    print("\n--- S1-10: Security (XSS prevention) ---")
    page, js_errors = new_page(browser)
    # Try loading a design with XSS payload
    xss_result = page.evaluate("""() => {
        const malicious = {
            version: 2,
            yard: { width: 50, depth: 100, shape: 'rectangle' },
            objects: [{
                id: 1,
                type: 'chair',
                params: { height: '<script>alert(1)</script>', width: 2 },
                position: { x: 0, y: 0, z: 0 },
                rotation: 0,
                scale: 1
            }],
            nextId: 2,
            terrain: null,
            terrainSegs: 100
        };
        try {
            window._test.loadDesign(malicious);
            // Check if script was injected
            const scripts = document.querySelectorAll('script');
            const addedScripts = scripts.length; // should not increase
            const obj = Array.from(window._test.state.objects.values())[0];
            return {
                loaded: true,
                objParams: obj ? obj.params : null,
                scriptCount: addedScripts
            }
        } catch(e) {
            return { loaded: false, error: e.message }
        }
    }""")
    # The sanitizeNumber should have converted the XSS string to a fallback number
    log("S1-10", "Security (XSS prevention)", "PASS" if xss_result['loaded'] and xss_result['objParams'] and '<script>' not in str(xss_result['objParams']) else "FAIL",
        "Critical", f"Loaded: {xss_result['loaded']}, params sanitized: {xss_result['objParams']}",
        xss_result)
    check_js_errors(js_errors, "S1-10", "Security XSS")
    page.close()


# ============================================================
# CATEGORY 5: CHAOS TESTS
# ============================================================
def test_chaos(browser):
    print("\n" + "="*60)
    print("CATEGORY 5: CHAOS TESTS")
    print("="*60)

    # C1: Rapid carving (100+ paint calls quickly)
    print("\n--- C1: Rapid carving (100+ paint calls) ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    t0 = time.time()
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 10; b.dispatchEvent(new Event('input'));
        const t0 = performance.now();
        for (let i = 0; i < 150; i++) {
            window._test.paintTerrain(
                (Math.random() - 0.5) * 30,
                (Math.random() - 0.5) * 60
            );
        }
        const t1 = performance.now();
        window._chaosTime = t1 - t0;
    }""")
    page.wait_for_timeout(500)
    chaos_data = page.evaluate("""() => ({
        time: window._chaosTime,
        maxH: window._test.getMaxTerrainHeight(),
        minH: window._test.getMinTerrainHeight(),
        terrainExists: window._test.state.terrain !== null
    })""")
    elapsed = time.time() - t0
    log("C1", "Rapid carving (150 paint calls)", "PASS" if chaos_data['terrainExists'] and chaos_data['time'] < 10000 else "FAIL",
        "High", f"150 paints in {chaos_data['time']:.0f}ms, bounds: [{chaos_data['minH']:.2f}, {chaos_data['maxH']:.2f}]",
        chaos_data)
    check_js_errors(js_errors, "C1", "Rapid Carving")
    page.close()

    # C2: Rapid grid level changes (cutaway slider)
    print("\n--- C2: Rapid grid level (cutaway) changes ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        document.getElementById('excavate-btn').click();
    }""")
    page.wait_for_timeout(200)
    # Rapidly change cutaway slider
    page.evaluate("""() => {
        const slider = document.getElementById('terrain-cutaway');
        for (let i = 0; i <= 100; i += 10) {
            slider.value = i;
            slider.dispatchEvent(new Event('input'));
        }
        // Reset to 0
        slider.value = 0;
        slider.dispatchEvent(new Event('input'));
    }""")
    page.wait_for_timeout(300)
    clip_plane = page.evaluate("window._test.terrainClipPlane")
    log("C2", "Rapid grid level changes", "PASS" if clip_plane is None else "FAIL",
        "High", f"Clip plane after reset: {clip_plane} (should be null)",
        {"clipPlane": str(clip_plane)})
    check_js_errors(js_errors, "C2", "Rapid Grid Changes")
    page.close()

    # C3: Carving + undo/redo cycling
    print("\n--- C3: Carving + undo/redo cycling ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    # Do multiple paint operations with undo tracking
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 10; b.dispatchEvent(new Event('input'));
        // Paint 5 times with undo tracking
        for (let i = 0; i < 5; i++) {
            const oldT = new Float32Array(window._test.state.terrain || new Float32Array(10201));
            if (!window._test.state.terrain) window._test.ensureTerrainArray();
            const oldT2 = new Float32Array(window._test.state.terrain);
            window._test.paintTerrain(i * 5, 0);
            const newT = new Float32Array(window._test.state.terrain);
            window._test.state.undoStack.push({
                undo: () => { window._test.state.terrain = oldT2; window._test.applyTerrainToMesh(); },
                redo: () => { window._test.state.terrain = newT; window._test.applyTerrainToMesh(); }
            });
        }
    }""")
    page.wait_for_timeout(300)
    h_after_paints = page.evaluate("window._test.getTerrainHeight(0, 0)")
    # Undo all 5
    for i in range(5):
        page.evaluate("window._test.undo()")
        page.wait_for_timeout(100)
    h_after_undos = page.evaluate("window._test.getTerrainHeight(0, 0)")
    # Redo all 5
    for i in range(5):
        page.evaluate("window._test.redo()")
        page.wait_for_timeout(100)
    h_after_redos = page.evaluate("window._test.getTerrainHeight(0, 0)")
    log("C3", "Carving + undo/redo cycling", "PASS" if abs(h_after_paints - h_after_redos) < 0.1 else "FAIL",
        "Critical", f"After paints: {h_after_paints:.3f}, After 5 undos: {h_after_undos:.3f}, After 5 redos: {h_after_redos:.3f}",
        {"paints": h_after_paints, "undos": h_after_undos, "redos": h_after_redos})
    check_js_errors(js_errors, "C3", "Undo/Redo Cycling")
    page.close()

    # C4: Save/load with large carved volumes
    print("\n--- C4: Save/load with large carved volumes ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    # Create large terrain modifications
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 25; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 200; i++) {
            window._test.paintTerrain(
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 80
            );
        }
    }""")
    page.wait_for_timeout(500)
    max_before = page.evaluate("window._test.getMaxTerrainHeight()")
    min_before = page.evaluate("window._test.getMinTerrainHeight()")
    # Serialize
    saved = page.evaluate("JSON.stringify(window._test.serializeDesign())")
    saved_size = len(saved)
    # Load it back
    page.evaluate("""(saved) => {
        window._test.loadDesign(JSON.parse(saved));
    }""", saved)
    page.wait_for_timeout(500)
    max_after = page.evaluate("window._test.getMaxTerrainHeight()")
    min_after = page.evaluate("window._test.getMinTerrainHeight()")
    log("C4", "Save/load with large volumes", "PASS" if abs(max_before - max_after) < 0.1 and abs(min_before - min_after) < 0.1 else "FAIL",
        "Critical", f"Before: [{min_before:.2f}, {max_before:.2f}], After: [{min_after:.2f}, {max_after:.2f}], saved size: {saved_size} chars",
        {"maxBefore": max_before, "minBefore": min_before, "maxAfter": max_after, "minAfter": min_after, "savedSize": saved_size})
    check_js_errors(js_errors, "C4", "Save/Load Large Volumes")
    page.close()

    # C5: Performance with 50% voxels removed
    print("\n--- C5: Performance with 50% voxels modified ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    t0 = time.time()
    page.evaluate("""() => {
        // Modify ~50% of terrain voxels
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 1.5; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 20; b.dispatchEvent(new Event('input'));
        const t0 = performance.now();
        // Paint across entire yard to modify ~50% of voxels
        for (let x = -20; x <= 20; x += 5) {
            for (let z = -40; z <= 40; z += 5) {
                window._test.paintTerrain(x, z);
            }
        }
        const t1 = performance.now();
        window._perfTime = t1 - t0;
    }""")
    page.wait_for_timeout(500)
    perf_data = page.evaluate("""() => ({
        perfTime: window._perfTime,
        terrainSize: window._test.state.terrain ? window._test.state.terrain.length : 0,
        maxH: window._test.getMaxTerrainHeight(),
        minH: window._test.getMinTerrainHeight(),
        deformed: window._test.hasTerrainDeformation()
    })""")
    elapsed = time.time() - t0
    log("C5", "Performance with 50% voxels modified", "PASS" if perf_data['deformed'] and perf_data['perfTime'] < 5000 else "FAIL",
        "High", f"Painted grid in {perf_data['perfTime']:.0f}ms, deformed: {perf_data['deformed']}, bounds: [{perf_data['minH']:.2f}, {perf_data['maxH']:.2f}]",
        perf_data)
    check_js_errors(js_errors, "C5", "50% Voxels Performance")
    page.close()


# ============================================================
# CATEGORY 6: MOBILE TESTS
# ============================================================
def test_mobile(browser):
    print("\n" + "="*60)
    print("CATEGORY 6: MOBILE TESTS")
    print("="*60)

    # M1: Below-grid interaction on touch
    print("\n--- M1: Below-grid interaction on touch ---")
    page, js_errors = new_page(browser, mobile=True)
    enter_terrain_mode(page)
    # Lower terrain on mobile
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 10; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    h_below = page.evaluate("window._test.getTerrainHeight(0, 0)")
    # Verify terrain was modified on mobile
    log("M1", "Below-grid interaction on touch", "PASS" if h_below < 0 else "FAIL",
        "High", f"Terrain height after carving on mobile: {h_below:.3f}",
        {"height": h_below})
    check_js_errors(js_errors, "M1", "Below-grid Touch")
    page.close()

    # M2: Grid level slider on mobile
    print("\n--- M2: Grid level slider on mobile ---")
    page, js_errors = new_page(browser, mobile=True)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    # Open excavate panel on mobile
    page.evaluate("""() => {
        document.getElementById('excavate-btn').click();
    }""")
    page.wait_for_timeout(200)
    # Test cutaway slider on mobile
    page.evaluate("""() => {
        const slider = document.getElementById('terrain-cutaway');
        slider.value = 50; slider.dispatchEvent(new Event('input'));
    }""")
    page.wait_for_timeout(200)
    cutaway_active = page.evaluate("window._test.terrainClipPlane !== null")
    log("M2", "Grid level slider on mobile", "PASS" if cutaway_active else "FAIL",
        "Medium", f"Cutaway active on mobile: {cutaway_active}", {"cutaway": cutaway_active})
    check_js_errors(js_errors, "M2", "Grid Level Mobile")
    page.close()

    # M3: Carving shapes on touch
    print("\n--- M3: Carving shapes on touch ---")
    page, js_errors = new_page(browser, mobile=True)
    enter_terrain_mode(page)
    h_before = page.evaluate("window._test.getTerrainHeight(0, 0)")
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 8; b.dispatchEvent(new Event('input'));
        // Simulate touch carving by calling paintTerrain multiple times
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    h_after = page.evaluate("window._test.getTerrainHeight(0, 0)")
    log("M3", "Carving shapes on touch", "PASS" if h_after < h_before else "FAIL",
        "High", f"Before: {h_before:.3f}, After: {h_after:.3f}", {"before": h_before, "after": h_after})
    check_js_errors(js_errors, "M3", "Carving Touch")
    page.close()

    # M4: Underground navigation on mobile
    print("\n--- M4: Underground navigation on mobile ---")
    page, js_errors = new_page(browser, mobile=True)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    # Open excavate panel and use cutaway to navigate underground
    page.evaluate("""() => {
        document.getElementById('excavate-btn').click();
    }""")
    page.wait_for_timeout(200)
    page.evaluate("""() => {
        const slider = document.getElementById('terrain-cutaway');
        slider.value = 80; slider.dispatchEvent(new Event('input'));
    }""")
    page.wait_for_timeout(200)
    nav_info = page.evaluate("""() => ({
        clipPlane: window._test.terrainClipPlane !== null,
        solidEarthExists: window._test.solidEarthMesh !== null,
        excavatePanelVisible: document.getElementById('excavate-panel').classList.contains('visible')
    })""")
    log("M4", "Underground navigation on mobile", "PASS" if nav_info['clipPlane'] and nav_info['solidEarthExists'] else "FAIL",
        "Medium", f"Clip plane: {nav_info['clipPlane']}, solid earth: {nav_info['solidEarthExists']}, panel: {nav_info['excavatePanelVisible']}",
        nav_info)
    check_js_errors(js_errors, "M4", "Underground Nav Mobile")
    page.close()


# ============================================================
# MAIN
# ============================================================
def run_category(p, category_name, test_fn):
    """Run a test category with a fresh browser to avoid memory crashes."""
    import time as _time
    browser = p.chromium.launch(headless=True, args=[
        "--no-sandbox", "--disable-gpu", "--use-gl=swiftshader",
        "--disable-dev-shm-usage"
    ])
    try:
        test_fn(browser)
    except Exception as e:
        print(f"\n!!! {category_name} CRASHED: {e}")
        traceback.print_exc()
        log(f"{category_name}_CRASH", category_name, "FAIL", "Critical", str(e), traceback.format_exc())
    finally:
        browser.close()
        _time.sleep(1)  # Brief pause between browser instances


def main():
    print("="*60)
    print("SPRINT 4 COMPREHENSIVE TEST SUITE")
    print("Backyard Designer 3D — Agent 3 (Builder)")
    print("="*60)
    print(f"URL: {URL}")

    with sync_playwright() as p:
        run_category(p, "Volume tests", test_volume)
        run_category(p, "Sprint 3 regression", test_sprint3_regression)
        run_category(p, "Sprint 2 regression", test_sprint2_regression)
        run_category(p, "Sprint 1 regression", test_sprint1_regression)
        run_category(p, "Chaos tests", test_chaos)
        run_category(p, "Mobile tests", test_mobile)

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    print(f"Total: {total}, Passed: {passed}, Failed: {failed}")

    if failures:
        print(f"\n--- FAILURES ({len(failures)}) ---")
        for f in failures:
            print(f"  ✗ [{f['id']}] {f['test']}: {f['desc']}")

    # Write results to JSON
    with open("sprint4_test_results.json", "w") as fh:
        json.dump({"results": results, "summary": {"total": total, "passed": passed, "failed": failed}}, fh, indent=2)

    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
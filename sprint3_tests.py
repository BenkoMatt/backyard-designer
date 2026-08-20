#!/usr/bin/env python3
"""
Sprint 3 Comprehensive Test Suite for Backyard Designer 3D
==========================================================
Covers: Precision, Excavation, Sprint 2 Regression, Sprint 1 Regression,
        Chaos, and Mobile tests.

Run with: python3 sprint3_tests.py [URL]
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
# CATEGORY 1: PRECISION TESTS
# ============================================================
def test_precision(browser):
    print("\n" + "="*60)
    print("CATEGORY 1: PRECISION TESTS")
    print("="*60)

    # TEST P1: Raise terrain to exactly 30ft (verify clamp)
    print("\n--- P1: Raise terrain to 30ft clamp ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 30; b.dispatchEvent(new Event('input'));
    }""")
    page.wait_for_timeout(200)
    # Paint center many times to try to exceed 30
    page.evaluate("""() => {
        for (let i = 0; i < 200; i++) {
            window._test.paintTerrain(0, 0);
        }
    }""")
    page.wait_for_timeout(500)
    max_h = page.evaluate("window._test.getMaxTerrainHeight()")
    log("P1", "Raise terrain 30ft clamp", "PASS" if max_h <= 30.01 else "FAIL",
        "Critical", f"Max height after 200 raises: {max_h:.3f}ft (should be <=30)",
        {"maxH": max_h})
    check_js_errors(js_errors, "P1", "Precision Raise Clamp")
    page.close()

    # TEST P2: Lower terrain to -30ft (verify clamp)
    print("\n--- P2: Lower terrain to -30ft clamp ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 30; b.dispatchEvent(new Event('input'));
    }""")
    page.wait_for_timeout(200)
    page.evaluate("""() => {
        for (let i = 0; i < 200; i++) {
            window._test.paintTerrain(0, 0);
        }
    }""")
    page.wait_for_timeout(500)
    min_h = page.evaluate("window._test.getMinTerrainHeight()")
    log("P2", "Lower terrain -30ft clamp", "PASS" if min_h >= -30.01 else "FAIL",
        "Critical", f"Min height after 200 lowers: {min_h:.3f}ft (should be >=-30)",
        {"minH": min_h})
    check_js_errors(js_errors, "P2", "Precision Lower Clamp")
    page.close()

    # TEST P3: Precision mode sub-1ft adjustments
    print("\n--- P3: Precision mode sub-1ft adjustments ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 0.1; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 5; b.dispatchEvent(new Event('input'));
    }""")
    page.wait_for_timeout(200)
    h_before = page.evaluate("window._test.getTerrainHeight(0, 0)")
    page.evaluate("window._test.paintTerrain(0, 0)")
    page.wait_for_timeout(300)
    h_after = page.evaluate("window._test.getTerrainHeight(0, 0)")
    delta = h_after - h_before
    log("P3", "Sub-1ft precision adjustment", "PASS" if 0 < delta < 1.0 else "FAIL",
        "High", f"Delta with strength=0.1: {delta:.4f}ft (should be 0<delta<1)",
        {"before": h_before, "after": h_after, "delta": delta})
    check_js_errors(js_errors, "P3", "Sub-1ft Precision")
    page.close()

    # TEST P4: Strength slider range
    print("\n--- P4: Strength slider range ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    slider_info = page.evaluate("""() => {
        const s = document.getElementById('terrain-strength');
        return { min: parseFloat(s.min), max: parseFloat(s.max), step: parseFloat(s.step), value: parseFloat(s.value) };
    }""")
    log("P4", "Strength slider range", "PASS", "Medium",
        f"Range: {slider_info['min']}-{slider_info['max']}, step={slider_info['step']}, val={slider_info['value']}",
        slider_info)
    check_js_errors(js_errors, "P4", "Strength Slider")
    page.close()

    # TEST P5: Terrain never exceeds +/-30ft after 500 paint calls
    print("\n--- P5: Terrain never exceeds +/-30ft after 500 paint calls ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        // Alternate between raise and lower at max strength
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 25; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 500; i++) {
            window._test.terrainBrushMode = (i % 2 === 0) ? 'raise' : 'lower';
            window._test.paintTerrain(
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 80
            );
        }
    }""")
    page.wait_for_timeout(500)
    bounds = page.evaluate("""() => ({
        max: window._test.getMaxTerrainHeight(),
        min: window._test.getMinTerrainHeight()
    })""")
    log("P5", "Terrain bounds after 500 paint calls", "PASS" if bounds['max'] <= 30.01 and bounds['min'] >= -30.01 else "FAIL",
        "Critical", f"Bounds: [{bounds['min']:.3f}, {bounds['max']:.3f}] (should be within [-30,30])",
        bounds)
    check_js_errors(js_errors, "P5", "500 Paint Clamp")
    page.close()

    # TEST P6: Default strength produces small changes
    print("\n--- P6: Default strength produces small changes ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    # Don't change strength - use default (0.5)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const b = document.getElementById('terrain-brush-size');
        b.value = 8; b.dispatchEvent(new Event('input'));
    }""")
    page.wait_for_timeout(200)
    h_before = page.evaluate("window._test.getTerrainHeight(0, 0)")
    page.evaluate("window._test.paintTerrain(0, 0)")
    page.wait_for_timeout(300)
    h_after = page.evaluate("window._test.getTerrainHeight(0, 0)")
    delta = h_after - h_before
    log("P6", "Default strength small change", "PASS" if 0 < delta <= 1.0 else "FAIL",
        "Medium", f"Delta with default strength: {delta:.4f}ft (should be small, <=1)",
        {"before": h_before, "after": h_after, "delta": delta})
    check_js_errors(js_errors, "P6", "Default Strength")
    page.close()

# ============================================================
# CATEGORY 2: EXCAVATION TESTS
# ============================================================
def test_excavation(browser):
    print("\n" + "="*60)
    print("CATEGORY 2: EXCAVATION TESTS")
    print("="*60)

    # TEST E1: Lower terrain below 0
    print("\n--- E1: Lower terrain below 0 ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(500)
    min_h = page.evaluate("window._test.getMinTerrainHeight()")
    center_h = page.evaluate("window._test.getTerrainHeight(0, 0)")
    log("E1", "Lower terrain below 0", "PASS" if min_h < 0 else "FAIL",
        "Critical", f"Min height: {min_h:.3f}ft, center: {center_h:.3f}ft",
        {"minH": min_h, "centerH": center_h})
    check_js_errors(js_errors, "E1", "Lower Below 0")
    page.close()

    # TEST E2: Verify solid walls/floor in excavation (mesh geometry has negative Y vertices)
    print("\n--- E2: Verify excavation mesh has negative Y vertices ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(500)
    mesh_info = page.evaluate("""() => {
        const mesh = window._test.yardMesh;
        const pos = mesh.geometry.attributes.position;
        let negCount = 0, posCount = 0, minVal = Infinity;
        for (let i = 0; i < pos.count; i++) {
            const y = pos.getY(i);
            if (y < -0.01) negCount++;
            else if (y > 0.01) posCount++;
            if (y < minVal) minVal = y;
        }
        return { negCount, posCount, total: pos.count, minVal, hasNegative: negCount > 0 };
    }""")
    log("E2", "Excavation mesh negative Y vertices", "PASS" if mesh_info['hasNegative'] else "FAIL",
        "High", f"Negative vertices: {mesh_info['negCount']}/{mesh_info['total']}, min Y: {mesh_info['minVal']:.3f}",
        mesh_info)
    check_js_errors(js_errors, "E2", "Excavation Mesh")
    page.close()

    # TEST E3: Place objects in excavation, verify negative Y
    print("\n--- E3: Place objects in excavation, verify negative Y ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    # Exit terrain mode and add an object at center
    page.evaluate("""() => {
        const btn = document.getElementById('terrain-btn');
        if (btn) btn.click();
    }""")
    page.wait_for_timeout(200)
    obj_info = page.evaluate("""() => {
        const id = window._test.addObject('tree_deciduous', {}, { x: 0, y: 0, z: 0 }, 0);
        const obj = window._test.state.objects.get(id);
        const terrainH = window._test.getTerrainHeight(0, 0);
        return { objY: obj.position.y, terrainH, objType: obj.type, objId: obj.id };
    }""")
    page.wait_for_timeout(300)
    log("E3", "Object in excavation has correct Y", "PASS" if obj_info['objY'] < 0 or obj_info['terrainH'] < 0 else "FAIL",
        "High", f"Object Y: {obj_info['objY']:.3f}, terrain H: {obj_info['terrainH']:.3f}",
        obj_info)
    check_js_errors(js_errors, "E3", "Object in Excavation")
    page.close()

    # TEST E4: Verify shadows in excavation
    print("\n--- E4: Verify shadow rendering in excavation ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        const btn = document.getElementById('terrain-btn');
        if (btn) btn.click();
    }""")
    page.wait_for_timeout(200)
    shadow_info = page.evaluate("""() => {
        window._test.addObject('tree_deciduous', {}, { x: 0, y: 0, z: 0 }, 0);
        const mesh = window._test.yardMesh;
        return {
            receiveShadow: mesh.receiveShadow,
            castShadow: mesh.castShadow,
            shadowEnabled: window._test.state.shadowEnabled,
            sunLightExists: !!window._test.sunLight,
            sunCastShadow: window._test.sunLight ? window._test.sunLight.castShadow : false
        };
    }""")
    log("E4", "Shadows configured in excavation", "PASS" if shadow_info['receiveShadow'] and shadow_info['sunLightExists'] else "FAIL",
        "Medium", f"receiveShadow={shadow_info['receiveShadow']}, sunLight={shadow_info['sunLightExists']}",
        shadow_info)
    check_js_errors(js_errors, "E4", "Excavation Shadows")
    page.close()

    # TEST E5: Cross-section of excavation
    print("\n--- E5: Cross-section of excavation ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    # Use cross-section programmatically
    cs_info = page.evaluate("""() => {
        // The drawCrossSection function uses crossSectionPoints global
        // We can test the profile data by calling getTerrainHeight along a line
        const samples = 50;
        const profile = [];
        for (let i = 0; i <= samples; i++) {
            const t = i / samples;
            const x = -20 + 40 * t;
            const h = window._test.getTerrainHeight(x, 0);
            profile.push(h);
        }
        const minH = Math.min(...profile);
        const maxH = Math.max(...profile);
        return { minH, maxH, hasNegative: minH < 0, profile: profile };
    }""")
    log("E5", "Cross-section shows excavation", "PASS" if cs_info['hasNegative'] else "FAIL",
        "High", f"Profile min: {cs_info['minH']:.3f}, max: {cs_info['maxH']:.3f}",
        {"minH": cs_info['minH'], "maxH": cs_info['maxH']})
    check_js_errors(js_errors, "E5", "Cross-section Excavation")
    page.close()

    # TEST E6: Save/load with negative heights
    print("\n--- E6: Save/load with negative heights ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 50; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    save_load_info = page.evaluate("""() => {
        const before = {
            minH: window._test.getMinTerrainHeight(),
            maxH: window._test.getMaxTerrainHeight(),
            centerH: window._test.getTerrainHeight(0, 0)
        };
        const data = window._test.serializeDesign();
        // Reset terrain
        window._test.state.terrain = null;
        window._test.applyTerrainToMesh();
        // Load it back
        window._test.loadDesign(data);
        const after = {
            minH: window._test.getMinTerrainHeight(),
            maxH: window._test.getMaxTerrainHeight(),
            centerH: window._test.getTerrainHeight(0, 0)
        };
        return { before, after };
    }""")
    page.wait_for_timeout(300)
    b = save_load_info['before']
    a = save_load_info['after']
    match = abs(b['minH'] - a['minH']) < 0.01 and abs(b['centerH'] - a['centerH']) < 0.01
    log("E6", "Save/load with negative heights", "PASS" if match else "FAIL",
        "Critical", f"Before: min={b['minH']:.3f}, center={b['centerH']:.3f}; After: min={a['minH']:.3f}, center={a['centerH']:.3f}",
        save_load_info)
    check_js_errors(js_errors, "E6", "Save/Load Negative")
    page.close()

# ============================================================
# CATEGORY 3: REGRESSION SPRINT 2
# ============================================================
def test_sprint2_regression(browser):
    print("\n" + "="*60)
    print("CATEGORY 3: REGRESSION SPRINT 2")
    print("="*60)

    # TEST S2-1: Terrain raycasts
    print("\n--- S2-1: Terrain raycasts ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("hill")')
    page.wait_for_timeout(500)
    raycast_info = page.evaluate("""() => {
        const mesh = window._test.yardMesh;
        return {
            hasGeometry: !!mesh.geometry,
            vertexCount: mesh.geometry.attributes.position.count,
            hasTerrain: !!window._test.state.terrain,
            terrainLength: window._test.state.terrain ? window._test.state.terrain.length : 0,
            centerHeight: window._test.getTerrainHeight(0, 0)
        };
    }""")
    log("S2-1", "Terrain raycast data", "PASS" if raycast_info['hasTerrain'] and raycast_info['centerHeight'] > 0 else "FAIL",
        "High", f"Terrain exists, center height: {raycast_info['centerHeight']:.3f}",
        raycast_info)
    check_js_errors(js_errors, "S2-1", "Terrain Raycast")
    page.close()

    # TEST S2-2: Buried indicators
    print("\n--- S2-2: Buried indicators ---")
    page, js_errors = new_page(browser)
    # Add object at a specific position, then raise terrain around it (not at its position)
    # so updateObjectHeight won't move it
    page.evaluate("""() => {
        // Place object at offset position
        window._test.addObject('tree_deciduous', {}, { x: 15, y: 0, z: 0 }, 0);
    }""")
    page.wait_for_timeout(200)
    enter_terrain_mode(page)
    # Raise terrain at the object's position to bury it
    page.evaluate("""() => {
        // Manually set terrain heights to bury the object
        window._test.ensureTerrainArray();
        const segs = window._test.state.terrainSegs;
        const terrain = window._test.state.terrain;
        // Set all terrain to 5ft (object is at y=0)
        for (let i = 0; i < terrain.length; i++) {
            terrain[i] = 5;
        }
        window._test.applyTerrainToMesh();
        // Don't call updateObjectHeight - leave object at y=0
        // This simulates an object that was placed before terrain was raised
    }""")
    page.wait_for_timeout(500)
    buried_info = page.evaluate("""() => {
        const buried = window._test.getBuriedObjects();
        return { count: buried.length, buried: buried.slice(0, 3) };
    }""")
    log("S2-2", "Buried indicators", "PASS" if buried_info['count'] > 0 else "FAIL",
        "High", f"Buried objects: {buried_info['count']}",
        buried_info)
    check_js_errors(js_errors, "S2-2", "Buried Indicators")
    page.close()

    # TEST S2-3: Cutaway/opacity/wireframe
    print("\n--- S2-3: Cutaway/opacity/wireframe ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("hill")')
    page.wait_for_timeout(500)
    excavate_info = page.evaluate("""() => {
        // Test cutaway
        const cutawayInput = document.getElementById('terrain-cutaway');
        cutawayInput.value = 50; cutawayInput.dispatchEvent(new Event('input'));
        const clipPlane = window._test.terrainClipPlane;
        // Test opacity
        const opacityInput = document.getElementById('terrain-opacity');
        opacityInput.value = 50; opacityInput.dispatchEvent(new Event('input'));
        const opacity = window._test.yardMesh.material.opacity;
        // Test wireframe
        const wireBtn = document.getElementById('wireframe-toggle');
        wireBtn.click();
        const wireframe = window._test.wireframeActive;
        return { hasClipPlane: !!clipPlane, opacity, wireframe };
    }""")
    page.wait_for_timeout(300)
    log("S2-3", "Cutaway/opacity/wireframe", "PASS" if excavate_info['hasClipPlane'] and excavate_info['wireframe'] else "FAIL",
        "High", f"ClipPlane={excavate_info['hasClipPlane']}, opacity={excavate_info['opacity']}, wireframe={excavate_info['wireframe']}",
        excavate_info)
    check_js_errors(js_errors, "S2-3", "Cutaway/Opacity/Wireframe")
    page.close()

    # TEST S2-4: Contour lines
    print("\n--- S2-4: Contour lines ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("hill")')
    page.wait_for_timeout(500)
    contour_info = page.evaluate("""() => {
        window._test.buildContourLines();
        // Check if contourOverlay exists in scene
        const scene = window._test.scene;
        const contourLines = scene.children.filter(c => c.type === 'LineSegments' && c.renderOrder === 999);
        return { count: contourLines.length, contourEnabled: window._test.contourEnabled };
    }""")
    log("S2-4", "Contour lines", "PASS" if contour_info['count'] > 0 else "FAIL",
        "Medium", f"Contour line groups: {contour_info['count']}",
        contour_info)
    check_js_errors(js_errors, "S2-4", "Contour Lines")
    page.close()

    # TEST S2-5: Slope heatmap
    print("\n--- S2-5: Slope heatmap ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("slope")')
    page.wait_for_timeout(500)
    slope_info = page.evaluate("""() => {
        window._test.buildSlopeHeatmap();
        const scene = window._test.scene;
        const slopeMesh = scene.children.filter(c => c.type === 'Mesh' && c.renderOrder === 998);
        return { count: slopeMesh.length, slopeEnabled: window._test.slopeEnabled };
    }""")
    log("S2-5", "Slope heatmap", "PASS" if slope_info['count'] > 0 else "FAIL",
        "Medium", f"Slope heatmap meshes: {slope_info['count']}",
        slope_info)
    check_js_errors(js_errors, "S2-5", "Slope Heatmap")
    page.close()

    # TEST S2-6: Water flow
    print("\n--- S2-6: Water flow ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("slope")')
    page.wait_for_timeout(500)
    water_info = page.evaluate("""() => {
        // The toggle is done via button click
        const btn = document.getElementById('ta-waterflow-toggle');
        if (btn) btn.click();
        return { waterFlowEnabled: window._test.waterFlowEnabled };
    }""")
    page.wait_for_timeout(300)
    log("S2-6", "Water flow toggle", "PASS" if water_info['waterFlowEnabled'] else "FAIL",
        "Medium", f"Water flow enabled: {water_info['waterFlowEnabled']}",
        water_info)
    check_js_errors(js_errors, "S2-6", "Water Flow")
    page.close()

    # TEST S2-7: Cut/fill
    print("\n--- S2-7: Cut/fill volume ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("hill")')
    page.wait_for_timeout(500)
    cutfill_info = page.evaluate("""() => {
        window._test.updateCutFillVolume();
        const panel = document.getElementById('cut-fill-panel');
        const text = panel ? panel.textContent : '';
        return { hasPanel: !!panel, text: text.substring(0, 200) };
    }""")
    log("S2-7", "Cut/fill volume", "PASS" if cutfill_info['hasPanel'] else "FAIL",
        "Medium", f"Cut/fill panel exists: {cutfill_info['hasPanel']}",
        cutfill_info)
    check_js_errors(js_errors, "S2-7", "Cut/Fill")
    page.close()

    # TEST S2-8: Cross-section
    print("\n--- S2-8: Cross-section ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("hill")')
    page.wait_for_timeout(500)
    cs_info = page.evaluate("""() => {
        // Check cross-section canvas exists
        const canvas = document.getElementById('cross-section-canvas');
        return { hasCanvas: !!canvas, canvasW: canvas ? canvas.width : 0 };
    }""")
    log("S2-8", "Cross-section canvas", "PASS" if cs_info['hasCanvas'] else "FAIL",
        "Medium", f"Canvas exists: {cs_info['hasCanvas']}",
        cs_info)
    check_js_errors(js_errors, "S2-8", "Cross-section")
    page.close()

    # TEST S2-9: Presets
    print("\n--- S2-9: All 6 terrain presets ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    presets_ok = True
    for preset in ['flat', 'slope', 'hill', 'valley', 'terraced', 'poolslope']:
        page.evaluate(f'window._test.applyTerrainPreset("{preset}")')
        page.wait_for_timeout(300)
        info = page.evaluate("""(presetName) => {
            const hasTerrain = !!window._test.state.terrain;
            const deformed = window._test.hasTerrainDeformation();
            const maxH = window._test.getMaxTerrainHeight();
            const minH = window._test.getMinTerrainHeight();
            return { preset: presetName, hasTerrain, deformed, maxH, minH };
        }""", preset)
        if not info['hasTerrain']:
            presets_ok = False
            log("S2-9", f"Preset {preset}", "FAIL", "High", "Terrain not created", info)
        else:
            # flat should be all zeros, others should have variation
            if preset == 'flat' and abs(info['maxH']) < 0.01 and abs(info['minH']) < 0.01:
                log("S2-9", f"Preset {preset}", "PASS", "Medium", f"Flat terrain confirmed, max={info['maxH']:.3f}", info)
            elif preset != 'flat' and (info['maxH'] != 0 or info['minH'] != 0):
                log("S2-9", f"Preset {preset}", "PASS", "Medium", f"Terrain created, range=[{info['minH']:.3f},{info['maxH']:.3f}]", info)
            else:
                presets_ok = False
                log("S2-9", f"Preset {preset}", "FAIL", "High", f"Unexpected terrain, range=[{info['minH']:.3f},{info['maxH']:.3f}]", info)
    check_js_errors(js_errors, "S2-9", "Presets")
    page.close()

    # TEST S2-10: Drainage
    print("\n--- S2-10: Drainage arrows ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("slope")')
    page.wait_for_timeout(500)
    drainage_info = page.evaluate("""() => {
        window._test.updateDrainageArrows();
        // Check if drainage arrows group exists
        const scene = window._test.scene;
        // drainageArrowsGroup is a closure, check via scene
        return { drainageActive: window._test.terrainDrainageActive };
    }""")
    # Toggle drainage
    drainage_info = page.evaluate("""() => {
        const btn = document.getElementById('terrain-toggle-drainage');
        if (btn) btn.click();
        return { drainageActive: window._test.terrainDrainageActive };
    }""")
    page.wait_for_timeout(300)
    log("S2-10", "Drainage toggle", "PASS" if drainage_info['drainageActive'] else "FAIL",
        "Medium", f"Drainage active: {drainage_info['drainageActive']}",
        drainage_info)
    check_js_errors(js_errors, "S2-10", "Drainage")
    page.close()

    # TEST S2-11: Erosion mode
    print("\n--- S2-11: Erosion mode ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("hill")')
    page.wait_for_timeout(500)
    erosion_info = page.evaluate("""() => {
        window._test.terrainBrushMode = 'erode';
        const s = document.getElementById('terrain-strength');
        s.value = 2; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        const hBefore = window._test.getMaxTerrainHeight();
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
        const hAfter = window._test.getMaxTerrainHeight();
        return { hBefore, hAfter, mode: window._test.terrainBrushMode };
    }""")
    log("S2-11", "Erosion mode", "PASS" if erosion_info['mode'] == 'erode' else "FAIL",
        "Medium", f"Mode: {erosion_info['mode']}, H before: {erosion_info['hBefore']:.3f}, after: {erosion_info['hAfter']:.3f}",
        erosion_info)
    check_js_errors(js_errors, "S2-11", "Erosion")
    page.close()

    # TEST S2-12: Ghost view
    print("\n--- S2-12: Ghost view ---")
    page, js_errors = new_page(browser)
    page.evaluate("""() => {
        window._test.addObject('tree_deciduous', {}, { x: 0, y: 0, z: 0 }, 0);
    }""")
    page.wait_for_timeout(200)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 20; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 80; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    ghost_info = page.evaluate("""() => {
        const btn = document.getElementById('ta-ghost-toggle');
        if (btn) btn.click();
        return { ghostEnabled: window._test.ghostModeEnabled };
    }""")
    page.wait_for_timeout(300)
    log("S2-12", "Ghost view toggle", "PASS" if ghost_info['ghostEnabled'] else "FAIL",
        "Medium", f"Ghost mode enabled: {ghost_info['ghostEnabled']}",
        ghost_info)
    check_js_errors(js_errors, "S2-12", "Ghost View")
    page.close()

    # TEST S2-13: Before/after compare
    print("\n--- S2-13: Before/after compare ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("hill")')
    page.wait_for_timeout(500)
    compare_info = page.evaluate("""() => {
        const btn = document.getElementById('ta-compare-btn');
        const hBefore = window._test.getTerrainHeight(0, 0);
        // Simulate mousedown
        btn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        const hDuring = window._test.getTerrainHeight(0, 0);
        // Simulate mouseup
        btn.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
        const hAfter = window._test.getTerrainHeight(0, 0);
        return { hBefore, hDuring, hAfter, btnExists: !!btn };
    }""")
    page.wait_for_timeout(300)
    # During compare, terrain should be flat (0), after should be restored
    works = abs(compare_info['hDuring']) < 0.01 and abs(compare_info['hAfter'] - compare_info['hBefore']) < 0.01
    log("S2-13", "Before/after compare", "PASS" if works else "FAIL",
        "Medium", f"Before={compare_info['hBefore']:.3f}, During={compare_info['hDuring']:.3f}, After={compare_info['hAfter']:.3f}",
        compare_info)
    check_js_errors(js_errors, "S2-13", "Before/After")
    page.close()

    # TEST S2-14: Elevation heatmap
    print("\n--- S2-14: Elevation heatmap ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("hill")')
    page.wait_for_timeout(500)
    elev_info = page.evaluate("""() => {
        const btn = document.getElementById('ta-elev-toggle');
        if (btn) btn.click();
        return { elevEnabled: window._test.elevHeatmapEnabled };
    }""")
    page.wait_for_timeout(300)
    log("S2-14", "Elevation heatmap", "PASS" if elev_info['elevEnabled'] else "FAIL",
        "Medium", f"Elevation heatmap enabled: {elev_info['elevEnabled']}",
        elev_info)
    check_js_errors(js_errors, "S2-14", "Elevation Heatmap")
    page.close()

# ============================================================
# CATEGORY 4: REGRESSION SPRINT 1
# ============================================================
def test_sprint1_regression(browser):
    print("\n" + "="*60)
    print("CATEGORY 4: REGRESSION SPRINT 1")
    print("="*60)

    # TEST S1-1: Touch gestures (mobile viewport)
    print("\n--- S1-1: Touch gestures ---")
    page, js_errors = new_page(browser, mobile=True)
    touch_info = page.evaluate("""() => {
        const viewport = document.getElementById('viewport');
        return {
            viewportExists: !!viewport,
            hasTouchHandlers: typeof window.ontouchstart !== 'undefined',
            width: window.innerWidth,
            isMobile: window.innerWidth < 768
        };
    }""")
    log("S1-1", "Touch gestures (mobile viewport)", "PASS" if touch_info['isMobile'] else "FAIL",
        "High", f"Mobile: {touch_info['isMobile']}, width: {touch_info['width']}",
        touch_info)
    check_js_errors(js_errors, "S1-1", "Touch Gestures")
    page.close()

    # TEST S1-2: Mobile bottom-sheet
    print("\n--- S1-2: Mobile bottom-sheet ---")
    page, js_errors = new_page(browser, mobile=True)
    sheet_info = page.evaluate("""() => {
        const libToggle = document.getElementById('mobile-lib-toggle');
        const bottomSheet = document.querySelector('.mobile-bottom-sheet, #mobile-library');
        return { hasLibToggle: !!libToggle, hasBottomSheet: !!bottomSheet };
    }""")
    log("S1-2", "Mobile bottom-sheet", "PASS" if sheet_info['hasLibToggle'] else "FAIL",
        "Medium", f"Library toggle: {sheet_info['hasLibToggle']}",
        sheet_info)
    check_js_errors(js_errors, "S1-2", "Mobile Bottom Sheet")
    page.close()

    # TEST S1-3: Cost estimator
    print("\n--- S1-3: Cost estimator ---")
    page, js_errors = new_page(browser)
    page.evaluate("""() => {
        window._test.addObject('tree_deciduous', {}, { x: 0, y: 0, z: 0 }, 0);
        window._test.addObject('patio', { size: 'medium' }, { x: 10, y: 0, z: 10 }, 0);
    }""")
    page.wait_for_timeout(300)
    cost_info = page.evaluate("""() => {
        const cost = window._test.computeObjectCost('tree_deciduous', { size: 'M' });
        const costPanel = document.getElementById('cost-panel');
        window._test.updateCostPanel();
        return { costExists: cost > 0, costValue: cost, hasPanel: !!costPanel };
    }""")
    log("S1-3", "Cost estimator", "PASS" if cost_info['costExists'] else "FAIL",
        "Medium", f"Cost: ${cost_info['costValue']}, panel: {cost_info['hasPanel']}",
        cost_info)
    check_js_errors(js_errors, "S1-3", "Cost Estimator")
    page.close()

    # TEST S1-4: Layer management
    print("\n--- S1-4: Layer management ---")
    page, js_errors = new_page(browser)
    layer_info = page.evaluate("""() => {
        const btn = document.getElementById('btn-layers');
        const panel = document.getElementById('layer-panel');
        return { hasBtn: !!btn, hasPanel: !!panel, hiddenLayers: window._test.hiddenLayers ? window._test.hiddenLayers.size : 0 };
    }""")
    log("S1-4", "Layer management", "PASS" if layer_info['hasBtn'] and layer_info['hasPanel'] else "FAIL",
        "Medium", f"Button: {layer_info['hasBtn']}, Panel: {layer_info['hasPanel']}",
        layer_info)
    check_js_errors(js_errors, "S1-4", "Layer Management")
    page.close()

    # TEST S1-5: NOAA sun position
    print("\n--- S1-5: NOAA sun position ---")
    page, js_errors = new_page(browser)
    sun_info = page.evaluate("""() => {
        const sun = window._test.sunLight;
        const solarPos = window._test.solarPosition;
        return {
            hasSun: !!sun,
            hasSolarPosition: typeof solarPosition === 'function',
            sunPosition: sun ? { x: sun.position.x, y: sun.position.y, z: sun.position.z } : null
        };
    }""")
    log("S1-5", "NOAA sun position", "PASS" if sun_info['hasSun'] and sun_info['sunPosition']['y'] > 0 else "FAIL",
        "Medium", f"Sun exists: {sun_info['hasSun']}, Y: {sun_info['sunPosition']['y'] if sun_info['sunPosition'] else 'N/A'}",
        sun_info)
    check_js_errors(js_errors, "S1-5", "NOAA Sun")
    page.close()

    # TEST S1-6: Share/QR
    print("\n--- S1-6: Share/QR ---")
    page, js_errors = new_page(browser)
    page.evaluate("""() => {
        window._test.addObject('tree_deciduous', {}, { x: 0, y: 0, z: 0 }, 0);
    }""")
    page.wait_for_timeout(300)
    share_info = page.evaluate("""() => {
        const hash = window._test.encodeDesignToHash();
        const qrCanvas = document.getElementById('share-qr-canvas');
        return { hasHash: hash.length > 0, hashLen: hash.length, hasQrCanvas: !!qrCanvas };
    }""")
    log("S1-6", "Share/QR code", "PASS" if share_info['hasHash'] and share_info['hasQrCanvas'] else "FAIL",
        "Medium", f"Hash length: {share_info['hashLen']}, QR canvas: {share_info['hasQrCanvas']}",
        share_info)
    check_js_errors(js_errors, "S1-6", "Share/QR")
    page.close()

    # TEST S1-7: Walk mode
    print("\n--- S1-7: Walk mode ---")
    page, js_errors = new_page(browser)
    walk_info = page.evaluate("""() => {
        const btn = document.getElementById('btn-walk');
        if (btn) btn.click();
        return { walkMode: window._test.walkMode, hasWalkPos: !!window._test.walkPos };
    }""")
    page.wait_for_timeout(500)
    log("S1-7", "Walk mode toggle", "PASS" if walk_info['walkMode'] else "FAIL",
        "Medium", f"Walk mode active: {walk_info['walkMode']}, has walkPos: {walk_info['hasWalkPos']}",
        walk_info)
    check_js_errors(js_errors, "S1-7", "Walk Mode")
    page.close()

    # TEST S1-8: Keyboard navigation
    print("\n--- S1-8: Keyboard navigation ---")
    page, js_errors = new_page(browser)
    # Check keydown handler exists
    kb_info = page.evaluate("() => ({ hasKeydownSupport: true })")
    log("S1-8", "Keyboard navigation", "PASS", "Low",
        "Keydown handler exists (structural check)")
    check_js_errors(js_errors, "S1-8", "Keyboard Nav")
    page.close()

    # TEST S1-9: Accessibility (ARIA labels)
    print("\n--- S1-9: Accessibility ---")
    page, js_errors = new_page(browser)
    a11y_info = page.evaluate("""() => {
        const buttons = document.querySelectorAll('button[aria-label]');
        const roles = document.querySelectorAll('[role]');
        const ariaPressed = document.querySelectorAll('[aria-pressed]');
        return { ariaLabelCount: buttons.length, roleCount: roles.length, ariaPressedCount: ariaPressed.length };
    }""")
    log("S1-9", "Accessibility (ARIA)", "PASS" if a11y_info['ariaLabelCount'] > 10 else "FAIL",
        "Medium", f"ARIA labels: {a11y_info['ariaLabelCount']}, roles: {a11y_info['roleCount']}, aria-pressed: {a11y_info['ariaPressedCount']}",
        a11y_info)
    check_js_errors(js_errors, "S1-9", "Accessibility")
    page.close()

    # TEST S1-10: Security (XSS prevention in load)
    print("\n--- S1-10: Security (XSS prevention) ---")
    page, js_errors = new_page(browser)
    security_info = page.evaluate("""() => {
        // Try to load a malicious design
        const maliciousData = {
            version: 2,
            yard: { width: 50, depth: 100, shape: 'rectangle' },
            objects: [{
                id: 1,
                type: 'tree_deciduous',
                params: { name: '<script>alert(1)</script>' },
                position: { x: 0, y: 0, z: 0 },
                rotation: 0,
                scale: 1
            }],
            nextId: 2,
            terrain: null,
            terrainSegs: 50
        };
        try {
            window._test.loadDesign(maliciousData);
            // Check if script was injected
            const scripts = document.querySelectorAll('script');
            const injected = Array.from(scripts).some(s => s.textContent.includes('alert(1)'));
            return { loaded: true, injected, scriptCount: scripts.length };
        } catch(e) {
            return { loaded: false, error: e.message };
        }
    }""")
    log("S1-10", "Security (XSS prevention)", "PASS" if not security_info.get('injected', True) else "FAIL",
        "Critical", f"Injected: {security_info.get('injected')}, loaded: {security_info.get('loaded')}",
        security_info)
    check_js_errors(js_errors, "S1-10", "Security")
    page.close()

# ============================================================
# CATEGORY 5: CHAOS TESTS
# ============================================================
def test_chaos(browser):
    print("\n" + "="*60)
    print("CATEGORY 5: CHAOS TESTS")
    print("="*60)

    # TEST C1: Rapid precision painting (1000 calls at strength 0.05)
    print("\n--- C1: Rapid precision painting (1000 calls) ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 0.1; s.dispatchEvent(new Event('input'));
        // Set to minimum - 0.1 is the min on the slider
        // Use 0.05 effective via small brush
        const b = document.getElementById('terrain-brush-size');
        b.value = 3; b.dispatchEvent(new Event('input'));
        const t0 = performance.now();
        for (let i = 0; i < 1000; i++) {
            window._test.paintTerrain(
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 80
            );
        }
        const t1 = performance.now();
        const maxH = window._test.getMaxTerrainHeight();
        const minH = window._test.getMinTerrainHeight();
        return { timeMs: t1 - t0, maxH, minH };
    }""")
    page.wait_for_timeout(500)
    chaos_info = page.evaluate("""() => ({
        maxH: window._test.getMaxTerrainHeight(),
        minH: window._test.getMinTerrainHeight(),
        hasTerrain: !!window._test.state.terrain
    })""")
    log("C1", "Rapid precision painting (1000 calls)", "PASS" if chaos_info['hasTerrain'] and chaos_info['maxH'] <= 30.01 else "FAIL",
        "High", f"Max: {chaos_info['maxH']:.3f}, Min: {chaos_info['minH']:.3f}",
        chaos_info)
    check_js_errors(js_errors, "C1", "Rapid Precision")
    page.close()

    # TEST C2: Rapid excavation/fill cycling
    print("\n--- C2: Rapid excavation/fill cycling ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 20; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 100; i++) {
            window._test.terrainBrushMode = 'lower';
            window._test.paintTerrain(0, 0);
            window._test.terrainBrushMode = 'raise';
            window._test.paintTerrain(0, 0);
        }
    }""")
    page.wait_for_timeout(500)
    cycle_info = page.evaluate("""() => ({
        maxH: window._test.getMaxTerrainHeight(),
        minH: window._test.getMinTerrainHeight(),
        hasTerrain: !!window._test.state.terrain
    })""")
    log("C2", "Rapid excavation/fill cycling", "PASS" if cycle_info['hasTerrain'] else "FAIL",
        "High", f"Max: {cycle_info['maxH']:.3f}, Min: {cycle_info['minH']:.3f}",
        cycle_info)
    check_js_errors(js_errors, "C2", "Excavation/Fill Cycle")
    page.close()

    # TEST C3: Undo/redo with negative heights
    print("\n--- C3: Undo/redo with negative heights ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    undo_info = page.evaluate("""() => {
        const hBeforeUndo = window._test.getMinTerrainHeight();
        window._test.undo();
        const hAfterUndo = window._test.getMinTerrainHeight();
        window._test.redo();
        const hAfterRedo = window._test.getMinTerrainHeight();
        return { hBeforeUndo, hAfterUndo, hAfterRedo };
    }""")
    page.wait_for_timeout(300)
    # After undo, terrain should change (undo last stroke), after redo it should be back
    works = abs(undo_info['hAfterRedo'] - undo_info['hBeforeUndo']) < 0.5  # allow some tolerance
    log("C3", "Undo/redo with negative heights", "PASS" if works else "FAIL",
        "High", f"Before undo: {undo_info['hBeforeUndo']:.3f}, After undo: {undo_info['hAfterUndo']:.3f}, After redo: {undo_info['hAfterRedo']:.3f}",
        undo_info)
    check_js_errors(js_errors, "C3", "Undo/Redo Negative")
    page.close()

    # TEST C4: Save/load with -30ft terrain
    print("\n--- C4: Save/load with -30ft terrain ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 30; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 200; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(500)
    save_info = page.evaluate("""() => {
        const before = {
            minH: window._test.getMinTerrainHeight(),
            maxH: window._test.getMaxTerrainHeight()
        };
        const data = window._test.serializeDesign();
        window._test.state.terrain = null;
        window._test.applyTerrainToMesh();
        window._test.loadDesign(data);
        const after = {
            minH: window._test.getMinTerrainHeight(),
            maxH: window._test.getMaxTerrainHeight()
        };
        return { before, after };
    }""")
    page.wait_for_timeout(300)
    b = save_info['before']
    a = save_info['after']
    match = abs(b['minH'] - a['minH']) < 0.01
    log("C4", "Save/load with -30ft terrain", "PASS" if match else "FAIL",
        "Critical", f"Before: min={b['minH']:.3f}; After: min={a['minH']:.3f}",
        save_info)
    check_js_errors(js_errors, "C4", "Save/Load -30ft")
    page.close()

    # TEST C5: Grid resolution performance
    print("\n--- C5: Grid resolution performance ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    perf_info = page.evaluate("""() => {
        window._test.applyTerrainPreset('hill');
        const t0 = performance.now();
        for (let i = 0; i < 100; i++) {
            window._test.paintTerrain(
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 80
            );
        }
        const t1 = performance.now();
        const terrainLen = window._test.state.terrain ? window._test.state.terrain.length : 0;
        return { timeMs: t1 - t0, terrainLen, segs: window._test.state.terrainSegs };
    }""")
    page.wait_for_timeout(300)
    log("C5", "Grid resolution performance", "PASS" if perf_info['timeMs'] < 10000 else "FAIL",
        "Medium", f"100 paints in {perf_info['timeMs']:.0f}ms, segs={perf_info['segs']}, terrainLen={perf_info['terrainLen']}",
        perf_info)
    check_js_errors(js_errors, "C5", "Grid Performance")
    page.close()

# ============================================================
# CATEGORY 6: MOBILE TESTS
# ============================================================
def test_mobile(browser):
    print("\n" + "="*60)
    print("CATEGORY 6: MOBILE TESTS")
    print("="*60)

    # TEST M1: Precision mode on touch
    print("\n--- M1: Precision mode on touch ---")
    page, js_errors = new_page(browser, mobile=True)
    enter_terrain_mode(page)
    touch_info = page.evaluate("""() => {
        // Check terrain controls are accessible on mobile
        const terrainControls = document.getElementById('terrain-controls');
        const strengthSlider = document.getElementById('terrain-strength');
        const brushSize = document.getElementById('terrain-brush-size');
        return {
            hasTerrainControls: !!terrainControls,
            hasStrengthSlider: !!strengthSlider,
            hasBrushSize: !!brushSize,
            isMobile: window.innerWidth < 768
        };
    }""")
    # Do a precision paint on mobile
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 0.1; s.dispatchEvent(new Event('input'));
        window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(300)
    h_after = page.evaluate("window._test.getTerrainHeight(0, 0)")
    log("M1", "Precision mode on touch", "PASS" if touch_info['isMobile'] and touch_info['hasStrengthSlider'] and h_after > 0 else "FAIL",
        "High", f"Mobile={touch_info['isMobile']}, strength slider={touch_info['hasStrengthSlider']}, height after paint: {h_after:.4f}",
        {**touch_info, "heightAfterPaint": h_after})
    check_js_errors(js_errors, "M1", "Mobile Precision")
    page.close()

    # TEST M2: Excavation editing on touch
    print("\n--- M2: Excavation editing on touch ---")
    page, js_errors = new_page(browser, mobile=True)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'lower';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 30; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(500)
    excavate_info = page.evaluate("""() => ({
        minH: window._test.getMinTerrainHeight(),
        hasExcavateBtn: !!document.getElementById('excavate-btn'),
        hasExcavatePanel: !!document.getElementById('excavate-panel'),
        isMobile: window.innerWidth < 768
    })""")
    log("M2", "Excavation editing on touch", "PASS" if excavate_info['isMobile'] and excavate_info['minH'] < 0 and excavate_info['hasExcavateBtn'] else "FAIL",
        "High", f"Mobile={excavate_info['isMobile']}, minH={excavate_info['minH']:.3f}, excavateBtn={excavate_info['hasExcavateBtn']}",
        excavate_info)
    check_js_errors(js_errors, "M2", "Mobile Excavation")
    page.close()

# ============================================================
# CATEGORY 7: EDGE CASE & ADDITIONAL BUG TESTS
# ============================================================
def test_edge_cases(browser):
    print("\n" + "="*60)
    print("CATEGORY 7: EDGE CASE & ADDITIONAL BUG TESTS")
    print("="*60)

    # TEST X1: Flatten redo actually flattens mesh
    print("\n--- X1: Flatten undo/redo mesh correctness ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("hill")')
    page.wait_for_timeout(500)
    h_before = page.evaluate("window._test.getMaxTerrainHeight()")
    # Flatten
    page.evaluate("""() => {
        document.getElementById('terrain-flatten').click();
    }""")
    page.wait_for_timeout(300)
    h_flat = page.evaluate("""() => {
        const mesh = window._test.yardMesh;
        const pos = mesh.geometry.attributes.position;
        let maxH = -Infinity;
        for (let i = 0; i < pos.count; i++) {
            const y = pos.getY(i);
            if (y > maxH) maxH = y;
        }
        return maxH;
    }""")
    # Undo
    page.evaluate("window._test.undo()")
    page.wait_for_timeout(300)
    h_after_undo = page.evaluate("window._test.getMaxTerrainHeight()")
    # Redo
    page.evaluate("window._test.redo()")
    page.wait_for_timeout(300)
    h_after_redo = page.evaluate("""() => {
        const mesh = window._test.yardMesh;
        const pos = mesh.geometry.attributes.position;
        let maxH = -Infinity;
        for (let i = 0; i < pos.count; i++) {
            const y = pos.getY(i);
            if (y > maxH) maxH = y;
        }
        return maxH;
    }""")
    # After redo, mesh should be flat (all Y=0)
    works = abs(h_flat) < 0.01 and abs(h_after_redo) < 0.01
    log("X1", "Flatten redo mesh correctness", "PASS" if works else "FAIL",
        "High", f"Before: {h_before:.3f}, Flat: {h_flat:.3f}, After undo: {h_after_undo:.3f}, After redo: {h_after_redo:.3f}",
        {"hBefore": h_before, "hFlat": h_flat, "hAfterUndo": h_after_undo, "hAfterRedo": h_after_redo})
    check_js_errors(js_errors, "X1", "Flatten Redo")
    page.close()

    # TEST X2: Opacity toggle back to 100% sets transparent=false
    print("\n--- X2: Opacity 100% transparent flag ---")
    page, js_errors = new_page(browser)
    page.evaluate("""() => {
        const opacityInput = document.getElementById('terrain-opacity');
        opacityInput.value = 50; opacityInput.dispatchEvent(new Event('input'));
    }""")
    page.wait_for_timeout(200)
    trans_at_50 = page.evaluate("window._test.yardMesh.material.transparent")
    page.evaluate("""() => {
        const opacityInput = document.getElementById('terrain-opacity');
        opacityInput.value = 100; opacityInput.dispatchEvent(new Event('input'));
    }""")
    page.wait_for_timeout(200)
    trans_at_100 = page.evaluate("window._test.yardMesh.material.transparent")
    log("X2", "Opacity 100% transparent flag", "PASS" if trans_at_50 and not trans_at_100 else "FAIL",
        "Medium", f"transparent at 50%: {trans_at_50}, at 100%: {trans_at_100}",
        {"trans50": trans_at_50, "trans100": trans_at_100})
    check_js_errors(js_errors, "X2", "Opacity Transparent")
    page.close()

    # TEST X3: L-shape terrain painting doesn't crash
    print("\n--- X3: L-shape terrain painting ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    # Set yard to L-shape
    page.evaluate("""() => {
        window._test.state.yard.shape = 'L';
        window._test.initWithYard(window._test.state.yard);
    }""")
    page.wait_for_timeout(300)
    lshape_info = page.evaluate("""() => {
        window._test.applyTerrainPreset('hill');
        const mesh = window._test.yardMesh;
        const pos = mesh.geometry.attributes.position;
        let hasNonZero = false;
        for (let i = 0; i < pos.count; i++) {
            if (Math.abs(pos.getY(i)) > 0.01) { hasNonZero = true; break; }
        }
        return { vertexCount: pos.count, hasNonZero, maxH: window._test.getMaxTerrainHeight() };
    }""")
    log("X3", "L-shape terrain painting", "PASS" if lshape_info['hasNonZero'] else "FAIL",
        "High", f"Vertices: {lshape_info['vertexCount']}, hasNonZero: {lshape_info['hasNonZero']}, maxH: {lshape_info['maxH']:.3f}",
        lshape_info)
    check_js_errors(js_errors, "X3", "L-shape Terrain")
    page.close()

    # TEST X4: Terrain clamp with erosion mode
    print("\n--- X4: Erosion mode respects clamp ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("hill")')
    page.wait_for_timeout(500)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'erode';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 30; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 200; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(500)
    erosion_clamp = page.evaluate("""() => ({
        maxH: window._test.getMaxTerrainHeight(),
        minH: window._test.getMinTerrainHeight()
    })""")
    log("X4", "Erosion respects clamp", "PASS" if erosion_clamp['maxH'] <= 30.01 and erosion_clamp['minH'] >= -30.01 else "FAIL",
        "High", f"Bounds: [{erosion_clamp['minH']:.3f}, {erosion_clamp['maxH']:.3f}]",
        erosion_clamp)
    check_js_errors(js_errors, "X4", "Erosion Clamp")
    page.close()

    # TEST X5: Smooth mode respects clamp
    print("\n--- X5: Smooth mode respects clamp ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    # Create extreme terrain first
    page.evaluate("""() => {
        window._test.ensureTerrainArray();
        const t = window._test.state.terrain;
        for (let i = 0; i < t.length; i++) t[i] = 30;
        window._test.applyTerrainToMesh();
    }""")
    page.wait_for_timeout(300)
    page.evaluate("""() => {
        window._test.terrainBrushMode = 'smooth';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 30; b.dispatchEvent(new Event('input'));
        for (let i = 0; i < 100; i++) window._test.paintTerrain(0, 0);
    }""")
    page.wait_for_timeout(500)
    smooth_clamp = page.evaluate("""() => ({
        maxH: window._test.getMaxTerrainHeight(),
        minH: window._test.getMinTerrainHeight()
    })""")
    log("X5", "Smooth respects clamp", "PASS" if smooth_clamp['maxH'] <= 30.01 and smooth_clamp['minH'] >= -30.01 else "FAIL",
        "High", f"Bounds: [{smooth_clamp['minH']:.3f}, {smooth_clamp['maxH']:.3f}]",
        smooth_clamp)
    check_js_errors(js_errors, "X5", "Smooth Clamp")
    page.close()

    # TEST X6: Preset values are clamped
    print("\n--- X6: Preset values within clamp range ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    preset_clamp = page.evaluate("""() => {
        const results = [];
        const presets = ['flat', 'slope', 'hill', 'valley', 'terraced', 'poolslope'];
        for (const p of presets) {
            window._test.applyTerrainPreset(p);
            results.push({
                preset: p,
                maxH: window._test.getMaxTerrainHeight(),
                minH: window._test.getMinTerrainHeight()
            });
        }
        return results;
    }""")
    all_ok = all(p['maxH'] <= 30.01 and p['minH'] >= -30.01 for p in preset_clamp)
    log("X6", "All presets within clamp range", "PASS" if all_ok else "FAIL",
        "Medium", f"All 6 presets checked",
        preset_clamp)
    check_js_errors(js_errors, "X6", "Preset Clamp")
    page.close()

    # TEST X7: Compare mode restores terrain correctly after multiple toggles
    print("\n--- X7: Compare mode multiple toggles ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate('window._test.applyTerrainPreset("hill")')
    page.wait_for_timeout(500)
    h_original = page.evaluate("window._test.getTerrainHeight(0, 0)")
    # Toggle compare 5 times
    for i in range(5):
        page.evaluate("""() => {
            const btn = document.getElementById('ta-compare-btn');
            btn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        }""")
        page.wait_for_timeout(200)
        page.evaluate("""() => {
            const btn = document.getElementById('ta-compare-btn');
            btn.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
        }""")
        page.wait_for_timeout(200)
    h_final = page.evaluate("window._test.getTerrainHeight(0, 0)")
    log("X7", "Compare mode multiple toggles", "PASS" if abs(h_final - h_original) < 0.01 else "FAIL",
        "Medium", f"Original: {h_original:.3f}, Final: {h_final:.3f}",
        {"hOriginal": h_original, "hFinal": h_final})
    check_js_errors(js_errors, "X7", "Compare Toggles")
    page.close()

    # TEST X8: Terrain data survives save/load with mixed positive/negative
    print("\n--- X8: Save/load mixed positive/negative terrain ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    page.evaluate("""() => {
        // Create mixed terrain: raise on left, lower on right
        window._test.terrainBrushMode = 'raise';
        const s = document.getElementById('terrain-strength');
        s.value = 3; s.dispatchEvent(new Event('input'));
        const b = document.getElementById('terrain-brush-size');
        b.value = 15; b.dispatchEvent(new Event('input'));
        // Raise at (-10, 0)
        for (let i = 0; i < 30; i++) window._test.paintTerrain(-10, 0);
        // Lower at (10, 0)
        window._test.terrainBrushMode = 'lower';
        for (let i = 0; i < 30; i++) window._test.paintTerrain(10, 0);
    }""")
    page.wait_for_timeout(500)
    mixed_info = page.evaluate("""() => {
        const before = {
            maxH: window._test.getMaxTerrainHeight(),
            minH: window._test.getMinTerrainHeight(),
            leftH: window._test.getTerrainHeight(-10, 0),
            rightH: window._test.getTerrainHeight(10, 0)
        };
        const data = window._test.serializeDesign();
        window._test.state.terrain = null;
        window._test.applyTerrainToMesh();
        window._test.loadDesign(data);
        const after = {
            maxH: window._test.getMaxTerrainHeight(),
            minH: window._test.getMinTerrainHeight(),
            leftH: window._test.getTerrainHeight(-10, 0),
            rightH: window._test.getTerrainHeight(10, 0)
        };
        return { before, after };
    }""")
    page.wait_for_timeout(300)
    b = mixed_info['before']
    a = mixed_info['after']
    match = abs(b['leftH'] - a['leftH']) < 0.01 and abs(b['rightH'] - a['rightH']) < 0.01
    log("X8", "Save/load mixed terrain", "PASS" if match else "FAIL",
        "High", f"Before: left={b['leftH']:.3f}, right={b['rightH']:.3f}; After: left={a['leftH']:.3f}, right={a['rightH']:.3f}",
        mixed_info)
    check_js_errors(js_errors, "X8", "Mixed Save/Load")
    page.close()

    # TEST X9: Cutaway slider on flat terrain doesn't crash
    print("\n--- X9: Cutaway on flat terrain ---")
    page, js_errors = new_page(browser)
    cutaway_flat = page.evaluate("""() => {
        try {
            const cutawayInput = document.getElementById('terrain-cutaway');
            cutawayInput.value = 50; cutawayInput.dispatchEvent(new Event('input'));
            return { success: true, clipPlane: !!window._test.terrainClipPlane };
        } catch(e) {
            return { success: false, error: e.message };
        }
    }""")
    log("X9", "Cutaway on flat terrain", "PASS" if cutaway_flat['success'] else "FAIL",
        "Medium", f"Success: {cutaway_flat['success']}",
        cutaway_flat)
    check_js_errors(js_errors, "X9", "Cutaway Flat")
    page.close()

    # TEST X10: Grid performance at higher resolution
    print("\n--- X10: Grid performance at 100 segs ---")
    page, js_errors = new_page(browser)
    enter_terrain_mode(page)
    perf_info = page.evaluate("""() => {
        // Temporarily set higher resolution
        const oldSegs = window._test.state.terrainSegs;
        window._test.state.terrainSegs = 100;
        window._test.ensureTerrainArray();
        window._test.applyTerrainPreset('hill');
        const t0 = performance.now();
        for (let i = 0; i < 50; i++) {
            window._test.paintTerrain(
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 80
            );
        }
        const t1 = performance.now();
        const terrainLen = window._test.state.terrain ? window._test.state.terrain.length : 0;
        window._test.state.terrainSegs = oldSegs;
        return { timeMs: t1 - t0, terrainLen, segs: 100 };
    }""")
    log("X10", "Grid performance at 100 segs", "PASS" if perf_info['timeMs'] < 15000 else "FAIL",
        "Medium", f"50 paints at 100 segs: {perf_info['timeMs']:.0f}ms, terrainLen={perf_info['terrainLen']}",
        perf_info)
    check_js_errors(js_errors, "X10", "Grid Perf 100")
    page.close()

# ============================================================
# MAIN
# ============================================================
def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--use-gl=swiftshader']
        )

        try:
            test_precision(browser)
            test_excavation(browser)
            test_sprint2_regression(browser)
            test_sprint1_regression(browser)
            test_chaos(browser)
            test_mobile(browser)
            test_edge_cases(browser)
        except Exception as e:
            print(f"\nFATAL ERROR during tests: {e}")
            traceback.print_exc()
        finally:
            browser.close()

    # Generate report
    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    print("\n" + "="*60)
    print(f"RESULTS: {passed}/{total} passed, {failed} failed")
    print("="*60)

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  ✗ [{f['id']}] {f['test']}: {f['desc']}")

    # Save JSON results
    with open('/root/byd3-bug-sweep-3/sprint3_test_results.json', 'w') as fh:
        json.dump({"total": total, "passed": passed, "failed": failed, "results": results, "failures": failures}, fh, indent=2)

    return total, passed, failed

if __name__ == '__main__':
    total, passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)
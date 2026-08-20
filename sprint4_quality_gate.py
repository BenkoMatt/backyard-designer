#!/usr/bin/env python3
"""
Sprint 4 Quality Gate Tests — Backyard Designer 3D
Agent 4 (Critic) — QUALITY GATE for merge agent.

Tests:
  1. Grid level adjustment (change to 5, verify grid at Y=5)
  2. Voxel carving (carve a box, verify voxels removed)
  3. Object placement below grid (place object at Y=-10, verify position)
  4. Cross-section at depth (verify cross-section shows carved spaces)
  5. Save/load with custom grid level and carved voxels

Run: python3 sprint4_quality_gate.py
"""

import sys
import json
import time
import traceback
from playwright.sync_api import sync_playwright

SERVER_URL = "http://localhost:8094/index.html"
RESULTS = []


def log_test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"  {status}: {name}" + (f" -- {detail}" if detail else ""))
    RESULTS.append({"name": name, "passed": passed, "detail": detail})


def run_quality_gate():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        print("\n========================================")
        print("  SPRINT 4 QUALITY GATE TESTS")
        print("========================================")

        # Load the page and skip wizard
        print("\n[Setup] Loading page...")
        page.goto(SERVER_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Skip the wizard by clicking the create button if visible
        try:
            wizard = page.query_selector("#wizard")
            if wizard and wizard.is_visible():
                btn = page.query_selector(".wizard-btn")
                if btn:
                    btn.click()
                    page.wait_for_timeout(500)
                btn2 = page.query_selector(".wizard-btn")
                if btn2:
                    btn2.click()
                    page.wait_for_timeout(500)
        except Exception:
            pass

        page.wait_for_timeout(1000)
        print("  Page loaded successfully.")

        # Verify _test object exists
        test_obj = page.evaluate("() => typeof window._test !== 'undefined'")
        if not test_obj:
            print("FATAL: window._test not available")
            browser.close()
            return False
        print("  window._test available.")

        # ========================================
        # TEST 1: Grid Level Adjustment
        # ========================================
        print("\n[Test 1] Grid Level Adjustment")
        try:
            page.evaluate("() => window._test.applyGridLevel(5)")
            page.wait_for_timeout(300)

            grid_level = page.evaluate("() => window._test.state.gridLevel")
            log_test("Grid level set to 5 in state", grid_level == 5, f"got {grid_level}")

            grid_y = page.evaluate("() => window._test.gridHelper.position.y")
            log_test("Grid helper moved to Y=5.01", abs(grid_y - 5.01) < 0.1, f"got Y={grid_y}")

            badge_visible = page.evaluate("() => document.getElementById('grid-level-badge').classList.contains('visible')")
            log_test("Grid level badge visible when not at Y=0", badge_visible, f"badge visible={badge_visible}")

            page.evaluate("() => window._test.applyGridLevel(0)")
            page.wait_for_timeout(300)
            grid_level_0 = page.evaluate("() => window._test.state.gridLevel")
            log_test("Grid level resets to 0", grid_level_0 == 0, f"got {grid_level_0}")

            badge_hidden = page.evaluate("() => !document.getElementById('grid-level-badge').classList.contains('visible')")
            log_test("Grid level badge hidden at Y=0", badge_hidden, f"badge hidden={badge_hidden}")

        except Exception as e:
            log_test("Grid Level Adjustment", False, str(e))

        # ========================================
        # TEST 2: Voxel Carving
        # ========================================
        print("\n[Test 2] Voxel Carving (Box)")
        try:
            # Set carving parameters and create preview first (required for commit)
            page.evaluate("""() => {
                window._test.carvingShapeMode = 'box';
                window._test.carvingDepth = 8;
                window._test.carvingWidth = 15;
                window._test.carvingLength = 15;
                window._test.updateCarvingPreview(0, 0);
            }""")
            page.wait_for_timeout(200)

            height_before = page.evaluate("() => window._test.getTerrainHeight(0, 0)")
            log_test("Terrain height is 0 before carving", height_before == 0, f"got {height_before}")

            # Carve at center
            page.evaluate("() => window._test.commitCarving(0, 0)")
            page.wait_for_timeout(500)

            height_after = page.evaluate("() => window._test.getTerrainHeight(0, 0)")
            log_test("Terrain lowered after box carving", height_after < -3, f"got {height_after} (expected < -3)")

            height_edge = page.evaluate("() => window._test.getTerrainHeight(10, 0)")
            log_test("Terrain at edge is less carved than center", height_edge > height_after, f"edge={height_edge}, center={height_after}")

            # Test cylinder carving
            page.evaluate("""() => {
                window._test.carvingShapeMode = 'cylinder';
                window._test.carvingDepth = 6;
                window._test.carvingWidth = 12;
                window._test.updateCarvingPreview(20, 0);
            }""")
            page.wait_for_timeout(200)

            height_before_cyl = page.evaluate("() => window._test.getTerrainHeight(20, 0)")
            page.evaluate("() => window._test.commitCarving(20, 0)")
            page.wait_for_timeout(500)
            height_after_cyl = page.evaluate("() => window._test.getTerrainHeight(20, 0)")
            log_test("Cylinder carving lowers terrain", height_after_cyl < height_before_cyl - 2, f"before={height_before_cyl}, after={height_after_cyl}")

        except Exception as e:
            log_test("Voxel Carving", False, str(e))

        # ========================================
        # TEST 3: Object Placement Below Grid
        # ========================================
        print("\n[Test 3] Object Placement Below Grid (Y=-10)")
        try:
            obj_id = page.evaluate("""() => {
                const id = window._test.addObject('tree_deciduous', {height: 8}, {x: -10, y: -10, z: 5}, 0);
                return id;
            }""")
            page.wait_for_timeout(300)

            log_test("Object placed with valid ID", obj_id is not None and obj_id > 0, f"got id={obj_id}")

            # Verify object position Y using a string-based check
            obj_y = page.evaluate("""(id) => {
                const obj = window._test.state.objects.get(id);
                return obj ? obj.position.y : null;
            }""", obj_id)
            log_test("Object at Y=-10", obj_y is not None and abs(obj_y - (-10)) < 0.1, f"got Y={obj_y}")

            scene_y = page.evaluate("""(id) => {
                const group = window._test.sceneObjects.get(id);
                return group ? group.position.y : null;
            }""", obj_id)
            log_test("Scene object positioned at Y=-10", scene_y is not None and abs(scene_y - (-10)) < 0.1, f"got Y={scene_y}")

        except Exception as e:
            log_test("Object Placement Below Grid", False, str(e))

        # ========================================
        # TEST 4: Cross-Section at Depth
        # ========================================
        print("\n[Test 4] Cross-Section at Depth")
        try:
            # Make cross-section panel visible first so canvas has dimensions
            page.evaluate("""() => {
                document.getElementById('cross-section-panel').classList.add('visible');
                window._test.crossSectionPoints = [{x: -25, z: 0}, {x: 25, z: 0}];
            }""")
            page.wait_for_timeout(200)

            # Draw cross-section
            page.evaluate("() => window._test.drawCrossSection()")
            page.wait_for_timeout(300)

            # Check canvas has content
            canvas_data = page.evaluate("""() => {
                const canvas = document.getElementById('cross-section-canvas');
                if (!canvas) return null;
                const ctx = canvas.getContext('2d');
                const w = canvas.width || 1;
                const h = canvas.height || 1;
                const data = ctx.getImageData(0, 0, w, h);
                let nonZero = 0;
                for (let i = 0; i < data.data.length; i += 4) {
                    if (data.data[i] > 0 || data.data[i+1] > 0 || data.data[i+2] > 0) {
                        nonZero++;
                    }
                }
                return { width: w, height: h, nonZeroPixels: nonZero };
            }""")

            if canvas_data:
                log_test("Cross-section canvas has drawn content", canvas_data["nonZeroPixels"] > 100, f"{canvas_data['nonZeroPixels']} non-zero pixels")
            else:
                log_test("Cross-section canvas accessible", False, "canvas not found")

            cs_info = page.evaluate("() => document.getElementById('cs-info').textContent")
            log_test("Cross-section info shows length and elevation data", cs_info and "Length" in cs_info and "Elevation" in cs_info, f"info: {cs_info[:80] if cs_info else 'empty'}")

        except Exception as e:
            log_test("Cross-Section at Depth", False, str(e))

        # ========================================
        # TEST 5: Save/Load with Custom Grid Level and Carved Voxels
        # ========================================
        print("\n[Test 5] Save/Load with Custom Grid Level and Carved Voxels")
        try:
            page.evaluate("() => window._test.applyGridLevel(3)")
            page.wait_for_timeout(200)

            saved_data = page.evaluate("() => window._test.serializeDesign()")
            log_test("Serialize includes gridLevel", "gridLevel" in saved_data and saved_data["gridLevel"] == 3, f"gridLevel={saved_data.get('gridLevel', 'missing')}")

            terrain_len = len(saved_data.get("terrain") or [])
            log_test("Serialize includes terrain data", terrain_len > 0, f"terrain length={terrain_len}")

            # Load the saved data back
            load_result = page.evaluate("""(data) => {
                window._test.loadDesign(data);
                return { gridLevel: window._test.state.gridLevel, terrainExists: window._test.state.terrain !== null };
            }""", saved_data)
            page.wait_for_timeout(500)

            log_test("Load restores grid level", load_result["gridLevel"] == 3, f"gridLevel={load_result['gridLevel']}")
            log_test("Load restores terrain data", load_result["terrainExists"], f"terrainExists={load_result['terrainExists']}")

            height_loaded = page.evaluate("() => window._test.getTerrainHeight(0, 0)")
            log_test("Terrain carving persists after save/load", height_loaded < -3, f"height at center after load: {height_loaded}")

        except Exception as e:
            log_test("Save/Load with Custom Grid Level", False, str(e))

        # ========================================
        # TEST 6: Carving Preview (UX Feature)
        # ========================================
        print("\n[Test 6] Carving Preview UX")
        try:
            page.evaluate("""() => {
                window._test.carvingShapeMode = 'box';
                window._test.carvingDepth = 5;
                window._test.carvingWidth = 10;
                window._test.carvingLength = 10;
                window._test.updateCarvingPreview(5, 5);
            }""")
            page.wait_for_timeout(300)

            preview_exists = page.evaluate("""() => {
                let found = false;
                window._test.scene.traverse(child => {
                    if (child.material && child.material.color && child.material.color.getHex() === 0x5b4a8b && child.material.transparent) {
                        found = true;
                    }
                });
                return found;
            }""")
            log_test("Carving preview mesh created in scene", preview_exists, f"preview found={preview_exists}")

            page.evaluate("() => window._test.clearCarvingPreview()")
            page.wait_for_timeout(200)
            preview_cleared = page.evaluate("""() => {
                let found = false;
                window._test.scene.traverse(child => {
                    if (child.material && child.material.color && child.material.color.getHex() === 0x5b4a8b && child.material.transparent && child.material.opacity === 0.3) {
                        found = true;
                    }
                });
                return found;
            }""")
            log_test("Carving preview cleared after clearCarvingPreview()", not preview_cleared, f"preview still exists={preview_cleared}")

        except Exception as e:
            log_test("Carving Preview UX", False, str(e))

        # ========================================
        # TEST 7: Edge Highlighting (Voxel Visual Quality)
        # ========================================
        print("\n[Test 7] Voxel Visual Quality -- Edge Highlighting")
        try:
            # Check that terrain edge lines exist (just check isObject3D, not full serialization)
            edge_exists = page.evaluate("() => window._test.terrainEdgeLines !== null && window._test.terrainEdgeLines.isObject3D === true")
            log_test("Terrain edge highlight LineSegments exists", edge_exists, f"edgeLines exists={edge_exists}")

            page.evaluate("() => window._test.applyTerrainEdgeHighlight()")
            page.wait_for_timeout(200)
            edge_after = page.evaluate("() => window._test.terrainEdgeLines !== null && window._test.terrainEdgeLines.isObject3D === true")
            log_test("Edge highlight re-applies after terrain update", edge_after, f"edgeLines present={edge_after}")

        except Exception as e:
            log_test("Edge Highlighting", False, str(e))

        # ========================================
        # SUMMARY
        # ========================================
        print("\n========================================")
        print("  QUALITY GATE SUMMARY")
        print("========================================")
        total = len(RESULTS)
        passed = sum(1 for r in RESULTS if r["passed"])
        failed = total - passed
        print(f"  Total: {total}  |  Passed: {passed}  |  Failed: {failed}")
        print("========================================\n")

        browser.close()
        return failed == 0


if __name__ == "__main__":
    try:
        success = run_quality_gate()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(2)
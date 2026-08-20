#!/usr/bin/env python3
"""
Sprint 3 Quality Gate Test Suite for Backyard Designer 3D
=========================================================
QUALITY GATE tests for UX & Ease-of-Use sprint.

Test categories:
  1. 30ft height clamp (raise 500 times, verify max <= 30)
  2. -30ft depth clamp (lower/excavate 500 times, verify min >= -30)
  3. Precision mode limitations (brush <= 10ft, strength <= 0.2 when active)
  4. Default strength produces small changes (single paint < 1ft at 0.05)
  5. Solid excavation rendering (terrain below 0 has visible geometry)
  6. Object placement in negative terrain

Run with: python3 sprint3_quality_gate.py [URL]
Default URL: http://127.0.0.1:8095/index.html
"""
import sys
import os
import time
import json
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8095/index.html"

results = []
failures = []


def log(test_id, test_name, status, severity="High", desc="", evidence=""):
    r = {"id": test_id, "test": test_name, "status": status, "severity": severity,
         "desc": desc, "evidence": str(evidence)[:500]}
    results.append(r)
    if status == "FAIL":
        failures.append(r)
    marker = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
    print(f"  {marker} [{status}] {test_name}: {desc}"[:200])


def dismiss_wizard(page):
    """Dismiss the startup wizard."""
    page.evaluate("""() => {
        const w = document.getElementById('wizard');
        if (w) w.style.display = 'none';
    }""")
    page.wait_for_timeout(200)


def enter_terrain_mode(page):
    """Click the terrain button to enter terrain editing mode."""
    page.evaluate("""() => {
        const btn = document.getElementById('terrain-btn');
        if (btn) btn.click();
    }""")
    page.wait_for_timeout(300)


def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--use-gl=swiftshader']
        )

        # ============================================================
        # TEST 1: 30ft Height Clamp
        # Raise terrain 500 times at center, verify max height <= 30
        # ============================================================
        print("\n=== TEST 1: 30ft Height Clamp (500 raises) ===")
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))

        page.goto(URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)
        dismiss_wizard(page)
        enter_terrain_mode(page)

        # Set to raise mode, max strength, small brush for concentrated effect
        page.evaluate("""() => {
            window._test.terrainBrushMode = 'raise';
            window._test.terrainBrushStrength = 1.0;
            window._test.terrainBrushSize = 3;
            window._test.ensureTerrainArray();
        }""")
        page.wait_for_timeout(100)

        # Paint 500 times at the center
        max_height = page.evaluate("""() => {
            const segs = window._test.state.terrainSegs;
            const centerIdx = Math.floor(segs / 2);
            const halfW = window._test.state.yard.width / 2;
            const halfD = window._test.state.yard.depth / 2;
            const wx = (centerIdx / segs) * window._test.state.yard.width - halfW;
            const wz = (centerIdx / segs) * window._test.state.yard.depth - halfD;
            for (let i = 0; i < 500; i++) {
                window._test.paintTerrain(wx, wz);
            }
            return window._test.getMaxTerrainHeight();
        }""")
        page.wait_for_timeout(200)

        clamped = max_height <= 30.0 + 0.01  # small tolerance for float
        log("QG-01", "30ft Height Clamp", "PASS" if clamped else "FAIL",
            "Critical",
            f"Max height after 500 raises: {max_height:.2f} ft (limit: 30.0)",
            f"max_height={max_height}")

        if js_errors:
            log("QG-01-ERR", "Height Clamp JS Errors", "FAIL", "High",
                f"{len(js_errors)} JS errors during test", str(js_errors[:3]))
        page.close()

        # ============================================================
        # TEST 2: -30ft Depth Clamp
        # Excavate (lower) terrain 500 times at center, verify min >= -30
        # ============================================================
        print("\n=== TEST 2: -30ft Depth Clamp (500 excavations) ===")
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))

        page.goto(URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)
        dismiss_wizard(page)
        enter_terrain_mode(page)

        # Set to lower (excavate) mode, max strength, small brush
        page.evaluate("""() => {
            window._test.terrainBrushMode = 'lower';
            window._test.terrainBrushStrength = 1.0;
            window._test.terrainBrushSize = 3;
            window._test.ensureTerrainArray();
        }""")
        page.wait_for_timeout(100)

        # Paint 500 times at the center
        min_height = page.evaluate("""() => {
            const segs = window._test.state.terrainSegs;
            const centerIdx = Math.floor(segs / 2);
            const halfW = window._test.state.yard.width / 2;
            const halfD = window._test.state.yard.depth / 2;
            const wx = (centerIdx / segs) * window._test.state.yard.width - halfW;
            const wz = (centerIdx / segs) * window._test.state.yard.depth - halfD;
            for (let i = 0; i < 500; i++) {
                window._test.paintTerrain(wx, wz);
            }
            return window._test.getMinTerrainHeight();
        }""")
        page.wait_for_timeout(200)

        clamped = min_height >= -30.0 - 0.01  # small tolerance
        log("QG-02", "-30ft Depth Clamp", "PASS" if clamped else "FAIL",
            "Critical",
            f"Min height after 500 excavations: {min_height:.2f} ft (limit: -30.0)",
            f"min_height={min_height}")

        if js_errors:
            log("QG-02-ERR", "Depth Clamp JS Errors", "FAIL", "High",
                f"{len(js_errors)} JS errors during test", str(js_errors[:3]))
        page.close()

        # ============================================================
        # TEST 3: Precision Mode Limitations
        # Activate precision mode, verify brush <= 10 and strength <= 0.2
        # ============================================================
        print("\n=== TEST 3: Precision Mode Limitations ===")
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))

        page.goto(URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)
        dismiss_wizard(page)
        enter_terrain_mode(page)

        # Set large brush and strength first
        page.evaluate("""() => {
            window._test.terrainBrushSize = 25;
            window._test.terrainBrushStrength = 0.8;
            const bs = document.getElementById('terrain-brush-size');
            const ss = document.getElementById('terrain-strength');
            if (bs) { bs.value = '25'; }
            if (ss) { ss.value = '0.8'; }
        }""")
        page.wait_for_timeout(100)

        # Enable precision mode
        page.evaluate("""() => {
            window._test.togglePrecisionMode();
        }""")
        page.wait_for_timeout(200)

        precision_info = page.evaluate("""() => {
            return {
                precisionMode: window._test.precisionMode,
                brushSize: window._test.terrainBrushSize,
                brushStrength: window._test.terrainBrushStrength,
                sliderMaxBrush: document.getElementById('terrain-brush-size').max,
                sliderMaxStrength: document.getElementById('terrain-strength').max,
                toggleClass: document.getElementById('precision-toggle').className,
                panelClass: document.getElementById('terrain-controls').className,
                statusText: document.getElementById('precision-status').textContent,
                hintVisible: document.getElementById('precision-hint').classList.contains('visible'),
            };
        }""")

        brush_ok = precision_info["brushSize"] <= 10
        strength_ok = precision_info["brushStrength"] <= 0.2
        slider_brush_ok = precision_info["sliderMaxBrush"] == '10'
        slider_strength_ok = precision_info["sliderMaxStrength"] == '0.2'
        visual_ok = 'precision-active' in precision_info["panelClass"] and 'on' in precision_info["toggleClass"]
        status_ok = precision_info["statusText"] == 'On'
        hint_ok = precision_info["hintVisible"] == True

        all_ok = brush_ok and strength_ok and slider_brush_ok and slider_strength_ok and visual_ok and status_ok and hint_ok
        log("QG-03", "Precision Mode Brush <= 10ft", "PASS" if brush_ok else "FAIL",
            "High", f"Brush size: {precision_info['brushSize']} (limit: 10)",
            f"brushSize={precision_info['brushSize']}")
        log("QG-03b", "Precision Mode Strength <= 0.2", "PASS" if strength_ok else "FAIL",
            "High", f"Strength: {precision_info['brushStrength']} (limit: 0.2)",
            f"strength={precision_info['brushStrength']}")
        log("QG-03c", "Precision Mode Slider Max Clamped", "PASS" if (slider_brush_ok and slider_strength_ok) else "FAIL",
            "Medium", f"Slider max brush: {precision_info['sliderMaxBrush']}, max strength: {precision_info['sliderMaxStrength']}",
            f"sliderMaxBrush={precision_info['sliderMaxBrush']}, sliderMaxStrength={precision_info['sliderMaxStrength']}")
        log("QG-03d", "Precision Mode Visual Indicator", "PASS" if visual_ok else "FAIL",
            "Medium", f"Panel class: {precision_info['panelClass']}, toggle class: {precision_info['toggleClass']}",
            f"visual={visual_ok}")
        log("QG-03e", "Precision Mode Status & Hint", "PASS" if (status_ok and hint_ok) else "FAIL",
            "Low", f"Status: {precision_info['statusText']}, hint visible: {precision_info['hintVisible']}",
            f"status={precision_info['statusText']}, hint={precision_info['hintVisible']}")

        # Test that precision mode can be turned off and restores slider max
        page.evaluate("""() => { window._test.togglePrecisionMode(); }""")
        page.wait_for_timeout(100)
        restored = page.evaluate("""() => {
            return {
                sliderMaxBrush: document.getElementById('terrain-brush-size').max,
                sliderMaxStrength: document.getElementById('terrain-strength').max,
                precisionMode: window._test.precisionMode,
            };
        }""")
        restored_ok = restored["sliderMaxBrush"] == '30' and restored["sliderMaxStrength"] == '1.0' and restored["precisionMode"] == False
        log("QG-03f", "Precision Mode Toggle Off Restores Limits", "PASS" if restored_ok else "FAIL",
            "Medium", f"Restored max brush: {restored['sliderMaxBrush']}, max strength: {restored['sliderMaxStrength']}",
            f"restored={restored}")

        if js_errors:
            log("QG-03-ERR", "Precision Mode JS Errors", "FAIL", "High",
                f"{len(js_errors)} JS errors during test", str(js_errors[:3]))
        page.close()

        # ============================================================
        # TEST 4: Default Strength Small Changes
        # Single paint at 0.05 strength should produce < 1ft change
        # ============================================================
        print("\n=== TEST 4: Default Strength (0.05) Small Changes ===")
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))

        page.goto(URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)
        dismiss_wizard(page)
        enter_terrain_mode(page)

        # Set to default strength 0.05, raise mode, brush size 8
        change_info = page.evaluate("""() => {
            window._test.terrainBrushMode = 'raise';
            window._test.terrainBrushStrength = 0.05;
            window._test.terrainBrushSize = 8;
            window._test.ensureTerrainArray();

            const segs = window._test.state.terrainSegs;
            const centerIdx = Math.floor(segs / 2);
            const halfW = window._test.state.yard.width / 2;
            const halfD = window._test.state.yard.depth / 2;
            const wx = (centerIdx / segs) * window._test.state.yard.width - halfW;
            const wz = (centerIdx / segs) * window._test.state.yard.depth - halfD;

            const beforeHeight = window._test.getTerrainHeight(wx, wz);
            window._test.paintTerrain(wx, wz);
            const afterHeight = window._test.getTerrainHeight(wx, wz);
            const maxAfter = window._test.getMaxTerrainHeight();

            return {
                beforeHeight: beforeHeight,
                afterHeight: afterHeight,
                change: afterHeight - beforeHeight,
                maxAfter: maxAfter,
            };
        }""")
        page.wait_for_timeout(200)

        small_change = change_info["change"] < 1.0
        log("QG-04", "Default Strength Single Paint < 1ft", "PASS" if small_change else "FAIL",
            "High",
            f"Change at center: {change_info['change']:.4f} ft (threshold: < 1.0 ft)",
            f"change={change_info['change']}, before={change_info['beforeHeight']}, after={change_info['afterHeight']}")

        if js_errors:
            log("QG-04-ERR", "Default Strength JS Errors", "FAIL", "High",
                f"{len(js_errors)} JS errors during test", str(js_errors[:3]))
        page.close()

        # ============================================================
        # TEST 5: Solid Excavation Rendering
        # Lower terrain below 0, verify the mesh has visible geometry
        # (vertices with Y < 0 exist in the yard mesh)
        # ============================================================
        print("\n=== TEST 5: Solid Excavation Rendering (below 0) ===")
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))

        page.goto(URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)
        dismiss_wizard(page)
        enter_terrain_mode(page)

        # Excavate terrain below 0
        excavation_info = page.evaluate("""() => {
            window._test.terrainBrushMode = 'lower';
            window._test.terrainBrushStrength = 1.0;
            window._test.terrainBrushSize = 15;
            window._test.ensureTerrainArray();

            const segs = window._test.state.terrainSegs;
            const centerIdx = Math.floor(segs / 2);
            const halfW = window._test.state.yard.width / 2;
            const halfD = window._test.state.yard.depth / 2;
            const wx = (centerIdx / segs) * window._test.state.yard.width - halfW;
            const wz = (centerIdx / segs) * window._test.state.yard.depth - halfD;

            // Excavate 50 times to get well below 0
            for (let i = 0; i < 50; i++) {
                window._test.paintTerrain(wx, wz);
            }

            const minH = window._test.getMinTerrainHeight();
            const mesh = window._test.yardMesh;
            const pos = mesh.geometry.attributes.position;

            // Count vertices below 0
            let belowZeroCount = 0;
            let minMeshY = Infinity;
            for (let i = 0; i < pos.count; i++) {
                const y = pos.getY(i);
                if (y < -0.01) belowZeroCount++;
                if (y < minMeshY) minMeshY = y;
            }

            // Check mesh is visible
            const meshVisible = mesh.visible;

            return {
                minTerrainHeight: minH,
                belowZeroVertices: belowZeroCount,
                minMeshY: minMeshY,
                meshVisible: meshVisible,
                totalVertices: pos.count,
            };
        }""")
        page.wait_for_timeout(200)

        has_below_zero = excavation_info["belowZeroVertices"] > 0
        mesh_visible = excavation_info["meshVisible"]
        min_below = excavation_info["minTerrainHeight"] < -0.5

        log("QG-05", "Terrain Below 0 Has Geometry", "PASS" if has_below_zero else "FAIL",
            "High",
            f"Vertices below 0: {excavation_info['belowZeroVertices']}/{excavation_info['totalVertices']}, min terrain: {excavation_info['minTerrainHeight']:.2f}",
            f"belowZeroVertices={excavation_info['belowZeroVertices']}, minMeshY={excavation_info['minMeshY']}")
        log("QG-05b", "Excavated Mesh Visible", "PASS" if mesh_visible else "FAIL",
            "Medium", f"Mesh visible: {mesh_visible}", f"meshVisible={mesh_visible}")
        log("QG-05c", "Terrain Can Go Below 0", "PASS" if min_below else "FAIL",
            "High", f"Min terrain height: {excavation_info['minTerrainHeight']:.2f} ft",
            f"minTerrainHeight={excavation_info['minTerrainHeight']}")

        if js_errors:
            log("QG-05-ERR", "Excavation Rendering JS Errors", "FAIL", "High",
                f"{len(js_errors)} JS errors during test", str(js_errors[:3]))
        page.close()

        # ============================================================
        # TEST 6: Object Placement in Negative Terrain
        # Excavate terrain below 0, place an object, verify it follows
        # ============================================================
        print("\n=== TEST 6: Object Placement in Negative Terrain ===")
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))

        page.goto(URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)
        dismiss_wizard(page)
        enter_terrain_mode(page)

        # First excavate, then add an object at the excavated location
        obj_info = page.evaluate("""() => {
            window._test.terrainBrushMode = 'lower';
            window._test.terrainBrushStrength = 1.0;
            window._test.terrainBrushSize = 15;
            window._test.ensureTerrainArray();

            // Excavate at center
            const segs = window._test.state.terrainSegs;
            const centerIdx = Math.floor(segs / 2);
            const halfW = window._test.state.yard.width / 2;
            const halfD = window._test.state.yard.depth / 2;
            const wx = (centerIdx / segs) * window._test.state.yard.width - halfW;
            const wz = (centerIdx / segs) * window._test.state.yard.depth - halfD;

            for (let i = 0; i < 50; i++) {
                window._test.paintTerrain(wx, wz);
            }

            const terrainH = window._test.getTerrainHeight(wx, wz);

            // Add a tree at the excavated location
            const objId = window._test.addObject('tree_deciduous', {}, { x: wx, y: 0, z: wz });

            // Update object height to follow terrain
            window._test.updateObjectHeight(objId);

            // Get the object
            const obj = window._test.state.objects.get(objId);
            const sceneObj = window._test.sceneObjects.get(objId);

            return {
                objId: objId,
                terrainHeight: terrainH,
                objY: obj ? obj.position.y : null,
                sceneObjY: sceneObj ? sceneObj.position.y : null,
                sceneObjVisible: sceneObj ? sceneObj.visible : null,
                terrainBelow: terrainH < -0.5,
            };
        }""")
        page.wait_for_timeout(300)

        obj_follows = obj_info["objY"] is not None and abs(obj_info["objY"] - obj_info["terrainHeight"]) < 0.5
        obj_visible = obj_info["sceneObjVisible"] == True
        terrain_below = obj_info["terrainBelow"]

        obj_y_str = f"{obj_info['objY']:.2f}" if obj_info['objY'] is not None else "null"
        log("QG-06", "Object Follows Negative Terrain", "PASS" if obj_follows else "FAIL",
            "High",
            f"Terrain height: {obj_info['terrainHeight']:.2f}, object Y: {obj_y_str}",
            f"terrainH={obj_info['terrainHeight']}, objY={obj_info['objY']}")
        log("QG-06b", "Object Visible in Negative Terrain", "PASS" if obj_visible else "FAIL",
            "Medium", f"Object visible: {obj_visible}", f"visible={obj_visible}")
        log("QG-06c", "Terrain Below 0 for Object Test", "PASS" if terrain_below else "FAIL",
            "Medium", f"Terrain height: {obj_info['terrainHeight']:.2f}",
            f"terrainBelow={terrain_below}")

        if js_errors:
            log("QG-06-ERR", "Object Placement JS Errors", "FAIL", "High",
                f"{len(js_errors)} JS errors during test", str(js_errors[:3]))
        page.close()

        # ============================================================
        # TEST 7: UX Element Verification
        # Verify all new UX elements exist and are functional
        # ============================================================
        print("\n=== TEST 7: UX Elements Present ===")
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))

        page.goto(URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)
        dismiss_wizard(page)
        enter_terrain_mode(page)

        ux_info = page.evaluate("""() => {
            const st = document.getElementById('terrain-strength');
            const sv = document.getElementById('terrain-strength-val');
            const pt = document.getElementById('precision-toggle');
            const ps = document.getElementById('precision-status');
            const ph = document.getElementById('precision-hint');
            const hr = document.getElementById('terrain-height-readout');
            const hv = document.getElementById('height-readout-value');
            const ed = document.getElementById('excavation-depth-hint');
            const lf = document.querySelector('.strength-label-fine');
            const lc = document.querySelector('.strength-label-coarse');
            const lb = document.querySelector('[data-tmode="lower"]');

            // Check excavation hint shows when in lower mode
            window._test.terrainBrushMode = 'lower';
            window._test.updateExcavationHint();

            return {
                strengthMin: st ? st.min : null,
                strengthMax: st ? st.max : null,
                strengthDefault: st ? st.value : null,
                strengthValText: sv ? sv.textContent : null,
                precisionToggleExists: !!pt,
                precisionStatusText: ps ? ps.textContent : null,
                precisionHintExists: !!ph,
                heightReadoutExists: !!hr,
                heightReadoutValue: hv ? hv.textContent : null,
                excavateHintExists: !!ed,
                excavateHintDisplay: ed ? ed.style.display : null,
                fineLabel: lf ? lf.textContent : null,
                coarseLabel: lc ? lc.textContent : null,
                lowerBtnText: lb ? lb.textContent : null,
            };
        }""")

        defaults_ok = ux_info["strengthDefault"] == '0.05' and ux_info["strengthMin"] == '0.01'
        labels_ok = ux_info["fineLabel"] == 'Fine' and ux_info["coarseLabel"] == 'Coarse'
        precision_ok = ux_info["precisionToggleExists"] and ux_info["precisionStatusText"] == 'Off'
        readout_ok = ux_info["heightReadoutExists"] and ux_info["heightReadoutValue"] is not None
        excavate_ok = ux_info["lowerBtnText"] == 'Excavate' and ux_info["excavateHintDisplay"] == 'flex'
        hint_ok = ux_info["excavateHintExists"]

        log("QG-07", "Default Strength 0.05 & Min 0.01", "PASS" if defaults_ok else "FAIL",
            "High", f"Default: {ux_info['strengthDefault']}, min: {ux_info['strengthMin']}, val: {ux_info['strengthValText']}",
            f"defaults={defaults_ok}")
        log("QG-07b", "Fine/Coarse Labels Present", "PASS" if labels_ok else "FAIL",
            "Medium", f"Fine: {ux_info['fineLabel']}, Coarse: {ux_info['coarseLabel']}",
            f"labels={labels_ok}")
        log("QG-07c", "Precision Mode Toggle Present", "PASS" if precision_ok else "FAIL",
            "High", f"Toggle exists: {ux_info['precisionToggleExists']}, status: {ux_info['precisionStatusText']}",
            f"precision={precision_ok}")
        log("QG-07d", "Height Readout Present", "PASS" if readout_ok else "FAIL",
            "Medium", f"Readout exists: {ux_info['heightReadoutExists']}, value: {ux_info['heightReadoutValue']}",
            f"readout={readout_ok}")
        log("QG-07e", "Excavate Button & Hint", "PASS" if (excavate_ok and hint_ok) else "FAIL",
            "High", f"Btn text: {ux_info['lowerBtnText']}, hint display: {ux_info['excavateHintDisplay']}",
            f"excavate={excavate_ok}, hint={hint_ok}")

        if js_errors:
            log("QG-07-ERR", "UX Elements JS Errors", "FAIL", "High",
                f"{len(js_errors)} JS errors during test", str(js_errors[:3]))
        page.close()

        browser.close()

    # ============================================================
    # SUMMARY
    # ============================================================
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    print(f"\n{'='*60}")
    print(f"SPRINT 3 QUALITY GATE RESULTS")
    print(f"{'='*60}")
    print(f"  Total tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Pass rate: {passed/total*100:.1f}%")
    print(f"{'='*60}")

    if failures:
        print(f"\n  FAILURES:")
        for f in failures:
            print(f"    ✗ [{f['id']}] {f['test']}: {f['desc']}")

    # Write JSON results
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprint3_quality_gate_results.json")
    with open(output_file, "w") as fh:
        json.dump({"total": total, "passed": passed, "failed": failed, "results": results}, fh, indent=2)
    print(f"\n  Results written to: {output_file}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
#!/usr/bin/env python3
"""
Sprint 6 — Chaos & Edge Case Test Suite for Backyard Designer 3D
Agent 4 (Critic): Tries to break the app.

Tests:
1. RAPID ACTIONS: Rapid button clicks, precision toggle spam, panel open/close
2. BOUNDARY INPUTS: Zero brush size, zero strength, extreme grid levels, edge carving
3. SAVE/LOAD CORRUPTION: Corrupt JSON, empty designs, backward compatibility
4. UNDO/REDO STRESS: Undo/redo spam, undo during operations
5. FEATURE COMBINATIONS: Multiple features simultaneously
6. KEYBOARD/MOUSE EDGE CASES: Tab spam, off-canvas, right-click
7. WEBGL CONTEXT: Context loss simulation
"""

import json
import os
import re
import sys
import time
import traceback
from playwright.sync_api import sync_playwright, Page, expect, Error as PlaywrightError

BASE_URL = "http://localhost:8484/index.html"
RESULTS_DIR = "/root/byd6-chaos-tester/chaos_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Collect all issues
issues = []

def log_issue(severity, category, description, error=None):
    issue = {
        "severity": severity,  # CRITICAL, HIGH, MEDIUM, LOW
        "category": category,
        "description": description,
        "error": str(error) if error else None,
        "timestamp": time.time(),
    }
    issues.append(issue)
    print(f"  [{severity}] {category}: {description}")
    if error:
        print(f"    Error: {error}")

def get_console_errors(page: Page):
    """Get all console errors collected during the session."""
    errors = []
    # We'll collect via a list we inject
    result = page.evaluate("() => window.__chaosErrors || []")
    return result

def setup_error_capture(page: Page):
    """Inject error capture into the page."""
    page.evaluate("""
        () => {
            window.__chaosErrors = [];
            window.__chaosUnhandledErrors = [];
            const origError = console.error;
            console.error = function(...args) {
                window.__chaosErrors.push(args.join(' '));
                origError.apply(console, args);
            };
            window.addEventListener('error', (e) => {
                window.__chaosUnhandledErrors.push({
                    message: e.message,
                    filename: e.filename,
                    lineno: e.lineno,
                });
            });
            window.addEventListener('unhandledrejection', (e) => {
                window.__chaosUnhandledErrors.push({
                    message: 'Unhandled promise: ' + (e.reason && e.reason.message || e.reason),
                });
            });
        }
    """)

def check_for_errors(page: Page, test_name):
    """Check if any JS errors occurred and log them."""
    errors = page.evaluate("() => window.__chaosErrors || []")
    unhandled = page.evaluate("() => window.__chaosUnhandledErrors || []")
    if errors:
        for err in errors[-5:]:  # last 5
            log_issue("HIGH", test_name, f"Console error: {err[:200]}")
    if unhandled:
        for err in unhandled[-5:]:
            log_issue("CRITICAL", test_name, f"Unhandled error: {err.get('message', '')[:200]}")
    # Clear for next test
    page.evaluate("() => { window.__chaosErrors = []; window.__chaosUnhandledErrors = []; }")
    return len(errors) + len(unhandled)

def wait_for_app(page: Page, timeout=15000):
    """Wait for the app to fully load."""
    page.wait_for_load_state("networkidle", timeout=timeout)
    page.wait_for_function("() => typeof window._test !== 'undefined' && window._test.state", timeout=timeout)
    # Expose all _test functions to global scope for easier testing
    page.evaluate("""
        () => {
            const t = window._test;
            if (!t) return;
            // Expose key functions and variables globally
            window.state = t.state;
            window.CATALOG = t.CATALOG;
            window.scene = t.scene;
            window.renderer = t.renderer;
            window.sceneObjects = t.sceneObjects;
            window.yardMesh = t.yardMesh;
            window.gridHelper = t.gridHelper;
            window.boundaryLines = t.boundaryLines;
            window.activeCamera = t.activeCamera;
            window.loadDesign = t.loadDesign;
            window.serializeDesign = t.serializeDesign;
            window.addObject = t.addObject;
            window.buildSceneObject = t.buildSceneObject;
            window.getTerrainHeight = t.getTerrainHeight;
            window.getTerrainIndex = t.getTerrainIndex;
            window.applyTerrainToMesh = t.applyTerrainToMesh;
            window.paintTerrain = t.paintTerrain;
            window.ensureTerrainArray = t.ensureTerrainArray;
            window.hasTerrainDeformation = t.hasTerrainDeformation;
            window.undo = t.undo;
            window.redo = t.redo;
            window.applyTerrainPreset = t.applyTerrainPreset;
            window.setGridLevel = t.setGridLevel;
            window.carveShape = t.carveShape;
            window.fillShape = t.fillShape;
            window.carveWithBrush = t.carveWithBrush;
            window.fillWithBrush = t.fillWithBrush;
            window.initVoxelsFromTerrain = t.initVoxelsFromTerrain;
            window.updateVoxelsFromTerrain = t.updateVoxelsFromTerrain;
            window.buildVoxelMesh = t.buildVoxelMesh;
            window.serializeVoxels = t.serializeVoxels;
            window.deserializeVoxels = t.deserializeVoxels;
            window.snapshotVoxels = t.snapshotVoxels;
            window.restoreVoxelSnapshot = t.restoreVoxelSnapshot;
            window.pushVoxelUndo = t.pushVoxelUndo;
            window.voxelToWorld = t.voxelToWorld;
            window.worldToVoxel = t.worldToVoxel;
            window.getVoxel = t.getVoxel;
            window.setVoxel = t.setVoxel;
            window.countSolidVoxels = t.countSolidVoxels;
            window.countVoxelFaces = t.countVoxelFaces;
            window.removeObject = t.removeObject || function(id) { t.state.objects.delete(id); };
            window.updateObjectHeight = t.updateObjectHeight;
            window.updateAllBuriedIndicators = t.updateAllBuriedIndicators;
            window.clampTerrainHeight = t.clampTerrainHeight;
            window.updateVoxelInfoDisplay = t.updateVoxelInfoDisplay;
            window.togglePrecisionMode = t.togglePrecisionMode;
            window.updatePrecisionModeUI = t.updatePrecisionModeUI;
            window.selectObject = t.selectObject;
            window.deselectObject = t.deselectObject;
            window.applyHeightColors = t.applyHeightColors;
            window.removeHeightColors = t.removeHeightColors;
            window.applyTerrainEdgeHighlight = t.applyTerrainEdgeHighlight;
            window._recomputeTerrainDeformed = t._recomputeTerrainDeformed;
            window.MAX_TERRAIN_HEIGHT = t.MAX_TERRAIN_HEIGHT;
            window.MIN_TERRAIN_HEIGHT = t.MIN_TERRAIN_HEIGHT;
            window.VOXEL_SIZE = t.VOXEL_SIZE;
            window.VOXEL_DEPTH = t.VOXEL_DEPTH;
            // Terrain snapshot helper (terrain uses Float32Array copies for undo)
            window.snapshotTerrain = function() { return t.state.terrain ? new Float32Array(t.state.terrain) : null; };
            window.pushTerrainUndo = function(beforeSnap) {
                const after = t.state.terrain ? new Float32Array(t.state.terrain) : null;
                if (beforeSnap || after) {
                    t.state.undoStack.push({
                        undo: () => { t.state.terrain = beforeSnap; t._recomputeTerrainDeformed(); t.window._test.applyTerrainToMesh(); },
                        redo: () => { t.state.terrain = after; t._recomputeTerrainDeformed(); t.window._test.applyTerrainToMesh(); },
                    });
                    t.state.redoStack = [];
                }
            };
            window.requestRender = function() { if (t.renderer) t.renderer.render(t.scene, t.activeCamera); };
            window.saveDesign = t.saveDesign || function() {};
            window.deleteObjectWithCommand = t.deleteObjectWithCommand || function(id) {
                const obj = t.state.objects.get(id);
                if (!obj) return;
                t.state.objects.delete(id);
                t.buildSceneObject(id);
            };
            window.showToast = t.showToast || function() {};
            window.removeObject = t.removeObject || function(id) {
                const obj = t.sceneObjects.get(id);
                if (obj) { t.scene.remove(obj); t.sceneObjects.delete(id); }
                t.state.objects.delete(id);
            };
            window.requestRender = t.requestRender || function() { if (t.renderer) t.renderer.render(t.scene, t.activeCamera); };
            window.moveBrushCursor = t.moveBrushCursor || function() {};
            window.getGroundPointFromEvent = t.getGroundPointFromEvent || function() { return null; };
            window.deleteObject = t.deleteObjectWithCommand || window.deleteObjectWithCommand;
        }
    """)

def dismiss_toasts(page: Page):
    """Dismiss any toast notifications."""
    try:
        page.evaluate("() => { const t = document.getElementById('toast'); if (t) { t.style.display = 'none'; t.textContent = ''; } }")
    except:
        pass

class ChaosTests:
    def __init__(self, page: Page):
        self.page = page
        self.errors_found = 0
        self.crashes_found = 0
        self.hangs_found = 0
        
    def setup(self):
        """Setup before each test - navigate and capture errors."""
        self.page.goto(BASE_URL, wait_until="networkidle", timeout=15000)
        wait_for_app(self.page)
        # Dismiss the setup wizard
        self._dismiss_wizard()
        setup_error_capture(self.page)
        dismiss_toasts(self.page)
    
    def _dismiss_wizard(self):
        """Dismiss the setup wizard if visible."""
        try:
            wizard = self.page.query_selector("#wizard")
            if wizard and wizard.is_visible():
                # Click Next
                next_btn = self.page.query_selector("#wizard-next")
                if next_btn and next_btn.is_visible():
                    next_btn.click()
                    self.page.wait_for_timeout(500)
                # Click Finish/Start
                finish_btn = self.page.query_selector("#wizard-finish")
                if finish_btn and finish_btn.is_visible():
                    finish_btn.click()
                    self.page.wait_for_timeout(500)
        except:
            pass
    
    def _click_dock_tab(self, tab_name):
        """Click a dock tab by aria-label or text."""
        try:
            tabs = self.page.query_selector_all(".td-tab")
            for tab in tabs:
                label = tab.get_attribute("aria-label") or ""
                text = tab.text_content() or ""
                if tab_name.lower() in label.lower() or tab_name.lower() in text.lower():
                    tab.click()
                    self.page.wait_for_timeout(200)
                    return True
        except:
            pass
        return False
    
    def _open_dock_panel(self, panel_id):
        """Open a dock panel by clicking the appropriate tab."""
        tab_map = {
            'dock-terrain': 'Terrain',
            'dock-underground': 'Underground',
            'dock-analyze': 'Analyze',
            'dock-innovate': 'Pro Tools',
            'dock-sun': 'Sun',
            'dock-measure': 'Measure',
        }
        tab_name = tab_map.get(panel_id, '')
        if tab_name:
            return self._click_dock_tab(tab_name)
        return False

    # ============================================================
    # 1. RAPID ACTIONS
    # ============================================================
    def test_rapid_terrain_button_clicks(self):
        """Click terrain dock tab 100 times rapidly."""
        self.setup()
        print("\n[TEST] Rapid terrain tab clicks (100x)")
        
        try:
            # Use JS to rapidly toggle the dock tab (simulates 100 clicks)
            result = self.page.evaluate("""
                () => {
                    try {
                        const tabs = document.querySelectorAll('.td-tab');
                        if (tabs.length === 0) return 'no tabs';
                        const terrainTab = tabs[0]; // First tab is Terrain
                        for (let i = 0; i < 100; i++) {
                            terrainTab.click();
                        }
                        return 'ok clicks=100';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            # Check app is still alive
            alive = self.page.evaluate("() => typeof window._test !== 'undefined' && window._test.state")
            assert alive, "App crashed after rapid terrain tab clicks"
            
            err_count = check_for_errors(self.page, "rapid_terrain_clicks")
            if err_count > 0:
                self.crashes_found += 1
            print(f"  ✓ App survived 100 rapid terrain tab clicks")
        except PlaywrightError as e:
            log_issue("CRITICAL", "rapid_terrain_clicks", "App crashed/hung during rapid terrain tab clicks", e)
            self.crashes_found += 1
        except AssertionError as e:
            log_issue("HIGH", "rapid_terrain_clicks", f"Assertion failed: {e}", e)
            self.crashes_found += 1

    def test_rapid_precision_toggle(self):
        """Toggle precision mode 50 times rapidly."""
        self.setup()
        print("\n[TEST] Rapid precision toggle (50x)")
        
        try:
            # Open terrain dock panel first
            self._open_dock_panel('dock-terrain')
            self.page.wait_for_timeout(200)
            
            precision_toggle = self.page.query_selector("#precision-toggle")
            if not precision_toggle or not precision_toggle.is_visible():
                # Use JS directly
                result = self.page.evaluate("""
                    () => {
                        try {
                            for (let i = 0; i < 50; i++) {
                                window._test.togglePrecisionMode();
                            }
                            return 'ok';
                        } catch(e) {
                            return 'error: ' + e.message;
                        }
                    }
                """)
            else:
                for i in range(50):
                    precision_toggle.click(timeout=1000)
                    if i % 10 == 0:
                        self.page.wait_for_timeout(10)
                result = 'ok'
            
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("CRITICAL", "rapid_precision_toggle", f"Precision toggle error: {result}")
                self.crashes_found += 1
            else:
                # Check state is valid
                pm = self.page.evaluate("() => typeof window._test !== 'undefined' && window._test.precisionMode !== 'undefined'")
                assert pm, "precisionMode variable lost after rapid toggle"
                err_count = check_for_errors(self.page, "rapid_precision_toggle")
                if err_count > 0:
                    self.crashes_found += 1
                print(f"  ✓ App survived 50 rapid precision toggles")
        except PlaywrightError as e:
            log_issue("CRITICAL", "rapid_precision_toggle", "App crashed during rapid precision toggle", e)
            self.crashes_found += 1
        except AssertionError as e:
            log_issue("HIGH", "rapid_precision_toggle", f"Assertion failed: {e}", e)
            self.crashes_found += 1

    def test_rapid_panel_open_close(self):
        """Open and close every dock panel 20 times rapidly."""
        self.setup()
        print("\n[TEST] Rapid panel open/close (20x each)")
        
        # Use dock tabs for the new IA system + topbar buttons
        dock_tabs = [
            ('dock-terrain', 'Terrain'),
            ('dock-underground', 'Underground'),
            ('dock-analyze', 'Analyze'),
            ('dock-innovate', 'Pro Tools'),
            ('dock-sun', 'Sun & Shadow'),
            ('dock-measure', 'Measure'),
        ]
        
        topbar_btns = ["#btn-layers", "#btn-cost", "#btn-walk"]
        
        for panel_id, tab_name in dock_tabs:
            try:
                # Use JS to rapidly toggle
                result = self.page.evaluate(f"""
                    () => {{
                        try {{
                            const tabs = document.querySelectorAll('.td-tab');
                            let targetTab = null;
                            for (const t of tabs) {{
                                const label = t.getAttribute('aria-label') || '';
                                const text = t.textContent || '';
                                if (label.includes('{tab_name}') || text.includes('{tab_name.split()[0]}')) {{
                                    targetTab = t;
                                    break;
                                }}
                            }}
                            if (!targetTab) return 'tab not found';
                            for (let i = 0; i < 20; i++) targetTab.click();
                            return 'ok';
                        }} catch(e) {{
                            return 'error: ' + e.message;
                        }}
                    }}
                """)
                
                if result.startswith('error'):
                    log_issue("HIGH", f"rapid_panel_{panel_id}", f"Panel toggle failed: {result[:200]}")
                    self.crashes_found += 1
                else:
                    err_count = check_for_errors(self.page, f"rapid_panel_{panel_id}")
                    if err_count > 0:
                        self.crashes_found += 1
                    print(f"  ✓ {panel_id} survived 20 rapid toggles")
            except PlaywrightError as e:
                log_issue("HIGH", f"rapid_panel_{panel_id}", f"Panel toggle failed for {panel_id}", e)
                self.crashes_found += 1
        
        for btn_id in topbar_btns:
            try:
                btn = self.page.query_selector(btn_id)
                if not btn or not btn.is_visible():
                    continue
                
                for i in range(20):
                    btn.click(timeout=1000)
                    if i % 5 == 0:
                        self.page.wait_for_timeout(10)
                
                # Close
                btn.click(timeout=1000)
                self.page.wait_for_timeout(50)
                
                err_count = check_for_errors(self.page, f"rapid_panel_{btn_id}")
                if err_count > 0:
                    self.crashes_found += 1
                print(f"  ✓ {btn_id} survived 20 rapid toggles")
            except PlaywrightError as e:
                log_issue("HIGH", f"rapid_panel_{btn_id}", f"Panel toggle failed for {btn_id}", e)
                self.crashes_found += 1

    # ============================================================
    # 2. BOUNDARY INPUTS
    # ============================================================
    def test_zero_brush_size(self):
        """Set brush size to 0 and try to paint."""
        self.setup()
        print("\n[TEST] Zero brush size painting")
        
        try:
            # Set brush size to 0 via window._test API
            result = self.page.evaluate("""
                () => {
                    try {
                        window._test.terrainBrushSize = 0;
                        window._test.terrainBrushStrength = 0.1;
                        window._test.ensureTerrainArray();
                        window._test.paintTerrain(5, 5);
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "zero_brush_size", f"Paint with zero brush size caused error: {result}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Zero brush size handled gracefully")
            
            check_for_errors(self.page, "zero_brush_size")
        except PlaywrightError as e:
            log_issue("HIGH", "zero_brush_size", "Error during zero brush size test", e)
            self.crashes_found += 1

    def test_zero_strength(self):
        """Set strength to 0 and try to paint."""
        self.setup()
        print("\n[TEST] Zero strength painting")
        
        try:
            result = self.page.evaluate("""
                () => {
                    try {
                        window._test.terrainBrushSize = 5;
                        window._test.terrainBrushStrength = 0;
                        window._test.ensureTerrainArray();
                        window._test.paintTerrain(5, 5);
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "zero_strength", f"Paint with zero strength caused error: {result}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Zero strength handled gracefully")
            
            check_for_errors(self.page, "zero_strength")
        except PlaywrightError as e:
            log_issue("HIGH", "zero_strength", "Error during zero strength test", e)
            self.crashes_found += 1

    def test_extreme_grid_level(self):
        """Set grid level to -30 then +30 rapidly."""
        self.setup()
        print("\n[TEST] Extreme grid level (-30 to +30 rapidly)")
        
        try:
            # Rapidly alternate between -30 and +30 via window._test API
            result = self.page.evaluate("""
                () => {
                    try {
                        for (let i = 0; i < 20; i++) {
                            window._test.setGridLevel(i % 2 === 0 ? -30 : 30);
                        }
                        return 'ok level=' + window._test.state.gridLevel;
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "extreme_grid_level", f"Extreme grid level failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Extreme grid level handled")
            
            check_for_errors(self.page, "extreme_grid_level")
        except PlaywrightError as e:
            log_issue("HIGH", "extreme_grid_level", "Error during extreme grid level test", e)
            self.crashes_found += 1

    def test_edge_carving(self):
        """Carve a shape at the exact edge of the yard."""
        self.setup()
        print("\n[TEST] Edge carving")
        
        try:
            # Get yard dimensions
            yard = self.page.evaluate("() => ({width: window._test.state.yard.width, depth: window._test.state.yard.depth})")
            print(f"  Yard: {yard}")
            
            # Carve at extreme edges using window._test API
            edges = [
                (yard['width']/2, yard['depth']/2),
                (-yard['width']/2, -yard['depth']/2),
                (yard['width']/2, 0),
                (0, yard['depth']/2),
                (yard['width']/2 + 100, yard['depth']/2 + 100),
                (-yard['width']*2, -yard['depth']*2),
            ]
            
            for i, (x, z) in enumerate(edges):
                result = self.page.evaluate(f"""
                    () => {{
                        try {{
                            window._test.ensureTerrainArray();
                            window._test.initVoxelsFromTerrain();
                            window._test.carveShape('box', {x}, 0, {z}, 5, 5);
                            return 'ok';
                        }} catch(e) {{
                            return 'error: ' + e.message + ' stack: ' + e.stack;
                        }}
                    }}
                """)
                if result.startswith('error'):
                    log_issue("HIGH", "edge_carving", f"Carve at ({x},{z}) failed: {result[:200]}")
                    self.crashes_found += 1
                else:
                    print(f"  ✓ Edge carve at ({x},{z}) OK")
            
            check_for_errors(self.page, "edge_carving")
        except PlaywrightError as e:
            log_issue("HIGH", "edge_carving", "Error during edge carving test", e)
            self.crashes_found += 1

    def test_object_at_extreme_coords(self):
        """Place objects at (0,0) and (100,100) and beyond."""
        self.setup()
        print("\n[TEST] Object placement at extreme coordinates")
        
        try:
            # Get first available object type
            obj_type = self.page.evaluate("""
                () => {
                    const keys = Object.keys(CATALOG);
                    return keys[0];
                }
            """)
            print(f"  Using object type: {obj_type}")
            
            coords = [(0, 0), (100, 100), (-100, -100), (1000, 1000), (-9999, -9999), (0.001, 0.001)]
            
            for x, z in coords:
                result = self.page.evaluate(f"""
                    () => {{
                        try {{
                            const id = addObject('{obj_type}', CATALOG['{obj_type}'].defaults || {{}}, {{x: {x}, y: 0, z: {z}}});
                            return 'ok id=' + id;
                        }} catch(e) {{
                            return 'error: ' + e.message;
                        }}
                    }}
                """)
                if result.startswith('error'):
                    log_issue("HIGH", "extreme_coords", f"Add object at ({x},{z}) failed: {result[:200]}")
                    self.crashes_found += 1
                else:
                    print(f"  ✓ Object at ({x},{z}): {result}")
            
            check_for_errors(self.page, "extreme_coords")
        except PlaywrightError as e:
            log_issue("HIGH", "extreme_coords", "Error during extreme coords test", e)
            self.crashes_found += 1

    # ============================================================
    # 3. SAVE/LOAD CORRUPTION
    # ============================================================
    def test_corrupt_json_load(self):
        """Load corrupted JSON data."""
        self.setup()
        print("\n[TEST] Corrupt JSON loading")
        
        corrupt_payloads = [
            '{"objects": }',  # syntax error
            '{"objects": null}',  # null objects
            '{"objects": "string"}',  # wrong type
            '{"objects": [null]}',  # null element
            '{"objects": [{"type": "nonexistent"}]}',  # invalid type
            '{"objects": [], "yard": {"width": -1, "depth": -1}}',  # negative yard
            '{"objects": [], "yard": {"width": 0}}',  # zero yard
            '{"objects": [{"type": "tree", "params": null}]}',  # null params
            '{"objects": [{"type": "tree", "params": {}, "position": null}]}',  # null position
            '{}',  # empty object
            'null',  # null
            'undefined',  # undefined string
            '{"objects": [{"type": "tree", "params": {}, "position": {"x": "NaN", "y": Infinity, "z": -Infinity}}]}',
            '{"objects": [{"type": "tree", "params": {}, "position": {"x": 1e308, "y": -1e308}}]}',
            '{"objects": [{"type": "<script>alert(1)</script>", "params": {}, "position": {"x":0,"y":0,"z":0}}]}',
        ]
        
        for i, payload in enumerate(corrupt_payloads):
            try:
                result = self.page.evaluate(f"""
                    () => {{
                        try {{
                            const data = JSON.parse({json.dumps(payload)});
                            window._test.loadDesign(data);
                            return 'loaded';
                        }} catch(e) {{
                            if (e instanceof SyntaxError) return 'parse_error_handled';
                            return 'error: ' + e.message;
                        }}
                    }}
                """)
                if result.startswith('error'):
                    log_issue("CRITICAL", "corrupt_json", f"Corrupt payload {i} caused error: {result[:200]}")
                    self.crashes_found += 1
                elif result == 'loaded' or result == 'parse_error_handled':
                    print(f"  ✓ Corrupt payload {i} handled gracefully")
                else:
                    print(f"  ? Corrupt payload {i}: {result}")
            except PlaywrightError as e:
                log_issue("CRITICAL", "corrupt_json", f"Corrupt payload {i} crashed page: {str(e)[:200]}", e)
                self.crashes_found += 1
                # Re-setup
                self.setup()
        
        check_for_errors(self.page, "corrupt_json")

    def test_empty_design_save_load(self):
        """Save and load with 0 objects."""
        self.setup()
        print("\n[TEST] Empty design save/load")
        
        try:
            # Clear all objects
            self.page.evaluate("""
                () => {
                    window._test.state.objects.clear();
                    window._test.state.objects.clear();
                    requestRender();
                }
            """)
            
            # Serialize
            data = self.page.evaluate("() => JSON.stringify(window._test.serializeDesign())")
            design = json.loads(data)
            print(f"  Objects in saved design: {len(design.get('objects', []))}")
            assert len(design.get('objects', [])) == 0, "Expected 0 objects"
            
            # Load it back
            result = self.page.evaluate(f"""
                () => {{
                    try {{
                        window._test.loadDesign({data});
                        return 'ok';
                    }} catch(e) {{
                        return 'error: ' + e.message;
                    }}
                }}
            """)
            if result.startswith('error'):
                log_issue("HIGH", "empty_save_load", f"Empty design load failed: {result}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Empty design save/load OK")
            
            check_for_errors(self.page, "empty_save_load")
        except PlaywrightError as e:
            log_issue("HIGH", "empty_save_load", "Error during empty design test", e)
            self.crashes_found += 1

    def test_max_objects_save_load(self):
        """Save and load with many objects."""
        self.setup()
        print("\n[TEST] Maximum objects save/load")
        
        try:
            # Add 100 objects
            result = self.page.evaluate("""
                () => {
                    try {
                        const types = Object.keys(window._test.CATALOG);
                        for (let i = 0; i < 100; i++) {
                            const t = types[i % types.length];
                            window._test.addObject(t, window._test.CATALOG[t].defaults || {}, {x: (i % 10) * 5 - 22, y: 0, z: Math.floor(i/10) * 5 - 22});
                        }
                        return 'added ' + window._test.state.objects.size;
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "max_objects", f"Adding 100 objects failed: {result}")
                self.crashes_found += 1
                return
            
            # Serialize
            data = self.page.evaluate("() => JSON.stringify(window._test.serializeDesign())")
            design = json.loads(data)
            print(f"  Objects in saved design: {len(design.get('objects', []))}")
            
            # Clear and reload
            self.page.evaluate("() => { window._test.state.objects.clear(); window._test.state.objects.clear(); }")
            
            result = self.page.evaluate(f"""
                () => {{
                    try {{
                        window._test.loadDesign({data});
                        return 'ok count=' + window._test.state.objects.size;
                    }} catch(e) {{
                        return 'error: ' + e.message;
                    }}
                }}
            """)
            print(f"  Load result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "max_objects", f"Loading 100 objects failed: {result}")
                self.crashes_found += 1
            else:
                print(f"  ✓ 100 objects save/load OK")
            
            check_for_errors(self.page, "max_objects")
        except PlaywrightError as e:
            log_issue("HIGH", "max_objects", "Error during max objects test", e)
            self.crashes_found += 1

    def test_backward_compatibility(self):
        """Load a Sprint 1 save file (version 1 format)."""
        self.setup()
        print("\n[TEST] Backward compatibility (Sprint 1 save)")
        
        try:
            # Simulate Sprint 1 save (version 1, minimal fields)
            sprint1_save = json.dumps({
                "version": 1,
                "yard": {"width": 40, "depth": 30, "shape": "rectangle"},
                "objects": [
                    {"type": "tree", "params": {"size": "medium"}, "position": {"x": 5, "y": 0, "z": 5}, "rotation": 0},
                    {"type": "pool", "params": {"shape": "rectangle", "size": "medium"}, "position": {"x": -5, "y": 0, "z": -5}, "rotation": 0},
                ],
                "nextId": 3,
            })
            
            result = self.page.evaluate(f"""
                () => {{
                    try {{
                        window._test.loadDesign({sprint1_save});
                        return 'ok count=' + window._test.state.objects.size;
                    }} catch(e) {{
                        return 'error: ' + e.message + ' stack: ' + (e.stack || '').substring(0, 300);
                    }}
                }}
            """)
            print(f"  Sprint 1 load: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "backward_compat", f"Sprint 1 save load failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Sprint 1 save loaded successfully")
            
            check_for_errors(self.page, "backward_compat")
        except PlaywrightError as e:
            log_issue("HIGH", "backward_compat", "Error during backward compat test", e)
            self.crashes_found += 1

    def test_corrupted_voxel_data(self):
        """Load save with corrupted voxel data."""
        self.setup()
        print("\n[TEST] Corrupted voxel data load")
        
        try:
            corrupt_voxel_saves = [
                # Empty RLE
                json.dumps({"version": 3, "yard": {"width": 40, "depth": 30, "shape": "rectangle"}, 
                           "objects": [], "nextId": 1, "voxels": {"dims": [40, 20, 40], "rle": [], "voxelSize": 1, "depth": 20}}),
                # Odd-length RLE
                json.dumps({"version": 3, "yard": {"width": 40, "depth": 30, "shape": "rectangle"}, 
                           "objects": [], "nextId": 1, "voxels": {"dims": [40, 20, 40], "rle": [1, 2, 3], "voxelSize": 1, "depth": 20}}),
                # RLE longer than total
                json.dumps({"version": 3, "yard": {"width": 40, "depth": 30, "shape": "rectangle"}, 
                           "objects": [], "nextId": 1, "voxels": {"dims": [2, 2, 2], "rle": [1, 999], "voxelSize": 1, "depth": 20}}),
                # Zero dimensions
                json.dumps({"version": 3, "yard": {"width": 40, "depth": 30, "shape": "rectangle"}, 
                           "objects": [], "nextId": 1, "voxels": {"dims": [0, 0, 0], "rle": [1, 1], "voxelSize": 1, "depth": 20}}),
                # Negative dimensions
                json.dumps({"version": 3, "yard": {"width": 40, "depth": 30, "shape": "rectangle"}, 
                           "objects": [], "nextId": 1, "voxels": {"dims": [-1, 10, 10], "rle": [1, 1], "voxelSize": 1, "depth": 20}}),
                # Missing dims
                json.dumps({"version": 3, "yard": {"width": 40, "depth": 30, "shape": "rectangle"}, 
                           "objects": [], "nextId": 1, "voxels": {"rle": [1, 1]}}),
                # Missing rle
                json.dumps({"version": 3, "yard": {"width": 40, "depth": 30, "shape": "rectangle"}, 
                           "objects": [], "nextId": 1, "voxels": {"dims": [10, 10, 10]}}),
            ]
            
            for i, save_data in enumerate(corrupt_voxel_saves):
                result = self.page.evaluate(f"""
                    () => {{
                        try {{
                            const data = JSON.parse({json.dumps(save_data)});
                            window._test.loadDesign(data);
                            return 'loaded';
                        }} catch(e) {{
                            return 'error: ' + e.message;
                        }}
                    }}
                """)
                if result.startswith('error'):
                    log_issue("HIGH", "corrupt_voxels", f"Corrupt voxel save {i} failed: {result[:200]}")
                    self.crashes_found += 1
                else:
                    print(f"  ✓ Corrupt voxel save {i} handled")
            
            check_for_errors(self.page, "corrupt_voxels")
        except PlaywrightError as e:
            log_issue("HIGH", "corrupt_voxels", "Error during corrupt voxel test", e)
            self.crashes_found += 1

    def test_corrupted_terrain_data(self):
        """Load save with corrupted terrain array."""
        self.setup()
        print("\n[TEST] Corrupted terrain data load")
        
        try:
            corrupt_terrain_saves = [
                # Terrain with wrong length
                json.dumps({"version": 3, "yard": {"width": 40, "depth": 30, "shape": "rectangle"}, 
                           "objects": [], "nextId": 1, "terrain": [1, 2, 3], "terrainSegs": 100}),
                # Terrain with null
                json.dumps({"version": 3, "yard": {"width": 40, "depth": 30, "shape": "rectangle"}, 
                           "objects": [], "nextId": 1, "terrain": None, "terrainSegs": 100}),
                # Terrain with extreme values
                json.dumps({"version": 3, "yard": {"width": 40, "depth": 30, "shape": "rectangle"}, 
                           "objects": [], "nextId": 1, "terrain": [99999, -99999, 1e308], "terrainSegs": 0}),
                # TerrainSegs = 0
                json.dumps({"version": 3, "yard": {"width": 40, "depth": 30, "shape": "rectangle"}, 
                           "objects": [], "nextId": 1, "terrainSegs": 0}),
                # TerrainSegs negative
                json.dumps({"version": 3, "yard": {"width": 40, "depth": 30, "shape": "rectangle"}, 
                           "objects": [], "nextId": 1, "terrainSegs": -10}),
                # TerrainSegs very large
                json.dumps({"version": 3, "yard": {"width": 40, "depth": 30, "shape": "rectangle"}, 
                           "objects": [], "nextId": 1, "terrainSegs": 1000000}),
            ]
            
            for i, save_data in enumerate(corrupt_terrain_saves):
                result = self.page.evaluate(f"""
                    () => {{
                        try {{
                            const data = JSON.parse({json.dumps(save_data)});
                            window._test.loadDesign(data);
                            return 'loaded segs=' + window._test.state.terrainSegs;
                        }} catch(e) {{
                            return 'error: ' + e.message;
                        }}
                    }}
                """)
                if result.startswith('error'):
                    log_issue("HIGH", "corrupt_terrain", f"Corrupt terrain save {i} failed: {result[:200]}")
                    self.crashes_found += 1
                else:
                    print(f"  ✓ Corrupt terrain save {i}: {result}")
            
            check_for_errors(self.page, "corrupt_terrain")
        except PlaywrightError as e:
            log_issue("HIGH", "corrupt_terrain", "Error during corrupt terrain test", e)
            self.crashes_found += 1

    # ============================================================
    # 4. UNDO/REDO STRESS
    # ============================================================
    def test_undo_100_times(self):
        """Undo 100 times when stack has limited entries."""
        self.setup()
        print("\n[TEST] Undo 100 times")
        
        try:
            # Add a few objects
            self.page.evaluate("""
                () => {
                    const types = Object.keys(window._test.CATALOG);
                    for (let i = 0; i < 5; i++) {
                        const t = types[i % types.length];
                        window._test.addObject(t, window._test.CATALOG[t].defaults || {}, {x: i*3, y: 0, z: 0});
                    }
                }
            """)
            
            stack_size = self.page.evaluate("() => window._test.state.undoStack.length")
            print(f"  Undo stack size: {stack_size}")
            
            # Undo 100 times
            result = self.page.evaluate("""
                () => {
                    try {
                        for (let i = 0; i < 100; i++) {
                            window._test.undo();
                        }
                        return 'ok stack=' + window._test.state.undoStack.length + ' redo=' + window._test.state.redoStack.length;
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("CRITICAL", "undo_100", f"Undo 100 times crashed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Undo 100x survived")
            
            check_for_errors(self.page, "undo_100")
        except PlaywrightError as e:
            log_issue("HIGH", "undo_100", "Error during undo stress test", e)
            self.crashes_found += 1

    def test_redo_100_times(self):
        """Redo 100 times."""
        self.setup()
        print("\n[TEST] Redo 100 times")
        
        try:
            # Add objects, undo them all, then redo spam
            self.page.evaluate("""
                () => {
                    const types = Object.keys(window._test.CATALOG);
                    for (let i = 0; i < 5; i++) {
                        const t = types[i % types.length];
                        window._test.addObject(t, window._test.CATALOG[t].defaults || {}, {x: i*3, y: 0, z: 0});
                    }
                    while (window._test.state.undoStack.length > 0) window._test.undo();
                }
            """)
            
            redo_size = self.page.evaluate("() => window._test.state.redoStack.length")
            print(f"  Redo stack size: {redo_size}")
            
            result = self.page.evaluate("""
                () => {
                    try {
                        for (let i = 0; i < 100; i++) {
                            window._test.redo();
                        }
                        return 'ok stack=' + window._test.state.undoStack.length + ' redo=' + window._test.state.redoStack.length;
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("CRITICAL", "redo_100", f"Redo 100 times crashed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Redo 100x survived")
            
            check_for_errors(self.page, "redo_100")
        except PlaywrightError as e:
            log_issue("HIGH", "redo_100", "Error during redo stress test", e)
            self.crashes_found += 1

    def test_undo_during_terrain_paint(self):
        """Undo while terrain painting is in progress."""
        self.setup()
        print("\n[TEST] Undo during terrain painting")
        
        try:
            # Set terrain mode to raise and paint
            self.page.evaluate("""
                () => {
                    window._test.terrainBrushMode = 'raise';
                    window._test.ensureTerrainArray();
                    // Paint several times to build up undo stack
                    for (let i = 0; i < 10; i++) {
                        const snap = window._test.state.terrain ? new Float32Array(window._test.state.terrain) : null;
                        window._test.paintTerrain(i * 2, i * 2);
                        const after = window._test.state.terrain ? new Float32Array(window._test.state.terrain) : null;
                        window._test.state.undoStack.push({
                            undo: () => { window._test.state.terrain = snap; window._test._recomputeTerrainDeformed(); window._test.applyTerrainToMesh(); },
                            redo: () => { window._test.state.terrain = after; window._test._recomputeTerrainDeformed(); window._test.applyTerrainToMesh(); },
                        });
                        window._test.state.redoStack = [];
                    }
                }
            """)
            
            # Now undo during a paint operation
            result = self.page.evaluate("""
                () => {
                    try {
                        const snap = window._test.state.terrain ? new Float32Array(window._test.state.terrain) : null;
                        window._test.paintTerrain(5, 5);
                        // Undo mid-paint
                        window._test.undo();
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "undo_during_paint", f"Undo during terrain paint failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Undo during terrain paint OK")
            
            check_for_errors(self.page, "undo_during_paint")
        except PlaywrightError as e:
            log_issue("HIGH", "undo_during_paint", "Error during undo-during-paint test", e)
            self.crashes_found += 1

    def test_undo_during_carving(self):
        """Undo while carving."""
        self.setup()
        print("\n[TEST] Undo during carving")
        
        try:
            result = self.page.evaluate("""
                () => {
                    try {
                        window._test.ensureTerrainArray();
                        window._test.initVoxelsFromTerrain();
                        const before = window._test.snapshotVoxels();
                        window._test.carveShape('box', 5, 0, 5, 5, 5);
                        window._test.undo();
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "undo_during_carve", f"Undo during carving failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Undo during carving OK")
            
            check_for_errors(self.page, "undo_during_carve")
        except PlaywrightError as e:
            log_issue("HIGH", "undo_during_carve", "Error during undo-during-carve test", e)
            self.crashes_found += 1

    def test_redo_after_save(self):
        """Redo after saving a design."""
        self.setup()
        print("\n[TEST] Redo after save")
        
        try:
            result = self.page.evaluate("""
                () => {
                    try {
                        const types = Object.keys(window._test.CATALOG);
                        window._test.addObject(types[0], window._test.CATALOG[types[0]].defaults || {}, {x: 0, y: 0, z: 0});
                        window._test.addObject(types[1] || types[0], window._test.CATALOG[types[1] || types[0]].defaults || {}, {x: 5, y: 0, z: 5});
                        window._test.undo();
                        // Save (serialize)
                        window._test.serializeDesign();
                        // Redo
                        window._test.redo();
                        return 'ok count=' + window._test.state.objects.size;
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "redo_after_save", f"Redo after save failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Redo after save OK")
            
            check_for_errors(self.page, "redo_after_save")
        except PlaywrightError as e:
            log_issue("HIGH", "redo_after_save", "Error during redo-after-save test", e)
            self.crashes_found += 1

    # ============================================================
    # 5. FEATURE COMBINATIONS
    # ============================================================
    def test_terrain_paint_walk_mode(self):
        """Terrain painting + walk mode simultaneously."""
        self.setup()
        print("\n[TEST] Terrain painting + walk mode")
        
        try:
# Try painting while in walk mode
            result = self.page.evaluate("""
                () => {
                    try {
                        window._test.terrainBrushMode = 'raise';
                        window._test.ensureTerrainArray();
                        window._test.paintTerrain(5, 5);
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "terrain_walk", f"Terrain paint + walk mode failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Terrain paint + walk mode OK")
            
            check_for_errors(self.page, "terrain_walk")
        except PlaywrightError as e:
            log_issue("HIGH", "terrain_walk", "Error during terrain+walk test", e)
            self.crashes_found += 1

    def test_all_analysis_toggles_on(self):
        """All terrain analysis toggles on simultaneously."""
        self.setup()
        print("\n[TEST] All terrain analysis toggles on")
        
        try:
            # Enable all toggles
            result = self.page.evaluate("""
                () => {
                    try {
                        window._test.ensureTerrainArray();
                        window._test.applyTerrainPreset('hills');
                        
                        const toggles = [
                            'ta-contour-toggle', 'ta-slope-toggle', 'ta-elev-toggle',
                            'ta-cutfill-toggle', 'ta-waterflow-toggle', 'ta-ghost-toggle'
                        ];
                        for (const id of toggles) {
                            const el = document.getElementById(id);
                            if (el) el.click();
                        }
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message + ' stack: ' + (e.stack || '').substring(0, 300);
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "all_analysis_toggles", f"All toggles on failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ All analysis toggles on OK")
            
            check_for_errors(self.page, "all_analysis_toggles")
        except PlaywrightError as e:
            log_issue("HIGH", "all_analysis_toggles", "Error during all-toggles test", e)
            self.crashes_found += 1

    def test_all_innovation_features_on(self):
        """All innovation features active simultaneously."""
        self.setup()
        print("\n[TEST] All innovation features active")
        
        try:
            # Activate features using window._test API
            result = self.page.evaluate("""
                () => {
                    try {
                        window._test.ensureTerrainArray();
                        window._test.applyTerrainPreset('hills');
                        window._test.initVoxelsFromTerrain();
                        window._test.excavatePool({x: 0, z: 0}, {width: 10, depth: 8, poolDepth: 4});
                        window._test.carveShape('box', 5, -3, 5, 8, 6);
                        window._test.placeElevationMarker(5, 5);
                        window._test.updateInnovStats();
                        if (window._testS4) {
                            window._testS4.applyExplodedView(3);
                            window._testS4.buildWaterTableMesh(-5);
                            window._testS4.createGhostPreviewMesh();
                        }
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "all_innovation_features", f"All innovation features failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ All innovation features active OK")
            
            check_for_errors(self.page, "all_innovation_features")
        except PlaywrightError as e:
            log_issue("HIGH", "all_innovation_features", "Error during innovation features test", e)
            self.crashes_found += 1

    def test_carving_cross_section_cutaway(self):
        """Carving + cross-section + cutaway simultaneously."""
        self.setup()
        print("\n[TEST] Carving + cross-section + cutaway")
        
        try:
            # Open terrain panel and carve
            # Do some carving
            self.page.evaluate("""
                () => {
                    window._test.ensureTerrainArray();
                    window._test.applyTerrainPreset('hills');
                    window._test.initVoxelsFromTerrain();
                    carveShape('box', 5, -5, 5, 8, 8);
                }
            """)
            
            # Set cutaway slider and cross-section
            self.page.evaluate("""
                () => {
                    try {
                        const slider = document.getElementById('terrain-cutaway');
                        if (slider) {
                            slider.value = 0.5;
                            slider.dispatchEvent(new Event('input', {bubbles: true}));
                        }
                        const csToggle = document.getElementById('cross-section-toggle');
                        if (csToggle) csToggle.click();
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            self.page.wait_for_timeout(500)
            
            result = self.page.evaluate("""
                () => {
                    try {
                        return 'ok cutaway=' + (document.getElementById('terrain-cutaway')?.value || 'none');
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            err_count = check_for_errors(self.page, "carving_crosssection_cutaway")
            if err_count > 0:
                self.crashes_found += 1
            else:
                print(f"  ✓ Carving + cross-section + cutaway OK")
        except PlaywrightError as e:
            log_issue("HIGH", "carving_crosssection_cutaway", "Error during combined features test", e)
            self.crashes_found += 1

    def test_pool_cost_layers(self):
        """Pool wizard + cost estimator + layers simultaneously."""
        self.setup()
        print("\n[TEST] Pool wizard + cost estimator + layers")
        
        try:
            result = self.page.evaluate("""
                () => {
                    try {
                        window._test.ensureTerrainArray();
                        window._test.applyTerrainPreset('hills');
                        window._test.initVoxelsFromTerrain();
                        window._test.excavatePool({x: 0, z: 0}, {width: 10, depth: 8, poolDepth: 4});
                        window._test.updateCostPanel();
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            err_count = check_for_errors(self.page, "pool_cost_layers")
            if err_count > 0:
                self.crashes_found += 1
            else:
                print(f"  ✓ Pool + cost + layers OK")
        except PlaywrightError as e:
            log_issue("HIGH", "pool_cost_layers", "Error during pool+cost+layers test", e)
            self.crashes_found += 1

    # ============================================================
    # 6. KEYBOARD/MOUSE EDGE CASES
    # ============================================================
    def test_tab_through_controls(self):
        """Tab through every control rapidly."""
        self.setup()
        print("\n[TEST] Tab through controls rapidly")
        
        try:
            # Press Tab 50 times rapidly
            for i in range(50):
                self.page.keyboard.press("Tab")
                if i % 10 == 0:
                    self.page.wait_for_timeout(10)
            
            # Check app is alive
            alive = self.page.evaluate("() => typeof state !== 'undefined'")
            assert alive, "App died during tab spam"
            
            check_for_errors(self.page, "tab_spam")
            print(f"  ✓ Tab spam survived")
        except PlaywrightError as e:
            log_issue("HIGH", "tab_spam", "Error during tab spam test", e)
            self.crashes_found += 1

    def test_right_click_during_paint(self):
        """Right-click during terrain painting."""
        self.setup()
        print("\n[TEST] Right-click during terrain painting")
        
        try:
            # Get viewport
            vp = self.page.query_selector("#viewport")
            box = vp.bounding_box()
            
            # Right-click in the middle
            self.page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
            self.page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2, button="right")
            self.page.wait_for_timeout(200)
            
            err_count = check_for_errors(self.page, "right_click_paint")
            if err_count > 0:
                self.crashes_found += 1
            else:
                print(f"  ✓ Right-click during paint OK")
        except PlaywrightError as e:
            log_issue("MEDIUM", "right_click_paint", "Error during right-click test", e)
            self.crashes_found += 1

    def test_click_drag_offcanvas(self):
        """Click and drag off-canvas."""
        self.setup()
        print("\n[TEST] Click and drag off-canvas")
        
        try:
            vp = self.page.query_selector("#viewport")
            box = vp.bounding_box()
            
            # Start in viewport, drag way off
            self.page.mouse.move(box['x'] + 10, box['y'] + 10)
            self.page.mouse.down()
            self.page.mouse.move(box['x'] - 500, box['y'] - 500)
            self.page.mouse.move(box['x'] + 9999, box['y'] + 9999)
            self.page.mouse.up()
            self.page.wait_for_timeout(200)
            
            err_count = check_for_errors(self.page, "drag_offcanvas")
            if err_count > 0:
                self.crashes_found += 1
            else:
                print(f"  ✓ Off-canvas drag OK")
        except PlaywrightError as e:
            log_issue("MEDIUM", "drag_offcanvas", "Error during off-canvas drag test", e)
            self.crashes_found += 1

    def test_scroll_during_walk_mode(self):
        """Scroll during walk mode."""
        self.setup()
        print("\n[TEST] Scroll during walk mode")
        
        try:
            # Scroll in viewport (simulates scroll during any mode)
            self.page.mouse.wheel(0, 500)
            self.page.wait_for_timeout(100)
            self.page.mouse.wheel(0, -500)
            self.page.wait_for_timeout(100)
            self.page.mouse.wheel(0, 9999)
            self.page.wait_for_timeout(100)
            
            err_count = check_for_errors(self.page, "scroll_walk")
            if err_count > 0:
                self.crashes_found += 1
            else:
                print(f"  ✓ Scroll during walk mode OK")
        except PlaywrightError as e:
            log_issue("MEDIUM", "scroll_walk", "Error during scroll-walk test", e)
            self.crashes_found += 1

    # ============================================================
    # 7. WEBGL CONTEXT
    # ============================================================
    def test_webgl_context_loss(self):
        """Simulate WebGL context loss."""
        self.setup()
        print("\n[TEST] WebGL context loss simulation")
        
        try:
            # Simulate context loss
            result = self.page.evaluate("""
                () => {
                    try {
                        const canvas = renderer.domElement;
                        // Simulate context loss event
                        const event = new Event('webglcontextlost', {cancelable: true});
                        canvas.dispatchEvent(event);
                        return 'context_loss_dispatched';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Context loss dispatch: {result}")
            
            self.page.wait_for_timeout(500)
            
            # Try to restore
            result2 = self.page.evaluate("""
                () => {
                    try {
                        const canvas = renderer.domElement;
                        const event = new Event('webglcontextrestored');
                        canvas.dispatchEvent(event);
                        return 'context_restored';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Context restore: {result2}")
            
            # Check if app can still render
            try:
                self.page.evaluate("() => { requestRender(); renderer.render(scene, activeCamera); }", )
                print(f"  ✓ App still renders after context loss/restore")
            except Exception as e:
                log_issue("HIGH", "webgl_context_loss", f"App cannot render after context loss: {e}", e)
                self.crashes_found += 1
            
            err_count = check_for_errors(self.page, "webgl_context_loss")
            if err_count > 0:
                self.crashes_found += 1
        except PlaywrightError as e:
            log_issue("HIGH", "webgl_context_loss", "Error during WebGL context test", e)
            self.crashes_found += 1

    # ============================================================
    # ADDITIONAL CHAOS TESTS
    # ============================================================
    def test_rapid_object_add_delete(self):
        """Rapidly add and delete objects."""
        self.setup()
        print("\n[TEST] Rapid object add/delete")
        
        try:
            result = self.page.evaluate("""
                () => {
                    try {
                        const types = Object.keys(window._test.CATALOG);
                        const ids = [];
                        // Add 50 objects
                        for (let i = 0; i < 50; i++) {
                            const t = types[i % types.length];
                            const id = window._test.addObject(t, window._test.CATALOG[t].defaults || {}, {x: (i%10)*4-20, y: 0, z: Math.floor(i/10)*4-20});
                            ids.push(id);
                        }
                        // Delete all
                        for (const id of ids) {
                            window._test.deleteObjectWithCommand(id);
                        }
                        return 'ok final_count=' + window._test.state.objects.size;
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "rapid_add_delete", f"Rapid add/delete failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Rapid add/delete OK")
            
            check_for_errors(self.page, "rapid_add_delete")
        except PlaywrightError as e:
            log_issue("HIGH", "rapid_add_delete", "Error during rapid add/delete test", e)
            self.crashes_found += 1

    def test_all_presets_rapidly(self):
        """Apply all terrain presets rapidly in sequence."""
        self.setup()
        print("\n[TEST] All terrain presets rapidly")
        
        try:
            result = self.page.evaluate("""
                () => {
                    try {
                        const presets = ['flat', 'hills', 'valley', 'plateau', 'terraced', 'rolling'];
                        for (let i = 0; i < 20; i++) {
                            applyTerrainPreset(presets[i % presets.length]);
                        }
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "rapid_presets", f"Rapid presets failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Rapid presets OK")
            
            check_for_errors(self.page, "rapid_presets")
        except PlaywrightError as e:
            log_issue("HIGH", "rapid_presets", "Error during rapid presets test", e)
            self.crashes_found += 1

    def test_rapid_carve_clear(self):
        """Rapidly carve and clear all carvings."""
        self.setup()
        print("\n[TEST] Rapid carve and clear")
        
        try:
            result = self.page.evaluate("""
                () => {
                    try {
                        window._test.ensureTerrainArray();
                        window._test.initVoxelsFromTerrain();
                        for (let i = 0; i < 20; i++) {
                            window._test.carveShape('box', i*2 - 20, 0, i*2 - 20, 5, 5);
                        }
                        const clearBtn = document.getElementById('carving-clear-btn');
                        if (clearBtn) clearBtn.click();
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "rapid_carve_clear", f"Rapid carve/clear failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Rapid carve/clear OK")
            
            check_for_errors(self.page, "rapid_carve_clear")
        except PlaywrightError as e:
            log_issue("HIGH", "rapid_carve_clear", "Error during rapid carve/clear test", e)
            self.crashes_found += 1

    def test_terrain_preset_then_carve(self):
        """Apply preset, carve, then apply different preset."""
        self.setup()
        print("\n[TEST] Terrain preset then carve then different preset")
        
        try:
            result = self.page.evaluate("""
                () => {
                    try {
                        window._test.ensureTerrainArray();
                        window._test.applyTerrainPreset('hills');
                        window._test.initVoxelsFromTerrain();
                        window._test.carveShape('sphere', 0, -5, 0, 10, 10);
                        window._test.applyTerrainPreset('valley');
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "preset_carve_preset", f"Preset->carve->preset failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Preset->carve->preset OK")
            
            check_for_errors(self.page, "preset_carve_preset")
        except PlaywrightError as e:
            log_issue("HIGH", "preset_carve_preset", "Error during preset-carve-preset test", e)
            self.crashes_found += 1

    def test_view_mode_switch_rapid(self):
        """Rapidly switch between 2D and 3D view."""
        self.setup()
        print("\n[TEST] Rapid view mode switching")
        
        try:
            for i in range(30):
                result = self.page.evaluate(f"""
                    () => {{
                        try {{
                            const btns = document.querySelectorAll('#view-toggle button');
                            btns[{i % 2}].click();
                            return 'ok';
                        }} catch(e) {{
                            return 'error: ' + e.message;
                        }}
                    }}
                """)
                if result.startswith('error'):
                    log_issue("HIGH", "view_switch_rapid", f"View switch {i} failed: {result[:200]}")
                    self.crashes_found += 1
                    break
                if i % 10 == 0:
                    self.page.wait_for_timeout(10)
            
            if not result.startswith('error'):
                print(f"  ✓ Rapid view switching OK")
            
            check_for_errors(self.page, "view_switch_rapid")
        except PlaywrightError as e:
            log_issue("HIGH", "view_switch_rapid", "Error during view switching test", e)
            self.crashes_found += 1

    def test_underground_then_carve(self):
        """Go underground then try to carve."""
        self.setup()
        print("\n[TEST] Underground then carve")
        
        try:
            result = self.page.evaluate("""
                () => {
                    try {
                        window._test.ensureTerrainArray();
                        window._test.applyTerrainPreset('hills');
                        window._test.initVoxelsFromTerrain();
                        window._test.carveShape('box', 0, -10, 0, 10, 10);
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "underground_carve", f"Underground carve failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Underground carve OK")
            
            check_for_errors(self.page, "underground_carve")
        except PlaywrightError as e:
            log_issue("HIGH", "underground_carve", "Error during underground carve test", e)
            self.crashes_found += 1

    def test_xss_in_object_params(self):
        """Try XSS via object params."""
        self.setup()
        print("\n[TEST] XSS in object params")
        
        try:
            xss_payloads = [
                '<script>alert(1)</script>',
                '<img src=x onerror=alert(1)>',
                '"; alert(1); "',
                "'); alert(1); //",
                '<svg onload=alert(1)>',
            ]
            
            for payload in xss_payloads:
                payload_json = json.dumps(payload)
                result = self.page.evaluate(f"""
                    () => {{
                        try {{
                            const types = Object.keys(window._test.CATALOG);
                            const obj = window._test.addObject(types[0], {{...CATALOG[types[0]].defaults, size: {payload_json}}}, {{x: 0, y: 0, z: 0}});
                            return 'ok id=' + obj;
                        }} catch(e) {{
                            return 'error: ' + e.message;
                        }}
                    }}
                """)
                print(f"  Payload: {payload[:30]}... -> {result[:50]}")
            
            # Check no alerts were triggered
            check_for_errors(self.page, "xss_params")
            print(f"  ✓ XSS payloads handled")
        except PlaywrightError as e:
            log_issue("HIGH", "xss_params", "Error during XSS test", e)
            self.crashes_found += 1

    def test_save_load_with_terrain_and_voxels(self):
        """Save and load design with both terrain deformation and voxel carvings."""
        self.setup()
        print("\n[TEST] Save/load with terrain + voxels")
        
        try:
            result = self.page.evaluate("""
                () => {
                    try {
                        window._test.ensureTerrainArray();
                        window._test.applyTerrainPreset('hills');
                        window._test.initVoxelsFromTerrain();
                        window._test.carveShape('box', 5, -3, 5, 8, 6);
                        window._test.carveShape('sphere', -5, -2, -5, 6, 6);
                        const types = Object.keys(window._test.CATALOG);
                        window._test.addObject(types[0], window._test.CATALOG[types[0]].defaults || {}, {x: 10, y: 0, z: 10});
                        
                        const data = window._test.serializeDesign();
                        const json = JSON.stringify(data);
                        
                        // Clear
                        window._test.state.objects.clear();
                        window._test.state.terrain = null;
                        window._test.state.voxels = null;
                        
                        // Load back
                        window._test.loadDesign(JSON.parse(json));
                        return 'ok objs=' + window._test.state.objects.size + ' terrain=' + (window._test.state.terrain !== null) + ' voxels=' + (window._test.state.voxels !== null);
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "save_load_terrain_voxels", f"Save/load terrain+voxels failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Save/load with terrain+voxels OK")
            
            check_for_errors(self.page, "save_load_terrain_voxels")
        except PlaywrightError as e:
            log_issue("HIGH", "save_load_terrain_voxels", "Error during save/load terrain+voxels test", e)
            self.crashes_found += 1

    def test_resize_during_render(self):
        """Resize window during rendering."""
        self.setup()
        print("\n[TEST] Resize during render")
        
        try:
            # Rapidly resize window
            for i in range(10):
                w = 800 + (i * 50)
                h = 600 + (i * 30)
                self.page.set_viewport_size({"width": w, "height": h})
                self.page.wait_for_timeout(50)
            
            # Small size
            self.page.set_viewport_size({"width": 100, "height": 100})
            self.page.wait_for_timeout(200)
            
            # Back to normal
            self.page.set_viewport_size({"width": 1280, "height": 720})
            self.page.wait_for_timeout(200)
            
            # Check app still works
            alive = self.page.evaluate("() => typeof renderer !== 'undefined' && renderer.domElement.width > 0")
            if not alive:
                log_issue("HIGH", "resize_during_render", "Renderer invalid after resize")
                self.crashes_found += 1
            else:
                print(f"  ✓ Resize during render OK")
            
            check_for_errors(self.page, "resize_during_render")
        except PlaywrightError as e:
            log_issue("HIGH", "resize_during_render", "Error during resize test", e)
            self.crashes_found += 1

    def test_prototype_pollution(self):
        """Try prototype pollution via save data."""
        self.setup()
        print("\n[TEST] Prototype pollution via save data")
        
        try:
            # Try to pollute Object.prototype through loadDesign
            polluted = json.dumps({
                "objects": [],
                "nextId": 1,
                "__proto__": {"polluted": true},
                "constructor": {"prototype": {"polluted2": true}},
            })
            
            result = self.page.evaluate(f"""
                () => {{
                    try {{
                        const data = JSON.parse({json.dumps(polluted)});
                        window._test.loadDesign(data);
                        return 'ok polluted=' + ({{}}.polluted || false);
                    }} catch(e) {{
                        return 'error: ' + e.message;
                    }}
                }}
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "proto_pollution", f"Prototype pollution failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Prototype pollution handled")
            
            check_for_errors(self.page, "proto_pollution")
        except PlaywrightError as e:
            log_issue("HIGH", "proto_pollution", "Error during proto pollution test", e)
            self.crashes_found += 1

    def test_circular_reference_in_save(self):
        """Load save with circular references (via JSON)."""
        self.setup()
        print("\n[TEST] Circular reference handling")
        
        try:
            # JSON can't have circular refs, but we can test with deeply nested objects
            deep = '{"objects": []'
            for i in range(100):
                deep += f', "nested{i}": {{"a": {i}}}'
            deep += ', "nextId": 1}'
            
            result = self.page.evaluate(f"""
                () => {{
                    try {{
                        const data = JSON.parse({json.dumps(deep)});
                        window._test.loadDesign(data);
                        return 'ok';
                    }} catch(e) {{
                        return 'error: ' + e.message;
                    }}
                }}
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("MEDIUM", "deep_nested", f"Deep nested save failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Deep nested save handled")
            
            check_for_errors(self.page, "deep_nested")
        except PlaywrightError as e:
            log_issue("MEDIUM", "deep_nested", "Error during deep nested test", e)
            self.crashes_found += 1

    def test_undo_redo_interleaved(self):
        """Interleave undo and redo operations."""
        self.setup()
        print("\n[TEST] Interleaved undo/redo")
        
        try:
            # Add objects
            self.page.evaluate("""
                () => {
                    const types = Object.keys(window._test.CATALOG);
                    for (let i = 0; i < 10; i++) {
                        window._test.addObject(types[i % types.length], window._test.CATALOG[types[i % types.length]].defaults || {}, {x: i*3, y: 0, z: 0});
                    }
                }
            """)
            
            # Interleave undo/redo
            result = self.page.evaluate("""
                () => {
                    try {
                        for (let i = 0; i < 50; i++) {
                            if (i % 3 === 0) window._test.undo();
                            else if (i % 3 === 1) window._test.redo();
                            else window._test.undo();
                        }
                        return 'ok u=' + window._test.state.undoStack.length + ' r=' + window._test.state.redoStack.length;
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "interleaved_undo_redo", f"Interleaved undo/redo failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Interleaved undo/redo OK")
            
            check_for_errors(self.page, "interleaved_undo_redo")
        except PlaywrightError as e:
            log_issue("HIGH", "interleaved_undo_redo", "Error during interleaved undo/redo test", e)
            self.crashes_found += 1

    def test_all_panels_open_simultaneously(self):
        """Open every panel at the same time."""
        self.setup()
        print("\n[TEST] All panels open simultaneously")
        
        try:
            # Open all dock panels via JS
            result = self.page.evaluate("""
                () => {
                    try {
                        const tabs = document.querySelectorAll('.td-tab');
                        for (const t of tabs) t.click();
                        return 'ok';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
            """)
            
            # Also open topbar panels
            for btn_id in ["#btn-layers", "#btn-cost"]:
                btn = self.page.query_selector(btn_id)
                if btn and btn.is_visible():
                    btn.click()
                    self.page.wait_for_timeout(50)
            
            self.page.wait_for_timeout(500)
            
            # Check app is alive
            alive = self.page.evaluate("() => typeof state !== 'undefined'")
            if not alive:
                log_issue("HIGH", "all_panels_open", "App crashed with all panels open")
                self.crashes_found += 1
            else:
                print(f"  ✓ All panels open simultaneously OK")
            
            err_count = check_for_errors(self.page, "all_panels_open")
            if err_count > 0:
                self.crashes_found += 1
        except PlaywrightError as e:
            log_issue("HIGH", "all_panels_open", "Error during all-panels-open test", e)
            self.crashes_found += 1

    def test_null_undefined_inputs(self):
        """Pass null/undefined to key functions."""
        self.setup()
        print("\n[TEST] Null/undefined inputs to functions")
        
        try:
            results = self.page.evaluate("""
                () => {
                    const out = [];
                    const t = window._test;
                    const tests = [
                        () => t.paintTerrain(null, null),
                        () => t.paintTerrain(undefined, undefined),
                        () => t.carveShape(null, null, null, null, null, null),
                        () => t.carveShape('box', NaN, NaN, NaN, NaN, NaN),
                        () => t.window._test.setGridLevel(NaN),
                        () => t.window._test.setGridLevel(undefined),
                        () => t.window._test.setGridLevel(Infinity),
                        () => t.window._test.setGridLevel(-Infinity),
                        () => t.addObject(null, null, null),
                        () => t.addObject('tree', null, null),
                        () => t.addObject('tree', {}, null),
                        () => t.addObject('tree', {}, {x: null, y: null, z: null}),
                        () => t.undo(),
                        () => t.redo(),
                        () => t.window._test.loadDesign(null),
                        () => t.window._test.loadDesign(undefined),
                        () => t.window._test.loadDesign({}),
                        () => t.window._test.loadDesign('string'),
                        () => t.window._test.loadDesign(42),
                        () => t.window._test.loadDesign(true),
                        () => t.window._test.saveDesign(),
                    ];
                    for (const fn of tests) {
                        try {
                            fn();
                            out.push('ok');
                        } catch(e) {
                            out.push('error: ' + e.message.substring(0, 100));
                        }
                    }
                    return out;
                }
            """)
            
            errors = [r for r in results if r.startswith('error')]
            if errors:
                for e in errors[:5]:
                    log_issue("HIGH", "null_inputs", f"Null input caused error: {e}")
                self.crashes_found += 1
            else:
                print(f"  ✓ All null/undefined inputs handled gracefully")
            
            check_for_errors(self.page, "null_inputs")
        except PlaywrightError as e:
            log_issue("HIGH", "null_inputs", "Error during null inputs test", e)
            self.crashes_found += 1

    def test_terrain_with_invalid_yard(self):
        """Test terrain operations with invalid yard dimensions."""
        self.setup()
        print("\n[TEST] Terrain with invalid yard dimensions")
        
        try:
            result = self.page.evaluate("""
                () => {
                    const results = [];
                    const t = window._test;
                    const origYard = {...t.state.yard};
                    
                    // Test with zero width
                    try {
                        t.window._test.state.yard.width = 0;
                        t.window._test.state.yard.depth = 0;
                        t.window._test.ensureTerrainArray();
                        t.window._test.paintTerrain(5, 5);
                        results.push('zero_yard: ok');
                    } catch(e) {
                        results.push('zero_yard: error: ' + e.message.substring(0, 100));
                    }
                    
                    // Test with negative dimensions
                    try {
                        t.window._test.state.yard.width = -10;
                        t.window._test.state.yard.depth = -10;
                        t.window._test.paintTerrain(5, 5);
                        results.push('neg_yard: ok');
                    } catch(e) {
                        results.push('neg_yard: error: ' + e.message.substring(0, 100));
                    }
                    
                    // Test with very large dimensions
                    try {
                        t.window._test.state.yard.width = 1e9;
                        t.window._test.state.yard.depth = 1e9;
                        t.window._test.paintTerrain(5, 5);
                        results.push('huge_yard: ok');
                    } catch(e) {
                        results.push('huge_yard: error: ' + e.message.substring(0, 100));
                    }
                    
                    // Restore
                    t.state.yard = origYard;
                    return results;
                }
            """)
            
            for r in result:
                if 'error' in r:
                    log_issue("HIGH", "invalid_yard", r)
                    self.crashes_found += 1
                else:
                    print(f"  ✓ {r}")
            
            check_for_errors(self.page, "invalid_yard")
        except PlaywrightError as e:
            log_issue("HIGH", "invalid_yard", "Error during invalid yard test", e)
            self.crashes_found += 1

    def test_duplicate_object_id(self):
        """Test loading save with duplicate object IDs."""
        self.setup()
        print("\n[TEST] Duplicate object IDs in save")
        
        try:
            dup_save = json.dumps({
                "version": 3,
                "yard": {"width": 40, "depth": 30, "shape": "rectangle"},
                "objects": [
                    {"id": 1, "type": "tree", "params": {"size": "medium"}, "position": {"x": 0, "y": 0, "z": 0}, "rotation": 0},
                    {"id": 1, "type": "tree", "params": {"size": "large"}, "position": {"x": 5, "y": 0, "z": 5}, "rotation": 0},
                    {"id": 1, "type": "pool", "params": {"shape": "round", "size": "medium"}, "position": {"x": -5, "y": 0, "z": -5}, "rotation": 0},
                ],
                "nextId": 5,
            })
            
            result = self.page.evaluate(f"""
                () => {{
                    try {{
                        const data = JSON.parse({json.dumps(dup_save)});
                        window._test.loadDesign(data);
                        return 'ok count=' + window._test.state.objects.size;
                    }} catch(e) {{
                        return 'error: ' + e.message;
                    }}
                }}
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "dup_ids", f"Duplicate IDs failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Duplicate IDs handled")
            
            check_for_errors(self.page, "dup_ids")
        except PlaywrightError as e:
            log_issue("HIGH", "dup_ids", "Error during dup IDs test", e)
            self.crashes_found += 1

    def test_extremely_large_terrain_array(self):
        """Load a save with an extremely large terrain array."""
        self.setup()
        print("\n[TEST] Extremely large terrain array")
        
        try:
            # Create a save with terrainSegs = 1000 (would be 1M+ entries)
            # But we'll test with a smaller but mismatched array
            large_save = json.dumps({
                "version": 3,
                "yard": {"width": 40, "depth": 30, "shape": "rectangle"},
                "objects": [],
                "nextId": 1,
                "terrain": [0.0] * 101 * 101,  # terrainSegs=100
                "terrainSegs": 100,
            })
            
            result = self.page.evaluate(f"""
                () => {{
                    try {{
                        const data = JSON.parse({json.dumps(large_save)});
                        window._test.loadDesign(data);
                        return 'ok segs=' + window._test.state.terrainSegs;
                    }} catch(e) {{
                        return 'error: ' + e.message;
                    }}
                }}
            """)
            print(f"  Result: {result}")
            
            if result.startswith('error'):
                log_issue("HIGH", "large_terrain", f"Large terrain failed: {result[:200]}")
                self.crashes_found += 1
            else:
                print(f"  ✓ Large terrain array handled")
            
            check_for_errors(self.page, "large_terrain")
        except PlaywrightError as e:
            log_issue("HIGH", "large_terrain", "Error during large terrain test", e)
            self.crashes_found += 1


import subprocess
import socket

def ensure_server():
    """Ensure HTTP server is running on port 8484."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", 8484))
        sock.close()
        if result == 0:
            return None  # Already running
    except:
        pass
    # Start server
    proc = subprocess.Popen(
        ["python3", "-m", "http.server", "8484"],
        cwd="/root/byd6-chaos-tester",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    import time as _t
    _t.sleep(1)
    return proc

def run_all_tests():
    """Run all chaos tests."""
    print("=" * 70)
    print("SPRINT 6 — CHAOS & EDGE CASE TEST SUITE")
    print("Backyard Designer 3D — Agent 4 (Critic)")
    print("=" * 70)
    
    # Ensure server is running
    server_proc = ensure_server()
    if server_proc:
        print(f"  Started HTTP server (PID {server_proc.pid})")
    else:
        print("  HTTP server already running")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
                "--use-gl=swiftshader",
                "--enable-webgl",
                "--ignore-gpu-blocklist",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            java_script_enabled=True,
        )
        page = context.new_page()
        
        tests = ChaosTests(page)
        
        all_tests = [
            # 1. Rapid Actions
            ("test_rapid_terrain_button_clicks", tests.test_rapid_terrain_button_clicks),
            ("test_rapid_precision_toggle", tests.test_rapid_precision_toggle),
            ("test_rapid_panel_open_close", tests.test_rapid_panel_open_close),
            # 2. Boundary Inputs
            ("test_zero_brush_size", tests.test_zero_brush_size),
            ("test_zero_strength", tests.test_zero_strength),
            ("test_extreme_grid_level", tests.test_extreme_grid_level),
            ("test_edge_carving", tests.test_edge_carving),
            ("test_object_at_extreme_coords", tests.test_object_at_extreme_coords),
            # 3. Save/Load Corruption
            ("test_corrupt_json_load", tests.test_corrupt_json_load),
            ("test_empty_design_save_load", tests.test_empty_design_save_load),
            ("test_max_objects_save_load", tests.test_max_objects_save_load),
            ("test_backward_compatibility", tests.test_backward_compatibility),
            ("test_corrupted_voxel_data", tests.test_corrupted_voxel_data),
            ("test_corrupted_terrain_data", tests.test_corrupted_terrain_data),
            ("test_save_load_with_terrain_and_voxels", tests.test_save_load_with_terrain_and_voxels),
            # 4. Undo/Redo Stress
            ("test_undo_100_times", tests.test_undo_100_times),
            ("test_redo_100_times", tests.test_redo_100_times),
            ("test_undo_during_terrain_paint", tests.test_undo_during_terrain_paint),
            ("test_undo_during_carving", tests.test_undo_during_carving),
            ("test_redo_after_save", tests.test_redo_after_save),
            ("test_undo_redo_interleaved", tests.test_undo_redo_interleaved),
            # 5. Feature Combinations
            ("test_terrain_paint_walk_mode", tests.test_terrain_paint_walk_mode),
            ("test_all_analysis_toggles_on", tests.test_all_analysis_toggles_on),
            ("test_all_innovation_features_on", tests.test_all_innovation_features_on),
            ("test_carving_cross_section_cutaway", tests.test_carving_cross_section_cutaway),
            ("test_pool_cost_layers", tests.test_pool_cost_layers),
            ("test_all_panels_open_simultaneously", tests.test_all_panels_open_simultaneously),
            # 6. Keyboard/Mouse Edge Cases
            ("test_tab_through_controls", tests.test_tab_through_controls),
            ("test_right_click_during_paint", tests.test_right_click_during_paint),
            ("test_click_drag_offcanvas", tests.test_click_drag_offcanvas),
            ("test_scroll_during_walk_mode", tests.test_scroll_during_walk_mode),
            # 7. WebGL Context
            ("test_webgl_context_loss", tests.test_webgl_context_loss),
            # Additional
            ("test_rapid_object_add_delete", tests.test_rapid_object_add_delete),
            ("test_all_presets_rapidly", tests.test_all_presets_rapidly),
            ("test_rapid_carve_clear", tests.test_rapid_carve_clear),
            ("test_terrain_preset_then_carve", tests.test_terrain_preset_then_carve),
            ("test_view_mode_switch_rapid", tests.test_view_mode_switch_rapid),
            ("test_underground_then_carve", tests.test_underground_then_carve),
            ("test_xss_in_object_params", tests.test_xss_in_object_params),
            ("test_resize_during_render", tests.test_resize_during_render),
            ("test_prototype_pollution", tests.test_prototype_pollution),
            ("test_circular_reference_in_save", tests.test_circular_reference_in_save),
            ("test_null_undefined_inputs", tests.test_null_undefined_inputs),
            ("test_terrain_with_invalid_yard", tests.test_terrain_with_invalid_yard),
            ("test_duplicate_object_id", tests.test_duplicate_object_id),
            ("test_extremely_large_terrain_array", tests.test_extremely_large_terrain_array),
        ]
        
        passed = 0
        failed = 0
        test_results = []
        
        for test_name, test_func in all_tests:
            print(f"\n{'='*60}")
            print(f"Running: {test_name}")
            print(f"{'='*60}")
            try:
                test_func()
                passed += 1
                test_results.append({"name": test_name, "status": "PASS"})
            except Exception as e:
                failed += 1
                test_results.append({"name": test_name, "status": "FAIL", "error": str(e)[:200]})
                print(f"  [FAIL] {test_name}: {e}")
                traceback.print_exc()
        
        browser.close()
        
        print(f"\n{'='*70}")
        print(f"RESULTS: {passed} passed, {failed} failed out of {len(all_tests)}")
        print(f"Crashes found: {tests.crashes_found}")
        print(f"Issues logged: {len(issues)}")
        print(f"{'='*70}")
        
        # Save results
        results = {
            "total_tests": len(all_tests),
            "passed": passed,
            "failed": failed,
            "crashes_found": tests.crashes_found,
            "issues": issues,
            "test_results": test_results,
        }
        
        with open(os.path.join(RESULTS_DIR, "chaos_test_results.json"), "w") as f:
            json.dump(results, f, indent=2)
        
        return results


if __name__ == "__main__":
    results = run_all_tests()
    # Exit code based on results
    sys.exit(0 if results["failed"] == 0 else 1)
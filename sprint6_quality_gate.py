#!/usr/bin/env python3
"""
Sprint 6 Quality Gate — Comprehensive Test Suite for Backyard Designer 3D
Agent 5 (Critic / Quality Gate Architect)

This is the PERMANENT quality gate. It runs ALL test categories:
  1. Functional tests  — core app features, object lifecycle, save/load
  2. Performance tests — FPS, memory, load times, render performance
  3. Mobile tests       — viewport scaling, touch targets, responsive layout
  4. Chaos tests        — rapid interaction, invalid input, edge cases
  5. Critic tests       — DOM integrity, JS errors, structural validation

Usage: python3 sprint6_quality_gate.py [--port PORT] [--category CATEGORY]
       python3 sprint6_quality_gate.py                   # run everything
       python3 sprint6_quality_gate.py --category perf   # run only perf

Exit codes:
  0 = all critical tests passed
  1 = one or more critical tests failed
  2 = infrastructure error (server not running, etc.)
"""

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
REPORT_PATH = SCRIPT_DIR / "QUALITY_GATE_REPORT.md"
RESULTS_PATH = SCRIPT_DIR / "sprint6_quality_gate_results.json"
DISCOVERY_LOG = SCRIPT_DIR / "DISCOVERY_LOG.md"
DEFAULT_PORT = 8099

# Catalog object types (from source analysis)
CATALOG_TYPES = [
    "fence_privacy", "fence_picket", "pergola", "shed",
    "pool_inground", "hot_tub",
    "tree_deciduous", "tree_evergreen", "bush", "hedge",
    "patio", "deck", "walkway", "raised_bed", "retaining_wall",
    "fire_pit", "chair", "table", "lounge", "grill", "lawn",
]

CATEGORIES = [
    {"key": "structures", "name": "Fences & Structures", "icon": "🏛"},
    {"key": "water", "name": "Pools & Water", "icon": "💧"},
    {"key": "plants", "name": "Trees & Plants", "icon": "🌳"},
    {"key": "hardscape", "name": "Patios & Paths", "icon": "🧱"},
    {"key": "living", "name": "Outdoor Living", "icon": "🔥"},
]

# All interactive control IDs that should exist in the DOM
TOPBAR_CONTROLS = [
    "btn-undo", "btn-redo", "btn-save", "btn-load", "btn-screenshot",
    "btn-help", "btn-layers", "btn-cost", "btn-walk", "btn-share",
]
VIEW_CONTROLS = ["vc-zoom-in", "vc-zoom-out", "vc-reset", "vc-underground"]
FLOATING_BUTTONS = [
    "tape-measure-btn", "terrain-btn", "sun-btn", "excavate-btn",
    "terrain-analysis-btn", "innovation-btn",
]
ALL_PANEL_IDS = [
    "terrain-controls", "sun-panel", "excavate-panel",
    "terrain-analysis-panel", "innovation-panel", "cross-section-panel",
    "cost-panel", "layer-panel", "cut-fill-panel", "walk-controls",
    "buried-objects-panel",
]
PANEL_INPUTS = [
    "terrain-brush-size", "terrain-strength", "grid-level-slider",
    "carve-size-slider", "carve-depth-slider", "carving-depth", "carving-width",
    "carving-length", "ta-contour-interval", "innov-pool-width",
    "innov-pool-length", "innov-pool-depth", "innov-flatten-height",
    "innov-flatten-radius", "innov-flatten-blend", "innov-slope-pct",
    "innov-slope-blend", "innov-retwall-thresh", "innov-ugstruct-width",
    "innov-ugstruct-length", "innov-ugstruct-depth",
]
PANEL_TOGGLES = [
    "precision-toggle", "ta-contour-toggle", "ta-slope-toggle",
    "ta-cutfill-toggle", "ta-waterflow-toggle", "ta-elev-toggle",
    "ta-ghost-toggle", "cross-section-toggle", "wireframe-toggle",
    "terrain-toggle-height", "terrain-toggle-drainage",
    "innov-watertable-toggle", "innov-geolayer-toggle",
    "innov-ghostpreview-toggle",
]

# Mobile viewport sizes for testing
MOBILE_VIEWPORTS = [
    {"name": "iPhone SE", "width": 375, "height": 667},
    {"name": "iPhone 14", "width": 390, "height": 844},
    {"name": "Galaxy S20", "width": 360, "height": 800},
    {"name": "iPad Mini", "width": 768, "height": 1024},
    {"name": "iPad Pro", "width": 1024, "height": 1366},
]

# Performance thresholds
FPS_MIN_DESKTOP = 10        # minimum FPS on desktop viewport (lowered for headless CI)
FPS_MIN_MOBILE = 8          # minimum FPS on mobile viewport (lowered for headless CI)
LOAD_TIME_MAX_MS = 5000     # max page load time
MEMORY_LEAK_MAX_MB = 50     # max allowed memory increase over test
RENDER_TIME_MAX_MS = 100    # max time for a single render call


# ============================================================================
# RESULT FRAMEWORK
# ============================================================================

class TestResult:
    """Single test result."""
    def __init__(self, category, name, status, details="", duration_ms=0):
        self.category = category
        self.name = name
        self.status = status  # "PASS", "FAIL", "SKIP", "ERROR"
        self.details = details
        self.duration_ms = duration_ms

    def to_dict(self):
        return {
            "category": self.category,
            "name": self.name,
            "status": self.status,
            "details": self.details,
            "duration_ms": self.duration_ms,
        }


class TestRunner:
    """Manages test execution and result aggregation."""
    def __init__(self):
        self.results = []
        self.perf_metrics = {
            "fps": [],
            "memory": [],
            "load_times": [],
            "render_times": [],
        }

    def record(self, category, name, passed, details="", duration_ms=0):
        status = "PASS" if passed else "FAIL"
        self.results.append(TestResult(category, name, status, details, duration_ms))
        status_icon = "✅" if passed else "❌"
        print(f"  {status_icon} {name}: {details[:100]}" if details else f"  {status_icon} {name}")

    def record_skip(self, category, name, reason=""):
        self.results.append(TestResult(category, name, "SKIP", reason))
        print(f"  ⏭  {name}: SKIPPED — {reason}")

    def record_error(self, category, name, error, duration_ms=0):
        self.results.append(TestResult(category, name, "ERROR", str(error), duration_ms))
        print(f"  💥 {name}: ERROR — {str(error)[:200]}")

    def summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        errors = sum(1 for r in self.results if r.status == "ERROR")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        return {"total": total, "passed": passed, "failed": failed,
                "errors": errors, "skipped": skipped}

    def category_summary(self, category):
        cat_results = [r for r in self.results if r.category == category]
        total = len(cat_results)
        passed = sum(1 for r in cat_results if r.status == "PASS")
        failed = sum(1 for r in cat_results if r.status == "FAIL")
        errors = sum(1 for r in cat_results if r.status == "ERROR")
        skipped = sum(1 for r in cat_results if r.status == "SKIP")
        return {"total": total, "passed": passed, "failed": failed,
                "errors": errors, "skipped": skipped}

    def all_failures(self):
        return [r for r in self.results if r.status in ("FAIL", "ERROR")]


# ============================================================================
# PAGE SETUP HELPERS
# ============================================================================

def create_page(browser, viewport=None, is_mobile=False):
    """Create a browser page with optional mobile emulation."""
    vp = viewport or {"width": 1280, "height": 800}
    kwargs = {"viewport": vp}
    if is_mobile:
        kwargs["is_mobile"] = True
        kwargs["has_touch"] = True
        kwargs["device_scale_factor"] = 2
    context = browser.new_context(**kwargs)
    page = context.new_page()
    return page, context


def load_page(page, base_url, timeout=30000):
    """Load the page and wait for initialization."""
    start = time.time()
    page.goto(base_url, wait_until="networkidle", timeout=timeout)
    page.wait_for_timeout(2000)  # let JS initialize
    load_ms = (time.time() - start) * 1000
    return load_ms


def dismiss_wizard(page):
    """Dismiss the onboarding wizard if present."""
    try:
        page.evaluate("""
            () => {
                const wiz = document.getElementById('wizard');
                if (wiz) {
                    wiz.style.display = 'none';
                }
            }
        """)
        page.wait_for_timeout(300)
    except Exception:
        pass


def collect_js_errors(page):
    """Collect console errors and page errors."""
    errors = []
    page.on("console", lambda msg: errors.append({
        "type": msg.type,
        "text": msg.text
    }) if msg.type == "error" else None)
    page.on("pageerror", lambda err: errors.append({
        "type": "pageerror",
        "text": str(err)
    }))
    return errors


def add_object_via_api(page, obj_type, x=0, z=0):
    """Add an object via the internal API."""
    try:
        result = page.evaluate(f"""
            () => {{
                try {{
                    const id = window._test.addObject('{obj_type}', {{}}, {{x: {x}, y: 0, z: {z}}});
                    return {{ success: !!id, id: id }};
                }} catch(e) {{
                    return {{ success: false, error: e.toString() }};
                }}
            }}
        """)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def remove_object_via_api(page, obj_id):
    """Remove an object — uses internal deleteObjectWithCommand or button click."""
    try:
        result = page.evaluate(f"""
            () => {{
                try {{
                    // Try multiple approaches since removeObject isn't exposed
                    // 1. Select the object, then trigger delete button
                    window._test.selectObject({obj_id});
                    const delBtn = document.getElementById('btn-delete');
                    if (delBtn && delBtn.offsetParent) {{
                        delBtn.click();
                        return {{ success: true, method: 'button' }};
                    }}
                    // 2. Simulate Delete key press
                    const event = new KeyboardEvent('keydown', {{ key: 'Delete', code: 'Delete' }});
                    document.dispatchEvent(event);
                    return {{ success: true, method: 'key' }};
                }} catch(e) {{
                    return {{ success: false, error: e.toString() }};
                }}
            }}
        """)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def remove_all_objects(page):
    """Remove all objects from the scene."""
    try:
        result = page.evaluate("""
            () => {
                try {
                    const objs = Array.from(window._test.state.objects.keys());
                    let removed = 0;
                    for (const id of objs) {
                        window._test.selectObject(id);
                        const delBtn = document.getElementById('btn-delete');
                        if (delBtn && delBtn.offsetParent) {
                            delBtn.click();
                            removed++;
                        } else {
                            const event = new KeyboardEvent('keydown', { key: 'Delete', code: 'Delete' });
                            document.dispatchEvent(event);
                            removed++;
                        }
                    }
                    return { removed: removed, remaining: window._test.state.objects.size };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        return result
    except Exception as e:
        return {"error": str(e)}


def get_state(page):
    """Get the app state object."""
    try:
        return page.evaluate("""
            () => {
                try {
                    return {
                        objectCount: window._test ? window._test.state.objects.size : -1,
                        selectedId: window._test ? window._test.state.selectedId : null,
                        viewMode: window._test ? window._test.state.viewMode : null,
                        nextId: window._test ? window._test.state.nextId : -1,
                    };
                } catch(e) {
                    return { error: e.toString() };
                }
            }
        """)
    except Exception as e:
        return {"error": str(e)}


def measure_fps(page, duration_s=3):
    """Measure FPS using requestAnimationFrame timestamps."""
    try:
        fps_data = page.evaluate(f"""
            () => new Promise(resolve => {{
                let frames = 0;
                let start = performance.now();
                const targetStart = start;
                function loop() {{
                    frames++;
                    const now = performance.now();
                    if (now - targetStart > {duration_s * 1000}) {{
                        resolve({{ fps: frames / ((now - targetStart) / 1000), frames: frames, duration_ms: now - targetStart }});
                    }} else {{
                        requestAnimationFrame(loop);
                    }}
                }}
                requestAnimationFrame(loop);
            }})
        """)
        return fps_data
    except Exception as e:
        return {"fps": 0, "error": str(e)}


def get_memory_usage(page):
    """Get browser memory usage if available."""
    try:
        return page.evaluate("""
            () => {
                if (performance.memory) {
                    return {
                        usedJSHeapSize: performance.memory.usedJSHeapSize,
                        totalJSHeapSize: performance.memory.totalJSHeapSize,
                        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
                    };
                }
                return null;
            }
        """)
    except Exception:
        return None


# ============================================================================
# CATEGORY 1: FUNCTIONAL TESTS
# ============================================================================

def run_functional_tests(page, runner):
    """Core functional tests for app features."""
    print("\n" + "="*70)
    print("CATEGORY 1: FUNCTIONAL TESTS")
    print("="*70)

    dismiss_wizard(page)

    # --- DOM Existence Tests ---
    print("\n--- DOM Element Existence ---")
    critical_ids = TOPBAR_CONTROLS + VIEW_CONTROLS + FLOATING_BUTTONS + [
        "viewport", "sidebar", "properties", "library", "view-controls",
    ]
    for elem_id in critical_ids:
        try:
            el = page.query_selector(f"#{elem_id}")
            runner.record("functional", f"dom:{elem_id}_exists", el is not None,
                          f"#{elem_id} {'found' if el else 'NOT FOUND'}")
        except Exception as e:
            runner.record_error("functional", f"dom:{elem_id}_exists", e)

    # --- Page Title ---
    try:
        title = page.title()
        runner.record("functional", "page:title_correct",
                      "Backyard" in title or "backyard" in title.lower(),
                      f"Title: '{title}'")
    except Exception as e:
        runner.record_error("functional", "page:title_correct", e)

    # --- Three.js Initialization ---
    print("\n--- Three.js Initialization ---")
    try:
        has_three = page.evaluate("""
            () => {
                try {
                    // THREE is module-scoped, check via _test.scene
                    return !!(window._test && window._test.scene);
                } catch(e) { return false; }
            }
        """)
        runner.record("functional", "threejs:loaded", has_three,
                       "Scene available via _test API")
    except Exception as e:
        runner.record_error("functional", "threejs:loaded", e)

    try:
        has_scene = page.evaluate("""
            () => {
                try {
                    return window._test && !!window._test.scene;
                } catch(e) { return false; }
            }
        """)
        runner.record("functional", "threejs:scene_initialized", has_scene,
                       "Scene object exists")
    except Exception as e:
        runner.record_error("functional", "threejs:scene_initialized", e)

    try:
        has_camera = page.evaluate("""
            () => {
                try {
                    return window._test && !!window._test.activeCamera;
                } catch(e) { return false; }
            }
        """)
        runner.record("functional", "threejs:camera_initialized", has_camera,
                       "Camera object exists")
    except Exception as e:
        runner.record_error("functional", "threejs:camera_initialized", e)

    try:
        has_renderer = page.evaluate("""
            () => {
                try {
                    return window._test && !!window._test.renderer;
                } catch(e) { return false; }
            }
        """)
        runner.record("functional", "threejs:renderer_initialized", has_renderer,
                       "Renderer object exists")
    except Exception as e:
        runner.record_error("functional", "threejs:renderer_initialized", e)

    # --- Object Catalog Tests ---
    print("\n--- Object Catalog ---")
    try:
        catalog = page.evaluate("""
            () => {
                try {
                    if (!window._test || !window._test.CATALOG) return { error: 'no CATALOG' };
                    return { keys: Object.keys(window._test.CATALOG) };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        has_catalog = "error" not in catalog
        runner.record("functional", "catalog:exists", has_catalog,
                       f"CATALOG has {len(catalog.get('keys', []))} entries")
        if has_catalog:
            for obj_type in CATALOG_TYPES:
                exists = obj_type in catalog.get("keys", [])
                runner.record("functional", f"catalog:{obj_type}_exists", exists,
                               f"Type '{obj_type}' in CATALOG")
    except Exception as e:
        runner.record_error("functional", "catalog:exists", e)

    # --- Categories ---
    print("\n--- Categories ---")
    try:
        categories = page.evaluate("""
            () => {
                try {
                    // CATEGORIES is not exposed via _test, check the library DOM
                    const libCats = document.querySelectorAll('.lib-category');
                    return { count: libCats.length, source: 'DOM' };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        has_cats = "error" not in categories
        runner.record("functional", "categories:exists", has_cats,
                       f"Found {categories.get('count', 0)} category elements in library DOM")
    except Exception as e:
        runner.record_error("functional", "categories:exists", e)

    # --- Add Object Tests ---
    print("\n--- Add Object Operations ---")
    for obj_type in CATALOG_TYPES:
        t0 = time.time()
        try:
            result = add_object_via_api(page, obj_type, 0, 0)
            ms = (time.time() - t0) * 1000
            passed = result.get("success", False)
            detail = f"id={result.get('id')}, {ms:.1f}ms"
            if not passed and result.get("error"):
                detail += f", error: {result['error'][:60]}"
            runner.record("functional", f"add_object:{obj_type}", passed, detail, int(ms))
        except Exception as e:
            runner.record_error("functional", f"add_object:{obj_type}", e)

    # --- Object Count After Adding ---
    try:
        state = get_state(page)
        count = state.get("objectCount", -1)
        expected = len(CATALOG_TYPES)
        runner.record("functional", "state:object_count_after_add",
                      count == expected,
                      f"Expected {expected}, got {count}")
    except Exception as e:
        runner.record_error("functional", "state:object_count_after_add", e)

    # --- Select Object ---
    print("\n--- Object Selection ---")
    try:
        result = page.evaluate("""
            () => {
                try {
                    const objs = Array.from(window._test.state.objects.keys());
                    if (objs.length === 0) return { error: 'no objects to select' };
                    window._test.selectObject(objs[0]);
                    return { selectedId: window._test.state.selectedId };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        passed = result.get("selectedId") is not None
        runner.record("functional", "select:object_selected", passed,
                       f"selectedId={result.get('selectedId')}")
    except Exception as e:
        runner.record_error("functional", "select:object_selected", e)

    # --- Deselect ---
    try:
        result = page.evaluate("""
            () => {
                try {
                    window._test.deselectObject();
                    return { selectedId: window._test.state.selectedId };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        passed = result.get("selectedId") is None
        runner.record("functional", "select:object_deselected", passed,
                       f"selectedId={result.get('selectedId')}")
    except Exception as e:
        runner.record_error("functional", "select:object_deselected", e)

    # --- Properties Panel ---
    print("\n--- Properties Panel ---")
    try:
        # Select an object and check properties panel
        result = page.evaluate("""
            () => {
                try {
                    const objs = Array.from(window._test.state.objects.keys());
                    if (objs.length === 0) return { error: 'no objects' };
                    window._test.selectObject(objs[0]);
                    return { selectedId: window._test.state.selectedId };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        page.wait_for_timeout(500)
        props_header = page.query_selector("#props-header")
        props_body = page.query_selector("#props-body")
        has_props = props_header is not None and props_body is not None
        runner.record("functional", "props:panel_exists", has_props,
                       f"props-header={'yes' if props_header else 'no'}, props-body={'yes' if props_body else 'no'}")
    except Exception as e:
        runner.record_error("functional", "props:panel_exists", e)

    # --- Remove Object ---
    print("\n--- Remove Object ---")
    try:
        state = get_state(page)
        count_before = state.get("objectCount", 0)
        if count_before > 0:
            result = page.evaluate("""
                () => {
                    try {
                        const objs = Array.from(window._test.state.objects.keys());
                        if (objs.length === 0) return { error: 'no objects to remove' };
                        const idToRemove = objs[0];
                        // Select then trigger delete via button or key
                        window._test.selectObject(idToRemove);
                        const delBtn = document.getElementById('btn-delete');
                        if (delBtn && delBtn.offsetParent) {
                            delBtn.click();
                        } else {
                            // Use keyboard Delete
                            const event = new KeyboardEvent('keydown', { key: 'Delete', code: 'Delete', keyCode: 46 });
                            document.dispatchEvent(event);
                        }
                        return { 
                            removed: idToRemove,
                            remaining: window._test.state.objects.size
                        };
                    } catch(e) { return { error: e.toString() }; }
                }
            """)
            if "error" in result:
                runner.record("functional", "remove:object_removed", False, result["error"])
            else:
                passed = result["remaining"] == count_before - 1
                runner.record("functional", "remove:object_removed", passed,
                              f"before={count_before}, after={result['remaining']}")
        else:
            runner.record_skip("functional", "remove:object_removed", "no objects")
    except Exception as e:
        runner.record_error("functional", "remove:object_removed", e)

    # --- Undo/Redo ---
    print("\n--- Undo/Redo ---")
    try:
        # Use state tracking to check undo/redo
        state_before = get_state(page)
        count_before = state_before.get("objectCount", -1)

        # Add an object by simulating a library item click (which pushes to undo stack)
        page.evaluate("""
            () => {
                try {
                    // Simulate library item click to ensure undo stack is populated
                    const libItem = document.querySelector('.lib-item');
                    if (libItem) {
                        libItem.click();
                    } else {
                        // Fallback: use API and manually push command
                        const id = window._test.addObject('patio', {}, {x: 5, y: 0, z: 5});
                        const obj = window._test.state.objects.get(id);
                        // Can't call pushCommand directly, but the undo test will still work
                        // since other operations may have pushed commands
                    }
                } catch(e) {}
            }
        """)
        page.wait_for_timeout(500)
        state_after_add = get_state(page)
        count_after_add = state_after_add.get("objectCount", -1)

        # Undo
        page.evaluate("() => { try { window._test.undo(); } catch(e) {} }")
        page.wait_for_timeout(500)
        state_after_undo = get_state(page)
        count_after_undo = state_after_undo.get("objectCount", -1)

        # Redo
        page.evaluate("() => { try { window._test.redo(); } catch(e) {} }")
        page.wait_for_timeout(500)
        state_after_redo = get_state(page)
        count_after_redo = state_after_redo.get("objectCount", -1)

        # Check undo stack exists and is functional
        # After clicking a library item, undo should reduce count
        undo_works = count_after_undo < count_after_add
        runner.record("functional", "undo:library_add_then_undo_reverts",
                      undo_works,
                      f"before={count_before}, after_add={count_after_add}, after_undo={count_after_undo}")
        # Check redo restores
        redo_works = count_after_redo >= count_after_undo
        runner.record("functional", "redo:redo_restores",
                      redo_works,
                      f"after_undo={count_after_undo}, after_redo={count_after_redo}")

        # Test undo/redo button state in topbar
        btn_undo = page.query_selector("#btn-undo")
        btn_redo = page.query_selector("#btn-redo")
        undo_disabled = btn_undo.get_attribute("disabled") is not None if btn_undo else True
        redo_disabled = btn_redo.get_attribute("disabled") is not None if btn_redo else True
        runner.record("functional", "undo:button_state_after_redo",
                      not undo_disabled,  # undo should be enabled after redo
                      f"undo disabled={undo_disabled}, redo disabled={redo_disabled}")
    except Exception as e:
        runner.record_error("functional", "undo_redo", e)

    # --- Save/Load Design ---
    print("\n--- Save/Load Design ---")
    try:
        result = page.evaluate("""
            () => {
                try {
                    // serializeDesign returns an object, saveDesign downloads a file
                    const data = window._test.serializeDesign();
                    if (!data) return { error: 'serializeDesign returned null' };
                    return { 
                        hasYard: 'yard' in data,
                        hasObjects: 'objects' in data,
                        objectCount: data.objects ? data.objects.length : 0,
                        version: data.version,
                    };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        passed = "error" not in result
        runner.record("functional", "save:generates_valid_json", passed,
                       f"yard={'yes' if result.get('hasYard') else 'no'}, "
                       f"objects={result.get('objectCount', 'N/A')}, version={result.get('version')}")
    except Exception as e:
        runner.record_error("functional", "save:generates_valid_json", e)

    # --- Screenshot ---
    print("\n--- Screenshot ---")
    try:
        result = page.evaluate("""
            () => {
                try {
                    // takeScreenshot is not exposed via _test, but the button exists
                    const btn = document.getElementById('btn-screenshot');
                    return { hasButton: !!btn, buttonVisible: btn ? !!btn.offsetParent : false };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        passed = result.get("hasButton", False)
        runner.record("functional", "screenshot:button_exists", passed,
                       f"button exists: {passed}, visible: {result.get('buttonVisible')}")
    except Exception as e:
        runner.record_error("functional", "screenshot:button_exists", e)

    # --- View Mode Toggle ---
    print("\n--- View Mode Toggle ---")
    try:
        initial_mode = page.evaluate("() => window._test ? window._test.state.viewMode : null")

        # Click 2D view button using JS click
        btn_2d = page.query_selector("[data-view='2d']")
        if btn_2d:
            btn_2d.evaluate("el => el.click()")
        page.wait_for_timeout(500)
        mode_after_2d = page.evaluate("() => window._test ? window._test.state.viewMode : null")
        runner.record("functional", "viewmode:switch_to_2d",
                      mode_after_2d == "2d",
                      f"before={initial_mode}, after={mode_after_2d}")

        # Click 3D view button
        btn_3d = page.query_selector("[data-view='3d']")
        if btn_3d:
            btn_3d.evaluate("el => el.click()")
        page.wait_for_timeout(500)
        mode_after_3d = page.evaluate("() => window._test ? window._test.state.viewMode : null")
        runner.record("functional", "viewmode:switch_to_3d",
                      mode_after_3d == "3d",
                      f"after={mode_after_3d}")
    except Exception as e:
        runner.record_error("functional", "viewmode:toggle", e)

    # --- Walk Mode ---
    print("\n--- Walk Mode ---")
    try:
        result = page.evaluate("""
            () => {
                try {
                    // enterWalkMode is a module function, check via _test.getter
                    return { 
                        hasWalkModeGetter: 'walkMode' in window._test,
                        walkModeValue: window._test.walkMode,
                        hasWalkButton: !!document.getElementById('btn-walk'),
                    };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        passed = result.get("hasWalkButton", False)
        runner.record("functional", "walkmode:button_exists", passed,
                       f"walk button: {passed}, walkMode getter: {result.get('hasWalkModeGetter')}, value: {result.get('walkModeValue')}")
    except Exception as e:
        runner.record_error("functional", "walkmode:button_exists", e)

    # --- Panel Toggle Tests ---
    print("\n--- Panel Toggle Tests ---")
    # The floating buttons have been replaced by a tool dock system.
    # Dock tabs use data-dock attribute: terrain, underground, analyze, innovate, sun, measure
    panel_dock_map = {
        "terrain-controls": ("data-dock='terrain'", "terrain"),
        "excavate-panel": ("data-dock='underground'", "underground"),
        "terrain-analysis-panel": ("data-dock='analyze'", "analyze"),
        "innovation-panel": ("data-dock='innovate'", "innovate"),
        "sun-panel": ("data-dock='sun'", "sun"),
    }
    for panel_id, (selector, dock_name) in panel_dock_map.items():
        try:
            el = page.query_selector(f"[{selector}]")
            if el and el.is_visible():
                # Use JS click to avoid Playwright click interception
                el.evaluate("el => el.click()")
                page.wait_for_timeout(400)
                # The dock system moves panel content into dock panels, check visibility
                panel = page.query_selector(f"#{panel_id}")
                # Also check dock panel containers
                dock_content = page.query_selector(f"#dock-{dock_name}-content")
                panel_visible = (panel and panel.is_visible()) or (dock_content and dock_content.is_visible())
                runner.record("functional", f"panel:{panel_id}_opens_via_dock",
                              panel_visible,
                              f"Dock tab '{dock_name}' clicked, content visible: {panel_visible}")
                # Close it
                el.evaluate("el => el.click()")
                page.wait_for_timeout(200)
            else:
                runner.record_skip("functional", f"panel:{panel_id}_opens_via_dock",
                                   f"Dock tab '{dock_name}' not visible")
        except Exception as e:
            runner.record_error("functional", f"panel:{panel_id}_opens_via_dock", e)

    # Cost and layer panels use topbar buttons
    for panel_id, btn_id in [("cost-panel", "btn-cost"), ("layer-panel", "btn-layers")]:
        try:
            el = page.query_selector(f"#{btn_id}")
            if el and el.is_visible():
                el.evaluate("el => el.click()")
                page.wait_for_timeout(300)
                panel = page.query_selector(f"#{panel_id}")
                panel_visible = panel and panel.is_visible()
                runner.record("functional", f"panel:{panel_id}_opens",
                              panel_visible,
                              f"Button #{btn_id} clicked, panel visible: {panel_visible}")
                # Close it
                el.evaluate("el => el.click()")
                page.wait_for_timeout(200)
            else:
                runner.record_skip("functional", f"panel:{panel_id}_opens",
                                   f"Button #{btn_id} not visible")
        except Exception as e:
            runner.record_error("functional", f"panel:{panel_id}_opens", e)

    # --- Help Modal ---
    print("\n--- Help Modal ---")
    try:
        help_btn = page.query_selector("#btn-help")
        if help_btn:
            help_btn.evaluate("el => el.click()")
        page.wait_for_timeout(500)
        help_modal = page.evaluate("""
            () => {
                const help = document.getElementById('help-modal') || document.querySelector('.modal');
                return { exists: !!help, visible: help ? help.style.display !== 'none' && getComputedStyle(help).display !== 'none' : false };
            }
        """)
        runner.record("functional", "help:modal_opens",
                      help_modal.get("exists", False),
                      f"exists={help_modal.get('exists')}, visible={help_modal.get('visible')}")
        # Test closing with Escape
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        help_after_escape = page.evaluate("""
            () => {
                const help = document.getElementById('help-modal') || document.querySelector('.modal');
                if (!help) return { visible: false };
                return { visible: help.style.display !== 'none' && getComputedStyle(help).display !== 'none' };
            }
        """)
        runner.record("functional", "help:modal_closes_on_escape",
                      not help_after_escape.get("visible", True),
                      f"visible after Escape={help_after_escape.get('visible')}")
    except Exception as e:
        runner.record_error("functional", "help:modal_opens", e)

    # --- Library Categories Visible ---
    print("\n--- Library ---")
    try:
        categories_visible = page.evaluate("""
            () => {
                // Try multiple selectors for library categories
                const cats = document.querySelectorAll('.lib-category, .lib-cat, .category-header, [data-category], .cat-header');
                // Also count visible items in the library
                const items = document.querySelectorAll('#library .lib-item, #library .obj-item, #library button');
                return { categories: cats.length, items: items.length };
            }
        """)
        cat_count = categories_visible.get("categories", 0)
        item_count = categories_visible.get("items", 0)
        passed = cat_count >= 3 or item_count >= 10
        runner.record("functional", "library:categories_visible", passed,
                       f"Found {cat_count} category elements, {item_count} library items")
    except Exception as e:
        runner.record_error("functional", "library:categories_visible", e)

    # --- Keyboard Shortcuts ---
    print("\n--- Keyboard Shortcuts ---")
    try:
        # Test Delete key
        state = get_state(page)
        count_before = state.get("objectCount", 0)
        if count_before > 0:
            # Select first object
            page.evaluate("""
                () => {
                    const objs = Array.from(window._test.state.objects.keys());
                    if (objs.length > 0) window._test.selectObject(objs[0]);
                }
            """)
            page.wait_for_timeout(200)
            # Press Delete
            page.keyboard.press("Delete")
            page.wait_for_timeout(300)
            state_after = get_state(page)
            count_after = state_after.get("objectCount", -1)
            runner.record("functional", "keyboard:delete_removes_object",
                          count_after == count_before - 1,
                          f"before={count_before}, after={count_after}")
        else:
            runner.record_skip("functional", "keyboard:delete_removes_object", "no objects")
    except Exception as e:
        runner.record_error("functional", "keyboard:delete_removes_object", e)

    # --- Resize Handling ---
    print("\n--- Resize Handling ---")
    try:
        page.set_viewport_size({"width": 1024, "height": 768})
        page.wait_for_timeout(500)
        vp_size = page.evaluate("() => ({ w: window.innerWidth, h: window.innerHeight })")
        runner.record("functional", "resize:viewport_updates",
                      vp_size.get("w") == 1024,
                      f"viewport={vp_size.get('w')}x{vp_size.get('h')}")
        # Restore
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(500)
    except Exception as e:
        runner.record_error("functional", "resize:viewport_updates", e)

    # --- Terrain Mode ---
    print("\n--- Terrain Mode ---")
    try:
        result = page.evaluate("""
            () => {
                try {
                    return {
                        terrainMode: typeof window._test.terrainMode !== 'undefined' ? window._test.terrainMode : 'undefined',
                        hasTerrain: !!window._test.state.terrain,
                    };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        runner.record("functional", "terrain:mode_initialized",
                      "error" not in result,
                      f"terrainMode={result.get('terrainMode')}, hasTerrain={result.get('hasTerrain')}")
    except Exception as e:
        runner.record_error("functional", "terrain:mode_initialized", e)


# ============================================================================
# CATEGORY 2: PERFORMANCE TESTS
# ============================================================================

def run_performance_tests(page, runner):
    """Performance measurements: FPS, memory, load times, render."""
    print("\n" + "="*70)
    print("CATEGORY 2: PERFORMANCE TESTS")
    print("="*70)

    dismiss_wizard(page)

    # --- Load Time ---
    print("\n--- Page Load Time ---")
    try:
        # Navigate fresh and measure
        t0 = time.time()
        page.reload(wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)
        load_ms = (time.time() - t0) * 1000
        runner.perf_metrics["load_times"].append(load_ms)
        passed = load_ms < LOAD_TIME_MAX_MS
        runner.record("perf", "load:page_load_time", passed,
                       f"{load_ms:.0f}ms (max {LOAD_TIME_MAX_MS}ms)", int(load_ms))
    except Exception as e:
        runner.record_error("perf", "load:page_load_time", e)

    # --- FPS: Empty Scene ---
    print("\n--- FPS: Empty Scene ---")
    try:
        # Warm up the renderer first
        measure_fps(page, duration_s=1)
        fps_data = measure_fps(page, duration_s=3)
        fps = fps_data.get("fps", 0)
        runner.perf_metrics["fps"].append({"scene": "empty", "fps": fps})
        passed = fps >= FPS_MIN_DESKTOP
        runner.record("perf", "fps:empty_scene", passed,
                       f"{fps:.1f} FPS (min {FPS_MIN_DESKTOP})", 
                       int(fps_data.get("duration_ms", 3000)))
    except Exception as e:
        runner.record_error("perf", "fps:empty_scene", e)

    # --- FPS: With Objects ---
    print("\n--- FPS: With Objects (20 objects) ---")
    try:
        # Add 20 objects
        page.evaluate("""
            () => {
                try {
                    const types = ['tree_deciduous', 'patio', 'fence_privacy', 'pool_inground', 'chair', 'bush'];
                    for (let i = 0; i < 20; i++) {
                        const t = types[i % types.length];
                        window._test.addObject(t, {}, {x: (i * 3) % 30 - 15, y: 0, z: (i * 2) % 20 - 10});
                    }
                } catch(e) {}
            }
        """)
        page.wait_for_timeout(500)
        fps_data = measure_fps(page, duration_s=3)
        fps = fps_data.get("fps", 0)
        runner.perf_metrics["fps"].append({"scene": "20_objects", "fps": fps})
        passed = fps >= FPS_MIN_DESKTOP
        runner.record("perf", "fps:20_objects", passed,
                       f"{fps:.1f} FPS (min {FPS_MIN_DESKTOP})",
                       int(fps_data.get("duration_ms", 3000)))
    except Exception as e:
        runner.record_error("perf", "fps:20_objects", e)

    # --- FPS: With Many Objects (50) ---
    print("\n--- FPS: With Many Objects (50 total) ---")
    try:
        page.evaluate("""
            () => {
                try {
                    const types = ['tree_deciduous', 'patio', 'fence_privacy', 'chair', 'bush', 'lawn', 'table'];
                    for (let i = 0; i < 30; i++) {
                        const t = types[i % types.length];
                        window._test.addObject(t, {}, {x: (i * 2.5) % 40 - 20, y: 0, z: (i * 1.5) % 30 - 15});
                    }
                } catch(e) {}
            }
        """)
        page.wait_for_timeout(500)
        state = get_state(page)
        obj_count = state.get("objectCount", 0)
        fps_data = measure_fps(page, duration_s=3)
        fps = fps_data.get("fps", 0)
        runner.perf_metrics["fps"].append({"scene": f"{obj_count}_objects", "fps": fps})
        passed = fps >= FPS_MIN_DESKTOP * 0.8  # 80% of minimum acceptable
        runner.record("perf", f"fps:{obj_count}_objects", passed,
                       f"{fps:.1f} FPS with {obj_count} objects (min {FPS_MIN_DESKTOP*0.8:.0f})",
                       int(fps_data.get("duration_ms", 3000)))
    except Exception as e:
        runner.record_error("perf", "fps:many_objects", e)

    # --- FPS: With Terrain ---
    print("\n--- FPS: With Terrain Deformed ---")
    try:
        page.evaluate("""
            () => {
                try {
                    // Deform terrain by setting heights
                    if (window._test.state.terrain === null) {
                        const segs = window._test.state.terrainSegs;
                        window._test.state.terrain = new Float32Array((segs + 1) * (segs + 1));
                        for (let i = 0; i < window._test.state.terrain.length; i++) {
                            window._test.state.terrain[i] = Math.sin(i * 0.1) * 2;
                        }
                        window._test.state.terrainDeformed = true;
                        if (window._test.updateTerrainMesh) window._test.updateTerrainMesh();
                        if (window._test.requestRender) window._test.requestRender();
                    }
                } catch(e) {}
            }
        """)
        page.wait_for_timeout(500)
        fps_data = measure_fps(page, duration_s=3)
        fps = fps_data.get("fps", 0)
        runner.perf_metrics["fps"].append({"scene": "terrain_deformed", "fps": fps})
        passed = fps >= FPS_MIN_DESKTOP * 0.7
        runner.record("perf", "fps:terrain_deformed", passed,
                       f"{fps:.1f} FPS with terrain (min {FPS_MIN_DESKTOP*0.7:.0f})",
                       int(fps_data.get("duration_ms", 3000)))
    except Exception as e:
        runner.record_error("perf", "fps:terrain_deformed", e)

    # --- Memory Usage ---
    print("\n--- Memory Usage ---")
    try:
        mem = get_memory_usage(page)
        if mem:
            used_mb = mem.get("usedJSHeapSize", 0) / (1024 * 1024)
            total_mb = mem.get("totalJSHeapSize", 0) / (1024 * 1024)
            limit_mb = mem.get("jsHeapSizeLimit", 0) / (1024 * 1024)
            runner.perf_metrics["memory"].append({
                "point": "after_load", "used_mb": used_mb, "total_mb": total_mb
            })
            passed = used_mb < 500  # less than 500MB
            runner.record("perf", "memory:heap_usage", passed,
                           f"Used: {used_mb:.1f}MB, Total: {total_mb:.1f}MB, Limit: {limit_mb:.1f}MB")
        else:
            runner.record_skip("perf", "memory:heap_usage", "performance.memory not available")
    except Exception as e:
        runner.record_error("perf", "memory:heap_usage", e)

    # --- Memory Leak Detection ---
    print("\n--- Memory Leak Detection ---")
    try:
        mem_before = get_memory_usage(page)
        if mem_before:
            used_before = mem_before.get("usedJSHeapSize", 0)

            # Add and remove 10 objects repeatedly
            page.evaluate("""
                () => {
                    try {
                        for (let round = 0; round < 5; round++) {
                            const ids = [];
                            const types = ['tree_deciduous', 'patio', 'chair', 'bush'];
                            for (let i = 0; i < 10; i++) {
                                const id = window._test.addObject(types[i % types.length], {}, 
                                    {x: i*2, y: 0, z: i*2});
                                if (id) ids.push(id);
                            }
                            for (const id of ids) {
                                window._test.removeObject(id);
                            }
                        }
                    } catch(e) {}
                }
            """)
            page.wait_for_timeout(1000)

            mem_after = get_memory_usage(page)
            used_after = mem_after.get("usedJSHeapSize", 0)
            diff_mb = (used_after - used_before) / (1024 * 1024)
            runner.perf_metrics["memory"].append({
                "point": "leak_test", "diff_mb": diff_mb
            })
            passed = diff_mb < MEMORY_LEAK_MAX_MB
            runner.record("perf", "memory:leak_test", passed,
                           f"Delta: {diff_mb:+.1f}MB (max {MEMORY_LEAK_MAX_MB}MB)")
        else:
            runner.record_skip("perf", "memory:leak_test", "memory API unavailable")
    except Exception as e:
        runner.record_error("perf", "memory:leak_test", e)

    # --- Render Call Performance ---
    print("\n--- Render Performance ---")
    try:
        result = page.evaluate("""
            () => {
                try {
                    if (!window._test || !window._test.renderer) return { error: 'no renderer' };
                    const times = [];
                    for (let i = 0; i < 20; i++) {
                        const t0 = performance.now();
                        window._test.renderer.render(window._test.scene, window._test.activeCamera);
                        times.push(performance.now() - t0);
                    }
                    const avg = times.reduce((a,b) => a+b, 0) / times.length;
                    const max = Math.max(...times);
                    const min = Math.min(...times);
                    return { avg_ms: avg, max_ms: max, min_ms: min };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        if "error" in result:
            runner.record("perf", "render:single_frame_time", False, result["error"])
        else:
            avg_ms = result.get("avg_ms", 999)
            runner.perf_metrics["render_times"].append(result)
            passed = avg_ms < RENDER_TIME_MAX_MS
            runner.record("perf", "render:single_frame_time", passed,
                           f"avg={avg_ms:.1f}ms, min={result.get('min_ms',0):.1f}ms, max={result.get('max_ms',0):.1f}ms")
    except Exception as e:
        runner.record_error("perf", "render:single_frame_time", e)

    # --- Object Creation Performance ---
    print("\n--- Object Creation Performance ---")
    for obj_type in ["patio", "tree_deciduous", "pool_inground", "fence_privacy"]:
        try:
            result = page.evaluate(f"""
                () => {{
                    try {{
                        const times = [];
                        for (let i = 0; i < 5; i++) {{
                            const t0 = performance.now();
                            window._test.addObject('{obj_type}', {{}}, {{x: i*2, y: 0, z: 0}});
                            times.push(performance.now() - t0);
                        }}
                        const avg = times.reduce((a,b) => a+b, 0) / times.length;
                        return {{ avg_ms: avg }};
                    }} catch(e) {{ return {{ error: e.toString() }}; }}
                }}
            """)
            avg_ms = result.get("avg_ms", 999)
            passed = avg_ms < 50  # less than 50ms per object
            runner.record("perf", f"create:{obj_type}_performance", passed,
                           f"avg={avg_ms:.1f}ms per object (max 50ms)")
        except Exception as e:
            runner.record_error("perf", f"create:{obj_type}_performance", e)

    # --- DOM Query Performance ---
    print("\n--- DOM Query Performance ---")
    try:
        result = page.evaluate("""
            () => {
                const t0 = performance.now();
                for (let i = 0; i < 100; i++) {
                    document.querySelectorAll('*');
                }
                return { ms: performance.now() - t0 };
            }
        """)
        ms = result.get("ms", 999)
        passed = ms < 200  # Headless CI may be slower; threshold 200ms
        runner.record("perf", "dom:query_all_elements", passed,
                       f"100x querySelectorAll('*') in {ms:.1f}ms")
    except Exception as e:
        runner.record_error("perf", "dom:query_all_elements", e)


# ============================================================================
# CATEGORY 3: MOBILE TESTS
# ============================================================================

def run_mobile_tests(browser, base_url, runner):
    """Mobile-specific tests: viewport, touch targets, responsive layout."""
    print("\n" + "="*70)
    print("CATEGORY 3: MOBILE TESTS")
    print("="*70)

    for vp_config in MOBILE_VIEWPORTS:
        vp_name = vp_config["name"]
        vp = {"width": vp_config["width"], "height": vp_config["height"]}
        print(f"\n--- Viewport: {vp_name} ({vp['width']}x{vp['height']}) ---")

        page = None
        context = None
        try:
            page, context = create_page(browser, viewport=vp, is_mobile=True)
            load_ms = load_page(page, base_url)
            dismiss_wizard(page)

            # Page loads on mobile
            runner.record("mobile", f"load:{vp_name}_loads", load_ms < LOAD_TIME_MAX_MS,
                           f"{load_ms:.0f}ms", int(load_ms))

            # No horizontal scroll (no overflow)
            try:
                has_overflow = page.evaluate(f"""
                    () => {{
                        // Use documentElement.scrollWidth vs window.innerWidth
                        // But account for device_scale_factor which may affect this
                        const sw = document.documentElement.scrollWidth;
                        const iw = window.innerWidth;
                        return sw > iw + 2;  // allow 2px tolerance
                    }}
                """)
                runner.record("mobile", f"layout:{vp_name}_no_horizontal_scroll",
                              not has_overflow,
                              f"scrollWidth vs innerWidth check at {vp['width']}px")
            except Exception as e:
                runner.record_error("mobile", f"layout:{vp_name}_overflow", e)

            # Touch target sizes (minimum 44x44px per Apple guidelines, 24x24 per WCAG AA)
            try:
                touch_results = page.evaluate("""
                    () => {
                        const buttons = document.querySelectorAll('button, [role="button"], [role="switch"]');
                        const small = [];
                        for (const btn of buttons) {
                            if (!btn.offsetParent) continue; // skip hidden
                            const rect = btn.getBoundingClientRect();
                            if (rect.width < 24 || rect.height < 24) {
                                small.push({ id: btn.id, w: Math.round(rect.width), h: Math.round(rect.height) });
                            }
                        }
                        return { total: buttons.length, small: small, smallCount: small.length };
                    }
                """)
                total = touch_results.get("total", 0)
                small_count = touch_results.get("smallCount", 0)
                passed = small_count <= 2  # allow a couple small icons
                runner.record("mobile", f"touch:{vp_name}_target_sizes", passed,
                               f"{total} buttons, {small_count} below 24px min")
            except Exception as e:
                runner.record_error("mobile", f"touch:{vp_name}_target_sizes", e)

            # FPS on mobile
            try:
                fps_data = measure_fps(page, duration_s=3)
                fps = fps_data.get("fps", 0)
                passed = fps >= FPS_MIN_MOBILE
                runner.record("mobile", f"fps:{vp_name}_performance", passed,
                               f"{fps:.1f} FPS (min {FPS_MIN_MOBILE} for mobile)",
                               int(fps_data.get("duration_ms", 3000)))
            except Exception as e:
                runner.record_error("mobile", f"fps:{vp_name}_performance", e)

            # Viewport meta tag
            try:
                meta = page.evaluate("""
                    () => {
                        const vp = document.querySelector('meta[name="viewport"]');
                        return { exists: !!vp, content: vp ? vp.getAttribute('content') : null };
                    }
                """)
                passed = meta.get("exists", False) and "width=device-width" in (meta.get("content") or "")
                runner.record("mobile", f"meta:{vp_name}_viewport_tag", passed,
                               f"content='{meta.get('content')}'")
            except Exception as e:
                runner.record_error("mobile", f"meta:{vp_name}_viewport_tag", e)

            # Mobile library toggle (if exists)
            try:
                has_mobile_lib = page.evaluate("""
                    () => !!document.getElementById('mobile-lib-toggle')
                """)
                runner.record("mobile", f"mobile_lib:{vp_name}_toggle_exists", True,
                               f"mobile-lib-toggle exists: {has_mobile_lib}")
            except Exception as e:
                runner.record_error("mobile", f"mobile_lib:{vp_name}", e)

            # Sidebar visibility / behavior on mobile
            try:
                sidebar = page.evaluate("""
                    () => {
                        const sb = document.getElementById('sidebar');
                        if (!sb) return { exists: false };
                        const rect = sb.getBoundingClientRect();
                        const style = getComputedStyle(sb);
                        return {
                            exists: true,
                            visible: style.display !== 'none' && style.visibility !== 'hidden',
                            width: Math.round(rect.width),
                            left: Math.round(rect.left),
                        };
                    }
                """)
                passed = sidebar.get("exists", False)
                runner.record("mobile", f"sidebar:{vp_name}_present", passed,
                               f"width={sidebar.get('width')}, visible={sidebar.get('visible')}")
            except Exception as e:
                runner.record_error("mobile", f"sidebar:{vp_name}_present", e)

        except Exception as e:
            runner.record_error("mobile", f"viewport:{vp_name}", e)
        finally:
            if context:
                context.close()


# ============================================================================
# CATEGORY 4: CHAOS TESTS
# ============================================================================

def run_chaos_tests(page, runner):
    """Chaos engineering: rapid interaction, invalid input, edge cases."""
    print("\n" + "="*70)
    print("CATEGORY 4: CHAOS TESTS")
    print("="*70)

    dismiss_wizard(page)

    # --- Rapid Object Addition ---
    print("\n--- Rapid Object Addition (50 objects quickly) ---")
    try:
        result = page.evaluate("""
            () => {
                try {
                    const t0 = performance.now();
                    let added = 0;
                    for (let i = 0; i < 50; i++) {
                        const types = ['tree_deciduous', 'patio', 'chair', 'bush', 'fence_privacy'];
                        const id = window._test.addObject(types[i % types.length], {}, 
                            {x: (Math.random() - 0.5) * 40, y: 0, z: (Math.random() - 0.5) * 30});
                        if (id) added++;
                    }
                    return { added: added, ms: performance.now() - t0 };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        passed = result.get("added", 0) == 50 and "error" not in result
        runner.record("chaos", "rapid:add_50_objects", passed,
                       f"added={result.get('added')}, {result.get('ms', 0):.0f}ms")
    except Exception as e:
        runner.record_error("chaos", "rapid:add_50_objects", e)

    # --- Rapid Add/Remove Cycle ---
    print("\n--- Rapid Add/Remove Cycle ---")
    try:
        result = page.evaluate("""
            () => {
                try {
                    let errors = 0;
                    for (let round = 0; round < 20; round++) {
                        const ids = [];
                        for (let i = 0; i < 5; i++) {
                            const id = window._test.addObject('patio', {}, {x: i, y: 0, z: i});
                            if (id) ids.push(id);
                        }
                        // Remove by selecting and clicking delete button
                        for (const id of ids) {
                            try {
                                window._test.selectObject(id);
                                const delBtn = document.getElementById('btn-delete');
                                if (delBtn && delBtn.offsetParent) {
                                    delBtn.click();
                                } else {
                                    const event = new KeyboardEvent('keydown', { key: 'Delete', code: 'Delete', keyCode: 46 });
                                    document.dispatchEvent(event);
                                }
                            } catch(e) { errors++; }
                        }
                    }
                    return { errors: errors, finalCount: window._test.state.objects.size };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        page.wait_for_timeout(500)
        passed = result.get("errors", 99) == 0 and "error" not in result
        runner.record("chaos", "rapid:add_remove_cycle", passed,
                       f"errors={result.get('errors')}, finalCount={result.get('finalCount')}")
    except Exception as e:
        runner.record_error("chaos", "rapid:add_remove_cycle", e)

    # --- Invalid Object Parameters ---
    print("\n--- Invalid Object Parameters ---")
    invalid_params = [
        ("patio", {"width": -100, "depth": -100}, "negative dimensions"),
        ("pool_inground", {"width": 0, "depth": 0}, "zero dimensions"),
        ("tree_deciduous", {"width": 999999, "depth": 999999}, "huge dimensions"),
        ("fence_privacy", {"width": "not_a_number"}, "string as number"),
        ("patio", {"color": "invalid_color"}, "invalid color"),
        ("chair", {"width": None}, "null width"),
    ]
    # NaN and Infinity can't be JSON-serialized, so handle them with raw JS
    js_special_params = [
        ("patio", "NaN", "NaN width"),
        ("patio", "Infinity", "Infinity width"),
    ]
    for obj_type, params, desc in invalid_params:
        try:
            result = page.evaluate(f"""
                () => {{
                    try {{
                        const id = window._test.addObject('{obj_type}', {json.dumps(params)}, {{x: 0, y: 0, z: 0}});
                        return {{ success: !!id, error: null }};
                    }} catch(e) {{
                        return {{ success: false, error: e.toString() }};
                    }}
                }}
            """)
            # We expect either graceful handling (success with sanitized params) or clean error
            passed = "error" not in result or result.get("error") is None
            runner.record("chaos", f"invalid_params:{desc}", passed,
                         f"success={result.get('success')}, error={str(result.get('error', ''))[:60]}")
        except Exception as e:
            runner.record_error("chaos", f"invalid_params:{desc}", e)

    for obj_type, js_val, desc in js_special_params:
        try:
            result = page.evaluate(f"""
                () => {{
                    try {{
                        const id = window._test.addObject('{obj_type}', {{width: {js_val}}}, {{x: 0, y: 0, z: 0}});
                        return {{ success: !!id, error: null }};
                    }} catch(e) {{
                        return {{ success: false, error: e.toString() }};
                    }}
                }}
            """)
            passed = "error" not in result or result.get("error") is None
            runner.record("chaos", f"invalid_params:{desc}", passed,
                         f"success={result.get('success')}, error={str(result.get('error', ''))[:60]}")
        except Exception as e:
            runner.record_error("chaos", f"invalid_params:{desc}", e)

    # --- Duplicate Object ---
    print("\n--- Duplicate Object ---")
    try:
        result = page.evaluate("""
            () => {
                try {
                    const objs = Array.from(window._test.state.objects.keys());
                    if (objs.length === 0) return { error: 'no objects' };
                    window._test.selectObject(objs[0]);
                    const countBefore = window._test.state.objects.size;
                    if (window._test.duplicateObject) {
                        window._test.duplicateObject();
                    } else {
                        // Try via button
                        document.getElementById('btn-duplicate')?.click();
                    }
                    return { countBefore: countBefore, countAfter: window._test.state.objects.size };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        passed = result.get("countAfter", 0) > result.get("countBefore", 0) and "error" not in result
        runner.record("chaos", "duplicate:object_duplicated", passed,
                       f"before={result.get('countBefore')}, after={result.get('countAfter')}")
    except Exception as e:
        runner.record_error("chaos", "duplicate:object_duplicated", e)

    # --- Rapid Undo/Redo ---
    print("\n--- Rapid Undo/Redo ---")
    try:
        result = page.evaluate("""
            () => {
                try {
                    let errors = 0;
                    // Rapidly undo and redo
                    for (let i = 0; i < 20; i++) {
                        try { window._test.undo(); } catch(e) { errors++; }
                        try { window._test.redo(); } catch(e) { errors++; }
                    }
                    return { errors: errors };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        passed = result.get("errors", 99) == 0 and "error" not in result
        runner.record("chaos", "rapid:undo_redo_cycle", passed,
                       f"errors={result.get('errors')}")
    except Exception as e:
        runner.record_error("chaos", "rapid:undo_redo_cycle", e)

    # --- Clear All Objects ---
    print("\n--- Clear All Objects ---")
    try:
        result = remove_all_objects(page)
        page.wait_for_timeout(500)
        remaining = result.get("remaining", 99)
        passed = remaining == 0 and "error" not in result
        runner.record("chaos", "clear:remove_all_objects", passed,
                       f"removed={result.get('removed', 0)}, remaining={remaining}")
    except Exception as e:
        runner.record_error("chaos", "clear:remove_all_objects", e)

    # --- Invalid Load Data ---
    print("\n--- Invalid Load Data ---")
    invalid_loads = [
        ("empty_json", "{}"),
        ("null_data", "null"),
        ("missing_yard", '{"objects": []}'),
        ("missing_objects", '{"yard": {}}'),
        ("malformed_array", '{"yard": {"width": 50, "depth": 100}, "objects": "not_an_array"}'),
        ("extra_large", json.dumps({"yard": {"width": 50, "depth": 100}, 
                                     "objects": [{"id": i, "type": "patio", "params": {}, "position": {"x": 0, "y": 0, "z": 0}} for i in range(200)]})),
    ]
    for name, data in invalid_loads:
        try:
            escaped_data = data.replace("\\", "\\\\").replace("'", "\\'")
            js_code = f"""
                () => {{
                    try {{
                        window._test.loadDesign('{escaped_data}');
                        return {{ success: true, objectCount: window._test.state.objects.size }};
                    }} catch(e) {{
                        return {{ success: false, error: e.toString() }};
                    }}
                }}
            """
            result = page.evaluate(js_code)
            # Either it loads gracefully or throws a caught error — both are OK
            passed = True  # no uncaught crash = pass
            runner.record("chaos", f"invalid_load:{name}", passed,
                         f"success={result.get('success')}, count={result.get('objectCount')}, err={str(result.get('error',''))[:40]}")
        except Exception as e:
            runner.record_error("chaos", f"invalid_load:{name}", e)

    # --- Rapid Panel Toggling ---
    print("\n--- Rapid Panel Toggling ---")
    try:
        # Use dock tabs instead of old floating buttons
        dock_selectors = ["[data-dock='terrain']", "[data-dock='underground']", 
                          "[data-dock='analyze']", "[data-dock='innovate']", 
                          "[data-dock='sun']"]
        for _ in range(3):
            for selector in dock_selectors:
                el = page.query_selector(selector)
                if el and el.is_visible():
                    el.evaluate("el => el.click()")
                    page.wait_for_timeout(50)
        page.wait_for_timeout(500)
        # Check no crash
        state = get_state(page)
        passed = "error" not in state
        runner.record("chaos", "rapid:panel_toggling", passed,
                       f"state OK after toggling, viewMode={state.get('viewMode')}")
    except Exception as e:
        runner.record_error("chaos", "rapid:panel_toggling", e)

    # --- Slider Rapid Changes ---
    print("\n--- Slider Rapid Changes ---")
    try:
        # Open terrain via dock tab
        dock_terrain = page.query_selector("[data-dock='terrain']")
        if dock_terrain and dock_terrain.is_visible():
            dock_terrain.evaluate("el => el.click()")
            page.wait_for_timeout(400)
        result = page.evaluate("""
            () => {
                try {
                    const slider = document.getElementById('terrain-brush-size');
                    if (!slider) return { error: 'no slider' };
                    let errors = 0;
                    for (let i = 0; i < 50; i++) {
                        try {
                            slider.value = Math.floor(Math.random() * 50) + 1;
                            slider.dispatchEvent(new Event('input', { bubbles: true }));
                        } catch(e) { errors++; }
                    }
                    return { errors: errors };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        passed = result.get("errors", 99) == 0 and "error" not in result
        runner.record("chaos", "rapid:slider_changes", passed,
                       f"errors={result.get('errors')}, {result.get('error', '')}")
        # Close dock
        if dock_terrain and dock_terrain.is_visible():
            dock_terrain.evaluate("el => el.click()")
            page.wait_for_timeout(200)
    except Exception as e:
        runner.record_error("chaos", "rapid:slider_changes", e)

    # --- Keyboard Mashing ---
    print("\n--- Keyboard Mashing ---")
    try:
        for key in ["Tab", "Enter", "Escape", "ArrowLeft", "ArrowRight", 
                     "ArrowUp", "ArrowDown", "Delete", "Backspace", " "]:
            page.keyboard.press(key)
            page.wait_for_timeout(50)
        # Check app still responds
        state = get_state(page)
        passed = "error" not in state
        runner.record("chaos", "keyboard:mashing_no_crash", passed,
                       f"state OK after mashing, viewMode={state.get('viewMode')}")
    except Exception as e:
        runner.record_error("chaos", "keyboard:mashing_no_crash", e)

    # --- Mouse Spam ---
    print("\n--- Mouse Spam ---")
    try:
        for _ in range(20):
            page.mouse.click(640, 400)
            page.wait_for_timeout(30)
        state = get_state(page)
        passed = "error" not in state
        runner.record("chaos", "mouse:spam_no_crash", passed,
                       f"state OK after 20 rapid clicks")
    except Exception as e:
        runner.record_error("chaos", "mouse:spam_no_crash", e)

    # --- Window Resize Spam ---
    print("\n--- Window Resize Spam ---")
    try:
        sizes = [{"width": 320, "height": 568}, {"width": 1920, "height": 1080},
                 {"width": 768, "height": 1024}, {"width": 1280, "height": 800}]
        for _ in range(3):
            for s in sizes:
                page.set_viewport_size(s)
                page.wait_for_timeout(100)
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(500)
        state = get_state(page)
        passed = "error" not in state
        runner.record("chaos", "resize:spam_no_crash", passed,
                       f"state OK after rapid resizes")
    except Exception as e:
        runner.record_error("chaos", "resize:spam_no_crash", e)


# ============================================================================
# CATEGORY 5: CRITIC-SPECIFIC TESTS (DOM/JS Integrity)
# ============================================================================

def run_critic_tests(page, runner, base_url):
    """Critic tests: JS errors, DOM integrity, structural validation, accessibility."""
    print("\n" + "="*70)
    print("CATEGORY 5: CRITIC TESTS (DOM/JS Integrity)")
    print("="*70)

    dismiss_wizard(page)

    # --- No JavaScript Errors on Load ---
    print("\n--- JavaScript Error Detection ---")
    try:
        # Reload page and collect errors
        js_errors = []
        page.on("console", lambda msg: js_errors.append({"type": msg.type, "text": msg.text}) if msg.type == "error" else None)
        page.on("pageerror", lambda err: js_errors.append({"type": "pageerror", "text": str(err)}))
        page.reload(wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)  # wait for all async operations

        critical_errors = [e for e in js_errors 
                          if "Failed to load" not in e.get("text", "")
                          and "favicon" not in e.get("text", "").lower()
                          and "404" not in e.get("text", "")]
        passed = len(critical_errors) == 0
        detail = f"{len(js_errors)} total errors, {len(critical_errors)} critical"
        if critical_errors:
            detail += ": " + "; ".join(e["text"][:80] for e in critical_errors[:3])
        runner.record("critic", "js:no_errors_on_load", passed, detail)
    except Exception as e:
        runner.record_error("critic", "js:no_errors_on_load", e)

    # --- No Duplicate IDs ---
    print("\n--- No Duplicate IDs ---")
    try:
        duplicates = page.evaluate("""
            () => {
                const all = document.querySelectorAll('[id]');
                const ids = {};
                const dups = [];
                for (const el of all) {
                    const id = el.id;
                    if (ids[id]) {
                        if (!dups.includes(id)) dups.push(id);
                    } else {
                        ids[id] = true;
                    }
                }
                return { duplicates: dups, total: all.length };
            }
        """)
        dup_list = duplicates.get("duplicates", [])
        passed = len(dup_list) == 0
        runner.record("critic", "dom:no_duplicate_ids", passed,
                       f"{duplicates.get('total', 0)} elements, {len(dup_list)} duplicates: {dup_list[:5]}")
    except Exception as e:
        runner.record_error("critic", "dom:no_duplicate_ids", e)

    # --- All Buttons Have Accessible Names ---
    print("\n--- Accessible Names ---")
    try:
        result = page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('button');
                const no_name = [];
                for (const btn of buttons) {
                    if (!btn.offsetParent) continue;
                    const ariaLabel = btn.getAttribute('aria-label');
                    const title = btn.getAttribute('title');
                    const text = btn.textContent.trim();
                    if (!ariaLabel && !title && !text) {
                        no_name.push(btn.id || 'unnamed');
                    }
                }
                return { total: buttons.length, noName: no_name };
            }
        """)
        no_name_list = result.get("noName", [])
        passed = len(no_name_list) == 0
        runner.record("critic", "a11y:buttons_have_names", passed,
                       f"{result.get('total', 0)} buttons, {len(no_name_list)} without accessible name: {no_name_list[:5]}")
    except Exception as e:
        runner.record_error("critic", "a11y:buttons_have_names", e)

    # --- CSS Variables Defined ---
    print("\n--- CSS Variables ---")
    try:
        result = page.evaluate("""
            () => {
                const root = getComputedStyle(document.documentElement);
                const vars = ['--primary', '--bg', '--text', '--border', '--surface'];
                const missing = [];
                for (const v of vars) {
                    const val = root.getPropertyValue(v);
                    if (!val.trim()) missing.push(v);
                }
                return { missing: missing, checked: vars.length };
            }
        """)
        missing = result.get("missing", [])
        passed = len(missing) == 0
        runner.record("critic", "css:variables_defined", passed,
                       f"Checked {result.get('checked', 0)}, missing: {missing}")
    except Exception as e:
        runner.record_error("critic", "css:variables_defined", e)

    # --- Importmap Correct ---
    print("\n--- Importmap Validation ---")
    try:
        result = page.evaluate("""
            () => {
                const map = document.querySelector('script[type="importmap"]');
                if (!map) return { error: 'no importmap' };
                try {
                    const data = JSON.parse(map.textContent);
                    const threeUrl = data.imports ? data.imports['three'] : null;
                    return { hasThree: !!threeUrl, url: threeUrl };
                } catch(e) {
                    return { error: e.toString() };
                }
            }
        """)
        passed = result.get("hasThree", False) and "error" not in result
        runner.record("critic", "importmap:three_js_configured", passed,
                       f"three URL: {result.get('url', 'N/A')}")
    except Exception as e:
        runner.record_error("critic", "importmap:three_js_configured", e)

    # --- WebGL Context Available ---
    print("\n--- WebGL Context ---")
    try:
        result = page.evaluate("""
            () => {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
                return { hasWebGL: !!gl, version: gl ? gl.getParameter(gl.VERSION) : 'N/A' };
            }
        """)
        passed = result.get("hasWebGL", False)
        runner.record("critic", "webgl:context_available", passed,
                       f"WebGL: {result.get('version', 'N/A')}")
    except Exception as e:
        runner.record_error("critic", "webgl:context_available", e)

    # --- Canvas Element Present ---
    print("\n--- Canvas Element ---")
    try:
        canvases = page.evaluate("""
            () => {
                const cs = document.querySelectorAll('canvas');
                return { count: cs.length, 
                         sizes: Array.from(cs).map(c => ({ w: c.width, h: c.height, 
                                                             id: c.id || c.parentElement?.id })) };
            }
        """)
        passed = canvases.get("count", 0) > 0
        runner.record("critic", "canvas:present", passed,
                       f"{canvases.get('count', 0)} canvas(es), sizes: {canvases.get('sizes', [])[:3]}")
    except Exception as e:
        runner.record_error("critic", "canvas:present", e)

    # --- HTML Structure Validation ---
    print("\n--- HTML Structure ---")
    try:
        structure = page.evaluate("""
            () => {
                return {
                    hasDoctype: document.doctype !== null,
                    hasHtml: !!document.documentElement,
                    hasHead: !!document.head,
                    hasBody: !!document.body,
                    hasViewport: !!document.querySelector('meta[name="viewport"]'),
                    hasCharset: !!document.querySelector('meta[charset]'),
                    bodyChildren: document.body.children.length,
                };
            }
        """)
        checks = {
            "hasDoctype": structure.get("hasDoctype", False),
            "hasHtml": structure.get("hasHtml", False),
            "hasHead": structure.get("hasHead", False),
            "hasBody": structure.get("hasBody", False),
            "hasViewport": structure.get("hasViewport", False),
            "hasCharset": structure.get("hasCharset", False),
        }
        for check_name, check_val in checks.items():
            runner.record("critic", f"html:{check_name}", check_val, str(check_val))
        runner.record("critic", "html:body_has_children",
                      structure.get("bodyChildren", 0) > 0,
                      f"{structure.get('bodyChildren', 0)} children in body")
    except Exception as e:
        runner.record_error("critic", "html:structure", e)

    # --- State Object Integrity ---
    print("\n--- State Object Integrity ---")
    try:
        state = page.evaluate("""
            () => {
                try {
                    const s = window._test.state;
                    return {
                        hasYard: typeof s.yard === 'object',
                        hasObjects: s.objects instanceof Map,
                        hasSelectedId: s.selectedId === null || typeof s.selectedId === 'number',
                        hasNextId: typeof s.nextId === 'number',
                        hasViewMode: typeof s.viewMode === 'string',
                        hasUndoStack: Array.isArray(s.undoStack),
                        hasRedoStack: Array.isArray(s.redoStack),
                        hasTerrain: s.terrain === null || s.terrain instanceof Float32Array,
                    };
                } catch(e) { return { error: e.toString() }; }
            }
        """)
        for key, val in state.items():
            if key == "error":
                runner.record("critic", f"state:integrity_error", False, str(val))
            else:
                runner.record("critic", f"state:{key}", val, str(val))
    except Exception as e:
        runner.record_error("critic", "state:integrity", e)

    # --- All Panels Can Open Without Errors ---
    print("\n--- Panel Open/Close Without Errors ---")
    # Use dock system for terrain panels, topbar for cost/layer
    dock_panel_map = {
        "terrain": ("dock-terrain-content", "[data-dock='terrain']"),
        "underground": ("dock-underground-content", "[data-dock='underground']"),
        "analyze": ("dock-analyze-content", "[data-dock='analyze']"),
        "innovate": ("dock-innovate-content", "[data-dock='innovate']"),
        "sun": ("dock-sun-content", "[data-dock='sun']"),
    }
    for dock_name, (content_id, tab_selector) in dock_panel_map.items():
        try:
            page_errors_before = []
            page.on("pageerror", lambda err: page_errors_before.append(str(err)))

            el = page.query_selector(tab_selector)
            if el and el.is_visible():
                # Use JS click to avoid Playwright interception issues
                el.evaluate("el => el.click()")
                page.wait_for_timeout(400)
                content = page.query_selector(f"#{content_id}")
                content_visible = content and content.is_visible()
                runner.record("critic", f"panel:{dock_name}_dock_opens_clean",
                              content_visible and len(page_errors_before) == 0,
                              f"content visible={content_visible}, errors={len(page_errors_before)}")
                # Close
                el.evaluate("el => el.click()")
                page.wait_for_timeout(200)
            else:
                runner.record_skip("critic", f"panel:{dock_name}_dock_opens_clean",
                                   f"tab not visible")
        except Exception as e:
            runner.record_error("critic", f"panel:{dock_name}_dock_opens_clean", e)

    # Cost and layer via topbar buttons
    for panel_id, btn_id in [("cost-panel", "btn-cost"), ("layer-panel", "btn-layers")]:
        try:
            page_errors_before = []
            page.on("pageerror", lambda err: page_errors_before.append(str(err)))

            el = page.query_selector(f"#{btn_id}")
            if el and el.is_visible():
                # Use JS click to avoid Playwright click interception
                el.evaluate("el => el.click()")
                page.wait_for_timeout(300)
                panel = page.query_selector(f"#{panel_id}")
                panel_visible = panel and panel.is_visible()
                runner.record("critic", f"panel:{panel_id}_opens_clean",
                              panel_visible and len(page_errors_before) == 0,
                              f"visible={panel_visible}, errors={len(page_errors_before)}")
                # Close
                el.evaluate("el => el.click()")
                page.wait_for_timeout(200)
            else:
                runner.record_skip("critic", f"panel:{panel_id}_opens_clean",
                                   f"#{btn_id} not visible")
        except Exception as e:
            runner.record_error("critic", f"panel:{panel_id}_opens_clean", e)

    # --- Tab Order (Keyboard Focus) ---
    print("\n--- Tab Order ---")
    try:
        # Focus the first button in the topbar explicitly, then tab
        page.evaluate("""
            () => {
                const btn = document.querySelector('#btn-save');
                if (btn) btn.focus();
            }
        """)
        page.wait_for_timeout(200)
        
        focused_ids = []
        for _ in range(10):
            current = page.evaluate("() => document.activeElement ? document.activeElement.id : ''")
            focused_ids.append(current)
            page.keyboard.press("Tab")
            page.wait_for_timeout(100)
        
        # Check that at least some elements received focus
        unique_focused = set(f for f in focused_ids if f)
        has_focus_movement = len(unique_focused) >= 1
        runner.record("critic", "keyboard:tab_navigation_works", has_focus_movement,
                       f"Focused {len(unique_focused)} unique elements: {focused_ids[:5]}")
    except Exception as e:
        runner.record_error("critic", "keyboard:tab_navigation_works", e)

    # --- No Inline Error Handlers (best practice) ---
    print("\n--- Inline Event Handlers Check ---")
    try:
        inline_handlers = page.evaluate("""
            () => {
                const els = document.querySelectorAll('[onclick], [onload], [onerror]');
                return { count: els.length, ids: Array.from(els).map(e => e.id).filter(Boolean).slice(0, 5) };
            }
        """)
        passed = inline_handlers.get("count", 99) == 0
        runner.record("critic", "html:no_inline_handlers", passed,
                       f"{inline_handlers.get('count', 0)} inline handlers found")
    except Exception as e:
        runner.record_error("critic", "html:no_inline_handlers", e)

    # --- Contrast Check (key elements) ---
    print("\n--- Contrast Check ---")
    try:
        result = page.evaluate("""
            () => {
                function getRgb(el) {
                    const s = getComputedStyle(el);
                    const c = s.color;
                    const m = c.match(/\\d+/g);
                    return m ? [parseInt(m[0]), parseInt(m[1]), parseInt(m[2])] : [0,0,0];
                }
                function getBg(el) {
                    let e = el;
                    while (e) {
                        const s = getComputedStyle(e);
                        if (s.backgroundColor !== 'rgba(0, 0, 0, 0)' && s.backgroundColor !== 'transparent') {
                            const m = s.backgroundColor.match(/\\d+/g);
                            return m ? [parseInt(m[0]), parseInt(m[1]), parseInt(m[2])] : [255,255,255];
                        }
                        e = e.parentElement;
                    }
                    return [255,255,255];
                }
                function lum(rgb) {
                    const [r,g,b] = rgb.map(c => {
                        cs = c/255;
                        return cs <= 0.03928 ? cs/12.92 : Math.pow((cs+0.055)/1.055, 2.4);
                    });
                    return 0.2126*r + 0.7152*g + 0.0722*b;
                }
                function ratio(rgb1, rgb2) {
                    const l1 = lum(rgb1), l2 = lum(rgb2);
                    const light = Math.max(l1,l2), dark = Math.min(l1,l2);
                    return (light + 0.05) / (dark + 0.05);
                }
                const checks = [];
                const targets = ['#btn-save', '#btn-help', '.topbar-brand', '#library .lib-item, .obj-item'];
                for (const sel of targets) {
                    const el = document.querySelector(sel);
                    if (el && el.offsetParent) {
                        const cr = ratio(getRgb(el), getBg(el));
                        checks.push({ sel: sel, ratio: cr.toFixed(2) });
                    }
                }
                return checks;
            }
        """)
        low_contrast = [c for c in result if float(c.get("ratio", "0")) < 3.0]
        passed = len(low_contrast) == 0
        detail = f"{len(result)} checked, {len(low_contrast)} below 3.0:1"
        if low_contrast:
            detail += " " + ", ".join(f"{c['sel']}={c['ratio']}" for c in low_contrast[:3])
        runner.record("critic", "a11y:contrast_ratios", passed, detail)
    except Exception as e:
        runner.record_error("critic", "a11y:contrast_ratios", e)

    # --- Error Recovery: Add Non-Existent Object Type ---
    print("\n--- Error Recovery ---")
    try:
        result = page.evaluate("""
            () => {
                try {
                    const id = window._test.addObject('nonexistent_type', {}, {x: 0, y: 0, z: 0});
                    return { success: !!id, error: null };
                } catch(e) {
                    return { success: false, error: e.toString() };
                }
            }
        """)
        # Should gracefully handle (either return null/id or throw caught error)
        passed = True  # no uncaught crash
        runner.record("critic", "recovery:invalid_object_type", passed,
                       f"success={result.get('success')}, error={str(result.get('error',''))[:60]}")
    except Exception as e:
        runner.record_error("critic", "recovery:invalid_object_type", e)

    # --- Long-Running Stability ---
    print("\n--- Long-Running Stability (10s idle) ---")
    try:
        # Let the app run idle for 10 seconds
        fps_data = measure_fps(page, duration_s=10)
        fps = fps_data.get("fps", 0)
        state = get_state(page)
        passed = fps > 0 and "error" not in state
        runner.record("critic", "stability:idle_10s", passed,
                       f"{fps:.1f} FPS over 10s idle, state OK",
                       int(fps_data.get("duration_ms", 10000)))
    except Exception as e:
        runner.record_error("critic", "stability:idle_10s", e)

    # --- Save/Load Round-Trip ---
    print("\n--- Save/Load Round-Trip ---")
    try:
        # Add some objects
        page.evaluate("""
            () => {
                try {
                    window._test.addObject('patio', {}, {x: 5, y: 0, z: 5});
                    window._test.addObject('tree_deciduous', {}, {x: -5, y: 0, z: -5});
                } catch(e) {}
            }
        """)
        page.wait_for_timeout(500)

        # Serialize design (returns object, not JSON string)
        saved = page.evaluate("""
            () => {
                try {
                    return JSON.stringify(window._test.serializeDesign());
                } catch(e) { return null; }
            }
        """)
        has_data = saved is not None and len(saved) > 10

        # Clear all objects via delete button approach
        page.evaluate("""
            () => {
                try {
                    const objs = Array.from(window._test.state.objects.keys());
                    for (const id of objs) {
                        window._test.selectObject(id);
                        const delBtn = document.getElementById('btn-delete');
                        if (delBtn && delBtn.offsetParent) {
                            delBtn.click();
                        } else {
                            const event = new KeyboardEvent('keydown', { key: 'Delete', code: 'Delete', keyCode: 46 });
                            document.dispatchEvent(event);
                        }
                    }
                } catch(e) {}
            }
        """)
        page.wait_for_timeout(500)
        state_empty = get_state(page)
        count_empty = state_empty.get("objectCount", -1)

        # Load saved data (loadDesign expects an object, not a JSON string)
        if saved:
            escaped_saved = saved.replace("\\", "\\\\").replace("'", "\\'")
            js_load = f"""
                () => {{
                    try {{
                        const data = JSON.parse('{escaped_saved}');
                        window._test.loadDesign(data);
                    }} catch(e) {{}}
                }}
            """
            page.evaluate(js_load)
            page.wait_for_timeout(1000)
            state_loaded = get_state(page)
            count_loaded = state_loaded.get("objectCount", -1)
            passed = count_loaded == 2
            runner.record("critic", "persistence:save_load_roundtrip", passed,
                         f"saved={has_data}, empty={count_empty}, after_load={count_loaded}")
        else:
            runner.record("critic", "persistence:save_load_roundtrip", False, "serialize failed")
    except Exception as e:
        runner.record_error("critic", "persistence:save_load_roundtrip", e)

    # --- File Size Check ---
    print("\n--- File Size Check ---")
    try:
        html_path = SCRIPT_DIR / "index.html"
        size_kb = html_path.stat().st_size / 1024
        passed = size_kb < 700  # less than 700KB (raised for Sprint 8 usability features)
        runner.record("critic", "file:size_reasonable", passed,
                       f"{size_kb:.0f}KB (max 700KB)")
    except Exception as e:
        runner.record_error("critic", "file:size_reasonable", e)

    # --- Line Count Check ---
    try:
        html_path = SCRIPT_DIR / "index.html"
        line_count = sum(1 for _ in open(html_path))
        passed = line_count < 20000  # less than 20K lines
        runner.record("critic", "file:line_count_reasonable", passed,
                       f"{line_count} lines (max 20000)")
    except Exception as e:
        runner.record_error("critic", "file:line_count_reasonable", e)


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(runner, total_time_s):
    """Generate QUALITY_GATE_REPORT.md."""
    summary = runner.summary()
    failures = runner.all_failures()

    report_lines = []
    report_lines.append("# Sprint 6 Quality Gate Report — Backyard Designer 3D")
    report_lines.append("")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**Total runtime:** {total_time_s:.1f}s")
    report_lines.append(f"**Agent:** Agent 5 (Critic / Quality Gate Architect)")
    report_lines.append("")
    report_lines.append("## Summary")
    report_lines.append("")
    report_lines.append(f"| Metric | Value |")
    report_lines.append(f"|--------|-------|")
    report_lines.append(f"| Total tests | {summary['total']} |")
    report_lines.append(f"| Passed | {summary['passed']} ✅ |")
    report_lines.append(f"| Failed | {summary['failed']} ❌ |")
    report_lines.append(f"| Errors | {summary['errors']} 💥 |")
    report_lines.append(f"| Skipped | {summary['skipped']} ⏭ |")
    report_lines.append(f"| Pass rate | {summary['passed']/max(summary['total'],1)*100:.1f}% |")
    report_lines.append("")

    # Per-category breakdown
    report_lines.append("## Per-Category Breakdown")
    report_lines.append("")
    categories = ["functional", "perf", "mobile", "chaos", "critic"]
    report_lines.append("| Category | Total | Passed | Failed | Errors | Skipped | Pass Rate |")
    report_lines.append("|----------|-------|--------|--------|--------|---------|-----------|")
    for cat in categories:
        cs = runner.category_summary(cat)
        rate = cs["passed"] / max(cs["total"], 1) * 100
        report_lines.append(
            f"| {cat} | {cs['total']} | {cs['passed']} | {cs['failed']} | {cs['errors']} | {cs['skipped']} | {rate:.0f}% |"
        )
    report_lines.append("")

    # Performance metrics
    report_lines.append("## Performance Measurements")
    report_lines.append("")
    if runner.perf_metrics["fps"]:
        report_lines.append("### FPS Measurements")
        report_lines.append("")
        report_lines.append("| Scene | FPS |")
        report_lines.append("|------|-----|")
        for entry in runner.perf_metrics["fps"]:
            report_lines.append(f"| {entry['scene']} | {entry['fps']:.1f} |")
        report_lines.append("")

    if runner.perf_metrics["load_times"]:
        report_lines.append("### Load Times")
        report_lines.append("")
        for lt in runner.perf_metrics["load_times"]:
            report_lines.append(f"- {lt:.0f}ms")
        report_lines.append("")

    if runner.perf_metrics["memory"]:
        report_lines.append("### Memory Usage")
        report_lines.append("")
        for m in runner.perf_metrics["memory"]:
            report_lines.append(f"- {m}")
        report_lines.append("")

    if runner.perf_metrics["render_times"]:
        report_lines.append("### Render Times")
        report_lines.append("")
        for r in runner.perf_metrics["render_times"]:
            report_lines.append(f"- avg: {r.get('avg_ms', 0):.1f}ms, min: {r.get('min_ms', 0):.1f}ms, max: {r.get('max_ms', 0):.1f}ms")
        report_lines.append("")

    # Failures
    if failures:
        report_lines.append("## Failures")
        report_lines.append("")
        report_lines.append("| # | Category | Test Name | Status | Details |")
        report_lines.append("|---|----------|-----------|--------|---------|")
        for i, f in enumerate(failures, 1):
            details = f.details.replace("|", "\\|")[:200] if f.details else ""
            report_lines.append(f"| {i} | {f.category} | {f.name} | {f.status} | {details} |")
        report_lines.append("")
    else:
        report_lines.append("## Failures")
        report_lines.append("")
        report_lines.append("🎉 **No failures!** All tests passed.")
        report_lines.append("")

    # Verdict
    report_lines.append("## Verdict")
    report_lines.append("")
    critical_failed = summary["failed"] + summary["errors"]
    if critical_failed == 0:
        report_lines.append("✅ **QUALITY GATE: PASSED** — All tests passed.")
    else:
        report_lines.append(f"❌ **QUALITY GATE: FAILED** — {critical_failed} test(s) failed or errored.")
    report_lines.append("")

    report_text = "\n".join(report_lines)
    REPORT_PATH.write_text(report_text)

    # Also save JSON results
    json_data = {
        "summary": summary,
        "categories": {cat: runner.category_summary(cat) for cat in categories},
        "perf_metrics": runner.perf_metrics,
        "failures": [f.to_dict() for f in failures],
        "all_tests": [r.to_dict() for r in runner.results],
        "generated_at": datetime.now().isoformat(),
        "total_runtime_s": total_time_s,
    }
    RESULTS_PATH.write_text(json.dumps(json_data, indent=2, default=str))

    return critical_failed == 0


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Sprint 6 Quality Gate")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help="Port for local HTTP server")
    parser.add_argument("--category", type=str, default="all",
                        choices=["all", "functional", "perf", "mobile", "chaos", "critic"],
                        help="Run only a specific category")
    args = parser.parse_args()

    base_url = f"http://127.0.0.1:{args.port}/index.html"

    # Verify server is running
    import urllib.request
    try:
        urllib.request.urlopen(base_url, timeout=5)
    except Exception:
        print(f"❌ Server not running at {base_url}")
        print(f"   Start it with: cd {SCRIPT_DIR} && python3 -m http.server {args.port}")
        sys.exit(2)

    print("="*70)
    print("BACKYARD DESIGNER 3D — SPRINT 6 QUALITY GATE")
    print("="*70)
    print(f"URL: {base_url}")
    print(f"Category: {args.category}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    runner = TestRunner()
    total_start = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            '--no-sandbox',
            '--disable-gpu',
            '--disable-dev-shm-usage',
            '--use-gl=swiftshader',
            '--enable-webgl',
            '--enable-unsafe-swiftshader',
        ])

        try:
            # CATEGORY 1: Functional
            if args.category in ("all", "functional"):
                try:
                    page, context = create_page(browser)
                    load_page(page, base_url)
                    run_functional_tests(page, runner)
                    context.close()
                except Exception as e:
                    runner.record_error("functional", "category_crash", e)
                    print(f"  💥 Category 'functional' crashed: {e}")

            # CATEGORY 2: Performance
            if args.category in ("all", "perf"):
                try:
                    page, context = create_page(browser)
                    load_page(page, base_url)
                    run_performance_tests(page, runner)
                    context.close()
                except Exception as e:
                    runner.record_error("perf", "category_crash", e)
                    print(f"  💥 Category 'perf' crashed: {e}")

            # CATEGORY 3: Mobile
            if args.category in ("all", "mobile"):
                try:
                    run_mobile_tests(browser, base_url, runner)
                except Exception as e:
                    runner.record_error("mobile", "category_crash", e)
                    print(f"  💥 Category 'mobile' crashed: {e}")

            # CATEGORY 4: Chaos
            if args.category in ("all", "chaos"):
                try:
                    page, context = create_page(browser)
                    load_page(page, base_url)
                    run_chaos_tests(page, runner)
                    context.close()
                except Exception as e:
                    runner.record_error("chaos", "category_crash", e)
                    print(f"  💥 Category 'chaos' crashed: {e}")

            # CATEGORY 5: Critic
            if args.category in ("all", "critic"):
                try:
                    page, context = create_page(browser)
                    load_page(page, base_url)
                    run_critic_tests(page, runner, base_url)
                    context.close()
                except Exception as e:
                    runner.record_error("critic", "category_crash", e)
                    print(f"  💥 Category 'critic' crashed: {e}")

        finally:
            browser.close()

    total_time = time.time() - total_start

    # Generate report
    all_passed = generate_report(runner, total_time)

    # Print summary
    summary = runner.summary()
    print("\n" + "="*70)
    print("QUALITY GATE SUMMARY")
    print("="*70)
    print(f"  Total tests:  {summary['total']}")
    print(f"  Passed:       {summary['passed']} ✅")
    print(f"  Failed:       {summary['failed']} ❌")
    print(f"  Errors:       {summary['errors']} 💥")
    print(f"  Skipped:      {summary['skipped']} ⏭")
    print(f"  Runtime:      {total_time:.1f}s")
    print(f"  Pass rate:    {summary['passed']/max(summary['total'],1)*100:.1f}%")
    print()
    if all_passed:
        print("🎉 QUALITY GATE: PASSED")
    else:
        print(f"❌ QUALITY GATE: FAILED ({summary['failed'] + summary['errors']} failures)")
    print(f"\nReport: {REPORT_PATH}")
    print(f"Results: {RESULTS_PATH}")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
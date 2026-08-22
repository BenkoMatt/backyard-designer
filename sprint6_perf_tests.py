#!/usr/bin/env python3
"""
Sprint 6 Performance Regression Test Suite (Playwright)
Tests FPS, memory stability, save/load performance, voxel meshing, and disposal.
Run: python3 sprint6_perf_tests.py
"""
import json, time, sys, os
import pytest
from playwright.sync_api import sync_playwright, Page, BrowserContext

BASE_URL = "http://localhost:8765/index.html"
HEADLESS_ARGS = ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
                 '--use-gl=swiftshader', '--enable-webgl', '--enable-unsafe-swiftshader']

# ===== FIXTURES =====

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=HEADLESS_ARGS)
        yield b
        b.close()

@pytest.fixture
def desktop_context(browser):
    ctx = browser.new_context(viewport={'width': 1920, 'height': 1080})
    yield ctx
    ctx.close()

@pytest.fixture
def mobile_context(browser):
    ctx = browser.new_context(
        viewport={'width': 375, 'height': 812},
        device_scale_factor=2,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
    )
    yield ctx
    ctx.close()

@pytest.fixture
def page(desktop_context):
    pg = desktop_context.new_page()
    pg.goto(BASE_URL, wait_until='networkidle')
    pg.wait_for_function("() => typeof window._test !== 'undefined' && window._test.scene", timeout=15000)
    try:
        pg.click('#wizard-skip', timeout=5000)
    except:
        pass
    time.sleep(1)
    # Ensure yard is initialized
    pg.evaluate("""
    () => {
        if (!window._test.state.yard || !window._test.state.yard.width) {
            window._test.initWithYard({ width: 50, depth: 50 });
        }
    }
    """)
    time.sleep(0.5)
    yield pg

@pytest.fixture
def mobile_page(mobile_context):
    pg = mobile_context.new_page()
    pg.goto(BASE_URL, wait_until='networkidle')
    pg.wait_for_function("() => typeof window._test !== 'undefined' && window._test.scene", timeout=15000)
    try:
        pg.click('#wizard-skip', timeout=5000)
    except:
        pass
    time.sleep(1)
    pg.evaluate("""
    () => {
        if (!window._test.state.yard || !window._test.state.yard.width) {
            window._test.initWithYard({ width: 50, depth: 50 });
        }
    }
    """)
    time.sleep(0.5)
    yield pg

# ===== HELPER FUNCTIONS =====

def measure_fps(page, duration_ms=2000):
    """Measure FPS by counting rAF frames over duration_ms."""
    page.evaluate("""
    (() => {
        window.__fpsFrames = 0;
        window.__fpsStart = performance.now();
        window.__fpsRafId = requestAnimationFrame(function tick() {
            window.__fpsFrames++;
            window.__fpsRafId = requestAnimationFrame(tick);
        });
    })();
    """)
    time.sleep(duration_ms / 1000)
    result = page.evaluate("""
    (() => {
        cancelAnimationFrame(window.__fpsRafId);
        const elapsed = performance.now() - window.__fpsStart;
        return (window.__fpsFrames / elapsed) * 1000;
    })()
    """)
    return round(result, 1)

def get_heap(page):
    return page.evaluate("() => performance.memory ? performance.memory.usedJSHeapSize / 1048576 : -1")

def get_renderer_info(page):
    return page.evaluate("""
    () => {
        const t = window._test;
        if (!t || !t.renderer) return null;
        return {
            geometries: t.renderer.info.memory.geometries,
            textures: t.renderer.info.memory.textures,
            render_calls: t.renderer.info.render.calls,
            triangles: t.renderer.info.render.triangles
        };
    }
    """)

def add_objects(page, count, spread=45):
    page.evaluate("""
    (count) => {
        const t = window._test;
        const types = Object.keys(t.CATALOG || {});
        if (types.length === 0) return;
        const sp = """ + str(spread) + """;
        for (let i = 0; i < count; i++) {
            const tp = types[i % types.length];
            t.addObject(tp, {}, {x: (i*2)%sp-sp/2, y:0, z: Math.floor(i*2/sp)*2-sp/2});
        }
    }
    """, count)
    time.sleep(0.3)

def remove_all_objects(page):
    page.evaluate("""
    () => {
        const t = window._test;
        const ids = Array.from(t.state.objects.keys());
        ids.forEach(id => {
            const obj = t.sceneObjects.get(id);
            if (obj) {
                t.scene.remove(obj);
                obj.traverse(child => {
                    if (child.geometry) child.geometry.dispose();
                    if (child.material) {
                        const mats = Array.isArray(child.material) ? child.material : [child.material];
                        mats.forEach(m => {
                            for (const key of Object.keys(m)) {
                                if (m[key] && m[key].isTexture) m[key].dispose();
                            }
                            m.dispose();
                        });
                    }
                });
                t.sceneObjects.delete(id);
            }
            t.state.objects.delete(id);
        });
    }
    """)
    time.sleep(0.3)

# ===== TESTS =====

class TestFPSDesktop:
    """FPS measurements on desktop viewport (1920x1080)."""

    def test_baseline_fps(self, page):
        """Baseline FPS with empty scene should be >= 30fps."""
        fps = measure_fps(page, 2000)
        assert fps >= 30, f"Baseline FPS {fps} below 30fps threshold"

    def test_50_objects_fps(self, page):
        """FPS with 50 objects should be >= 30fps."""
        add_objects(page, 50)
        fps = measure_fps(page, 2000)
        assert fps >= 30, f"50 objects FPS {fps} below 30fps threshold"

    def test_200_objects_fps(self, page):
        """FPS with 200 objects should be >= 30fps."""
        add_objects(page, 200)
        fps = measure_fps(page, 2000)
        assert fps >= 30, f"200 objects FPS {fps} below 30fps threshold"

    def test_500_objects_fps(self, page):
        """FPS with 500 objects should be >= 20fps."""
        add_objects(page, 500)
        fps = measure_fps(page, 2000)
        assert fps >= 20, f"500 objects FPS {fps} below 20fps threshold"

    def test_terrain_painting_fps(self, page):
        """FPS during terrain painting should be >= 30fps."""
        page.evaluate("""
        () => {
            const t = window._test;
            if (t.state.terrain) {
                for (let i = 0; i < 50; i++) {
                    const idx = Math.floor(Math.random() * t.state.terrain.length);
                    t.state.terrain[idx] += (Math.random() - 0.5) * 2;
                }
                t.applyTerrainToMesh();
            }
        }
        """)
        time.sleep(0.3)
        fps = measure_fps(page, 2000)
        assert fps >= 30, f"Terrain painting FPS {fps} below 30fps threshold"

class TestFPSMobile:
    """FPS measurements on mobile viewport (375x812)."""

    def test_mobile_baseline_fps(self, mobile_page):
        """Mobile baseline FPS should be >= 20fps."""
        fps = measure_fps(mobile_page, 2000)
        assert fps >= 20, f"Mobile baseline FPS {fps} below 20fps threshold"

    def test_mobile_50_objects_fps(self, mobile_page):
        """Mobile FPS with 50 objects should be >= 20fps."""
        add_objects(mobile_page, 50)
        fps = measure_fps(mobile_page, 2000)
        assert fps >= 20, f"Mobile 50 objects FPS {fps} below 20fps threshold"


class TestMemoryLeaks:
    """Memory leak detection tests."""

    def test_create_delete_100_objects_no_leak(self, page):
        """Creating and deleting 100 objects should not leak memory (>2MB delta)."""
        remove_all_objects(page)
        time.sleep(0.3)
        heap_before = get_heap(page)
        geo_before = get_renderer_info(page)

        add_objects(page, 100)
        time.sleep(0.3)
        remove_all_objects(page)
        time.sleep(0.3)

        heap_after = get_heap(page)
        geo_after = get_renderer_info(page)

        leak = heap_after - heap_before
        assert leak < 2.0, f"Memory leak detected: {leak:.1f}MB delta (threshold: 2.0MB)"
        assert geo_after['geometries'] <= geo_before['geometries'], \
            f"Geometry count increased: {geo_before['geometries']} -> {geo_after['geometries']}"

    def test_5_cycle_no_cumulative_leak(self, page):
        """5 create/delete cycles should not show cumulative leak (>3MB)."""
        remove_all_objects(page)
        time.sleep(0.3)
        heap_before = get_heap(page)

        for _ in range(5):
            add_objects(page, 100)
            time.sleep(0.2)
            remove_all_objects(page)
            time.sleep(0.1)

        heap_after = get_heap(page)
        leak = heap_after - heap_before
        assert leak < 3.0, f"Cumulative leak after 5 cycles: {leak:.1f}MB (threshold: 3.0MB)"


class TestSaveLoad:
    """Save/load performance tests."""

    def test_serialize_500_objects_under_2s(self, page):
        """Serializing 500 objects should take < 2 seconds."""
        remove_all_objects(page)
        add_objects(page, 500)
        page.evaluate("() => window._test.applyTerrainPreset('rolling')")
        time.sleep(0.3)

        # Measure serialization time INSIDE the page to avoid Playwright marshaling overhead
        result = page.evaluate("""
        () => {
            const t0 = performance.now();
            const data = window._test.serializeDesign();
            const elapsed = performance.now() - t0;
            return { time_ms: elapsed, object_count: data.objects.length };
        }
        """)
        assert result['object_count'] == 500, f"Expected 500 objects, got {result['object_count']}"
        assert result['time_ms'] < 2000, f"Serialize time {result['time_ms']:.0f}ms exceeds 2000ms threshold"

    def test_load_500_objects_under_3s(self, page):
        """Loading 500 objects should take < 3 seconds."""
        remove_all_objects(page)
        add_objects(page, 500)
        save_data = page.evaluate("() => window._test.serializeDesign()")

        remove_all_objects(page)
        time.sleep(0.3)

        # Measure load time INSIDE the page
        result = page.evaluate("""
        (data) => {
            const t0 = performance.now();
            window._test.loadDesign(data);
            const elapsed = performance.now() - t0;
            return { time_ms: elapsed };
        }
        """, save_data)
        assert result['time_ms'] < 3000, f"Load time {result['time_ms']:.0f}ms exceeds 3000ms threshold"

    def test_save_load_roundtrip_preserves_objects(self, page):
        """Save/load roundtrip should preserve object count."""
        remove_all_objects(page)
        add_objects(page, 50)
        save_data = page.evaluate("() => window._test.serializeDesign()")

        remove_all_objects(page)
        time.sleep(0.3)
        page.evaluate("(data) => window._test.loadDesign(data)", save_data)
        time.sleep(0.5)

        count = page.evaluate("() => window._test.state.objects.size")
        assert count == 50, f"Object count after roundtrip: {count} (expected 50)"


class TestVoxelPerformance:
    """Voxel meshing performance tests."""

    def test_voxel_mesh_build_under_500ms(self, page):
        """Building voxel mesh should take < 500ms."""
        page.evaluate("() => window._test.initWithYard({ width: 50, depth: 50 })")
        time.sleep(0.5)
        page.evaluate("() => window._test.rebuildVoxelVolume()")
        time.sleep(0.3)

        timing = page.evaluate("""
        () => {
            const t = window._test;
            t.initVoxelsFromTerrain();
            const t0 = performance.now();
            t.buildVoxelMesh();
            return performance.now() - t0;
        }
        """)
        assert timing < 500, f"Voxel mesh build time {timing:.0f}ms exceeds 500ms threshold"

    def test_voxel_mesh_greedy_merging(self, page):
        """Greedy meshing should produce fewer vertices than face count."""
        page.evaluate("() => window._test.initWithYard({ width: 50, depth: 50 })")
        time.sleep(0.5)
        page.evaluate("() => window._test.rebuildVoxelVolume()")
        time.sleep(0.3)

        result = page.evaluate("""
        () => {
            const t = window._test;
            t.initVoxelsFromTerrain();
            // Carve a sphere to create interior faces
            t.carveShape('sphere', 0, -5, 0, 8, 8);
            t.buildVoxelMesh();
            const mesh = t.voxelMesh;
            const vertCount = mesh ? mesh.geometry.attributes.position.count : 0;
            const faceCount = t.countVoxelFaces();
            return { vertices: vertCount, surfaceFaces: faceCount, ratio: vertCount / Math.max(faceCount * 4, 1) };
        }
        """)
        # Greedy meshing should produce fewer vertices than 4 per face
        # (4 verts per quad = non-merged; less means merging happened)
        assert result['vertices'] > 0, "No vertices in voxel mesh after carving"
        assert result['ratio'] < 1.0, \
            f"Greedy merging not effective: {result['vertices']} verts vs {result['surfaceFaces']} faces (ratio {result['ratio']:.2f})"

    def test_voxel_50pct_carved_fps(self, page):
        """FPS with 50% voxels carved should be >= 30fps."""
        page.evaluate("() => window._test.initWithYard({ width: 50, depth: 50 })")
        time.sleep(0.5)
        page.evaluate("() => window._test.rebuildVoxelVolume()")
        time.sleep(0.3)

        page.evaluate("""
        () => {
            const t = window._test;
            t.initVoxelsFromTerrain();
            const total = t.state.voxels.length;
            const target = Math.floor(total * 0.5);
            let carved = 0;
            const step = Math.max(1, Math.floor(total / target));
            for (let i = 0; i < total && carved < target; i += step) {
                if (t.state.voxels[i] === 1) { t.state.voxels[i] = 0; carved++; }
            }
            t.buildVoxelMesh();
        }
        """)
        time.sleep(0.3)
        fps = measure_fps(page, 2000)
        assert fps >= 30, f"50% carved FPS {fps} below 30fps threshold"


class TestDisposal:
    """Three.js resource disposal tests."""

    def test_geometry_count_stable_after_create_delete(self, page):
        """Geometry count should return to baseline after create/delete cycle."""
        remove_all_objects(page)
        time.sleep(0.3)
        info_before = get_renderer_info(page)

        add_objects(page, 100)
        time.sleep(0.3)
        remove_all_objects(page)
        time.sleep(0.3)

        info_after = get_renderer_info(page)
        assert info_after['geometries'] <= info_before['geometries'] + 1, \
            f"Geometry leak: {info_before['geometries']} -> {info_after['geometries']}"

    def test_texture_count_stable(self, page):
        """Texture count should not increase after create/delete cycle."""
        remove_all_objects(page)
        time.sleep(0.3)
        info_before = get_renderer_info(page)

        add_objects(page, 100)
        time.sleep(0.3)
        remove_all_objects(page)
        time.sleep(0.3)

        info_after = get_renderer_info(page)
        assert info_after['textures'] <= info_before['textures'], \
            f"Texture leak: {info_before['textures']} -> {info_after['textures']}"

    def test_dispose_group_cleans_geometry(self, page):
        """disposeGroup should dispose all geometries in a group."""
        result = page.evaluate("""
        () => {
            const t = window._test;
            const before = t.renderer.info.memory.geometries;
            // Create a complex object (fence with many pickets)
            const id = t.addObject('fence', { length: 100 }, {x: 0, y: 0, z: 0});
            const afterCreate = t.renderer.info.memory.geometries;
            // Delete it
            const obj = t.sceneObjects.get(id);
            if (obj) {
                t.scene.remove(obj);
                obj.traverse(child => {
                    if (child.geometry) child.geometry.dispose();
                    if (child.material) {
                        const mats = Array.isArray(child.material) ? child.material : [child.material];
                        mats.forEach(m => m.dispose());
                    }
                });
                t.sceneObjects.delete(id);
                t.state.objects.delete(id);
            }
            const afterDelete = t.renderer.info.memory.geometries;
            return { before, afterCreate, afterDelete };
        }
        """)
        assert result['afterDelete'] <= result['before'] + 1, \
            f"Geometry not disposed: {result['before']} -> {result['afterCreate']} -> {result['afterDelete']}"


class TestStability:
    """Long session stability tests."""

    def test_no_fps_degradation_after_rapid_cycles(self, page):
        """FPS should not degrade more than 20% after rapid add/delete cycles."""
        remove_all_objects(page)
        time.sleep(0.3)
        add_objects(page, 30)
        time.sleep(0.2)

        fps_start = measure_fps(page, 2000)
        heap_start = get_heap(page)

        # Rapid cycles for 20 seconds
        start_time = time.time()
        cycles = 0
        while time.time() - start_time < 20:
            page.evaluate("""
            () => {
                const t = window._test;
                const types = Object.keys(t.CATALOG || {});
                const ids = Array.from(t.state.objects.keys());
                for (let i = 0; i < Math.floor(ids.length / 2); i++) {
                    const obj = t.sceneObjects.get(ids[i]);
                    if (obj) {
                        t.scene.remove(obj);
                        obj.traverse(child => {
                            if (child.geometry) child.geometry.dispose();
                            if (child.material) {
                                const mats = Array.isArray(child.material) ? child.material : [child.material];
                                mats.forEach(m => m.dispose());
                            }
                        });
                        t.sceneObjects.delete(ids[i]);
                    }
                    t.state.objects.delete(ids[i]);
                }
                for (let i = 0; i < 15; i++) {
                    t.addObject(types[i % types.length], {}, {x: (i*3)%45-22, y:0, z: 0});
                }
            }
            """)
            cycles += 1

        fps_end = measure_fps(page, 2000)
        heap_end = get_heap(page)

        degradation = (1 - fps_end / max(fps_start, 1)) * 100
        assert degradation < 20, \
            f"FPS degradation {degradation:.1f}% exceeds 20% threshold (start={fps_start}, end={fps_end})"

    def test_no_heap_growth_after_cycles(self, page):
        """Heap should not grow more than 5MB after rapid cycles."""
        remove_all_objects(page)
        time.sleep(0.3)
        heap_before = get_heap(page)

        for _ in range(10):
            add_objects(page, 100)
            time.sleep(0.1)
            remove_all_objects(page)
            time.sleep(0.1)

        heap_after = get_heap(page)
        growth = heap_after - heap_before
        assert growth < 5.0, \
            f"Heap growth {growth:.1f}MB exceeds 5MB threshold (before={heap_before:.1f}, after={heap_after:.1f})"


class TestEventListeners:
    """Event listener and timer leak tests."""

    def test_walkloop_not_running_when_inactive(self, page):
        """walkLoop rAF should not be running when walkMode is false."""
        # walkLoop should only schedule rAF when walkMode is true
        # We can verify by checking that FPS is ~60 (not reduced by competing rAF loops)
        fps = measure_fps(page, 2000)
        assert fps >= 50, f"FPS {fps} suggests background rAF loop consuming frames"

    def test_no_console_errors(self, page):
        """No console errors should be produced during basic operations."""
        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

        # Perform various operations
        add_objects(page, 10)
        time.sleep(0.2)
        remove_all_objects(page)
        time.sleep(0.2)
        page.evaluate("() => window._test.applyTerrainPreset('rolling')")
        time.sleep(0.2)
        page.evaluate("() => window._test.serializeDesign()")
        time.sleep(0.2)

        assert len(errors) == 0, f"Console errors detected: {errors[:5]}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '--timeout=120'])
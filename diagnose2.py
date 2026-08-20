#!/usr/bin/env python3
"""Quick diagnostic: test route interception to expose module scope."""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--use-gl=swiftshader']
    )
    context = browser.new_context(viewport={'width': 1400, 'height': 900})
    page = context.new_page()

    # Intercept the HTML and inject window exports at the end of the module
    EXPORTS = '''
// === TEST HARNESS EXPORTS ===
window.__test = {
  THREE, OrbitControls, CATALOG, CATEGORIES, state, scene, renderer, activeCamera, camera3D, camera2D,
  controls, yardMesh, gridHelper, boundaryLines, sceneObjects, groundPlane, mouse, raycaster,
  addObject, buildSceneObject, removeObject, selectObject, deselectObject, showProperties, hideProperties,
  deleteObjectWithCommand, pushCommand, undo, redo,
  serializeDesign, loadDesign, saveDesign, loadFromFile,
  initWithYard, initScene, buildLibrary, renderWizard,
  treeCanopyDiameter, bushDiameter, disposeGroup,
  getTerrainHeight, applyTerrainToMesh, paintTerrain, updateObjectHeight, ensureTerrainArray, getTerrainIndex,
  hasTerrainDeformation, createBrushCursor, removeBrushCursor,
  checkSafetyWarnings, clearSafetyWarnings, addSafetyWarning,
  updateScaleBar, updateGridLabels, updateDimensionLines,
  showDimReadout, hideDimReadout, showToast, showHint, hideHint,
  requestRender, onResize, onPointerDown, onPointerMove, onPointerUp,
  getGroundPoint, makeTextSprite,
  tapeMeasureActive, tapeMeasureStart, tapeMeasureLine, clearTapeMeasure,
  terrainMode, terrainBrushSize, terrainBrushStrength, terrainBrushMode,
};
// === END TEST HARNESS EXPORTS ===
'''

    def handle_route(route, request):
        response = route.fetch()
        body = response.text()
        # Inject exports before the closing </script> tag of the module
        # The module ends with: initScene(); buildLibrary(); renderWizard(); ... </script>
        # We add our exports right before </script>
        modified = body.replace('</script>\n</body>', EXPORTS + '</script>\n</body>')
        route.fulfill(
            status=response.status,
            headers=response.headers,
            body=modified
        )

    page.route('**/index.html', handle_route)
    page.goto("http://localhost:8770/index.html", wait_until="networkidle")
    time.sleep(2)

    # Complete wizard via DOM
    page.eval_on_selector('.shape-card[data-shape="rectangle"]', 'el => el.click()')
    time.sleep(0.2)
    page.eval_on_selector('#wizard-next', 'el => el.click()')
    time.sleep(0.5)
    page.eval_on_selector('#wiz-width', '(el) => { el.value = "50"; }')
    page.eval_on_selector('#wiz-depth', '(el) => { el.value = "100"; }')
    page.eval_on_selector('#wizard-finish', 'el => el.click()')
    time.sleep(1)

    # Test access
    result = page.evaluate('''() => {
        const t = window.__test;
        if (!t) return { error: '__test not defined' };
        return {
            hasTHREE: !!t.THREE,
            hasCATALOG: !!t.CATALOG,
            catalogKeys: t.CATALOG ? Object.keys(t.CATALOG) : [],
            hasState: !!t.state,
            stateYard: t.state ? t.state.yard : null,
            hasScene: !!t.scene,
            hasRenderer: !!t.renderer,
            hasAddObject: typeof t.addObject === 'function',
            hasSelectObject: typeof t.selectObject === 'function',
            hasSerializeDesign: typeof t.serializeDesign === 'function',
            hasGetTerrainHeight: typeof t.getTerrainHeight === 'function',
        };
    }''')
    print("Module scope accessible via window.__test:")
    for k, v in result.items():
        print(f"  {k}: {v}")

    # Test adding an object
    obj_result = page.evaluate('''() => {
        const t = window.__test;
        const id = t.addObject('pool_inground', { width: 16, length: 32, depth: 5, shape: 'rectangle' }, { x: 0, y: 0, z: 0 }, 0);
        const fp = t.CATALOG.pool_inground.footprint(t.state.objects.get(id).params);
        return { id, footprint: fp, objCount: t.state.objects.size };
    }''')
    print(f"\nObject creation test: {obj_result}")

    browser.close()
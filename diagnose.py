#!/usr/bin/env python3
"""Quick diagnostic: what's accessible on window from the page?"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--use-gl=swiftshader']
    )
    context = browser.new_context(viewport={'width': 1400, 'height': 900})
    page = context.new_page()
    page.goto("http://localhost:8770/index.html", wait_until="networkidle")
    time.sleep(2)

    # Complete wizard
    page.eval_on_selector('.shape-card[data-shape="rectangle"]', 'el => el.click()')
    time.sleep(0.2)
    page.eval_on_selector('#wizard-next', 'el => el.click()')
    time.sleep(0.5)
    page.eval_on_selector('#wiz-width', '(el) => { el.value = "50"; }')
    page.eval_on_selector('#wiz-depth', '(el) => { el.value = "100"; }')
    page.eval_on_selector('#wizard-finish', 'el => el.click()')
    time.sleep(1)

    # Check what's on window
    result = page.evaluate('''() => {
        const keys = Object.keys(window).filter(k => !k.startsWith('_') && !['webkitURL','webkitRTCPeerConnection'].includes(k));
        const interesting = {};
        for (const k of ['THREE', 'CATALOG', 'state', 'scene', 'renderer', 'activeCamera', 'camera3D', 'camera2D', 'addObject', 'selectObject', 'deselectObject', 'removeObject', 'buildSceneObject', 'sceneObjects', 'serializeDesign', 'loadDesign', 'saveDesign', 'getTerrainHeight', 'applyTerrainToMesh', 'checkSafetyWarnings', 'clearSafetyWarnings', 'addSafetyWarning', 'updateScaleBar', 'updateGridLabels', 'updateDimensionLines', 'requestRender', 'onPointerDown', 'getGroundPoint', 'OrbitControls', 'controls', 'yardMesh', 'gridHelper', 'boundaryLines', 'initScene', 'initWithYard', 'buildLibrary', 'renderWizard', 'treeCanopyDiameter', 'bushDiameter', 'pushCommand', 'disposeGroup']);
            interesting[k] = typeof window[k] !== 'undefined';
        }
        return interesting;
    }''')
    
    print("Window globals accessible:")
    for k, v in result.items():
        status = "✅" if v else "❌"
        print(f"  {status} {k}")

    # Check if there's a way to access module scope
    # Sometimes modules expose things via custom events or data attributes
    canvas_info = page.evaluate('''() => {
        const canvas = document.querySelector('#viewport canvas');
        return canvas ? { 
            width: canvas.width, 
            height: canvas.height,
            hasContext: !!canvas.getContext('webgl') || !!canvas.getContext('webgl2')
        } : null;
    }''')
    print(f"\nCanvas info: {canvas_info}")
    
    # Check if we can inject a script to expose module scope
    page.add_script_tag(content='''
        // This script runs in page context, not module context
        // We need to find a way to access module-scoped variables
    ''')
    
    # Actually, we can expose module scope by adding code to the page
    # Let's try: modify the page source to add window exports
    
    browser.close()
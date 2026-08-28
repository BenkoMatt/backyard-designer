"""V01 root-cause hunt: log which branch of onPointerDown executes for a real drag."""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    page.locator("#wp-scratch").click(); page.wait_for_timeout(300)

    # instrument BEFORE object placement: watch for selectObject effect + hint text
    page.evaluate("""() => {
        window.__dbg = { hints: [], down: 0, move: 0, up: 0 };
        const vp = document.getElementById('viewport');
        vp.addEventListener('pointerdown', () => window.__dbg.down++, true);
        vp.addEventListener('pointermove', () => window.__dbg.move++, true);
        vp.addEventListener('pointerup', () => window.__dbg.up++, true);
        // watch the hint element
        const hint = document.getElementById('context-hint');
        new MutationObserver(() => window.__dbg.hints.push(hint.textContent))
          .observe(hint, {attributes: true, attributeFilter: ['class'], childList: true, characterData: true});
        // watch controls.enabled flips: can't reach module var; watch hint instead
    }""")
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(600)
    screen = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const r = window._bydRenderer.domElement.getBoundingClientRect();
        return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
    }""")
    print("screen:", screen)
    page.mouse.move(screen["x"], screen["y"])
    page.mouse.down()
    page.mouse.move(screen["x"] + 80, screen["y"] + 40, steps=8)
    page.mouse.up()
    page.wait_for_timeout(500)
    print("dbg:", json.dumps(page.evaluate("() => window.__dbg")))
    print("hint now:", page.evaluate("() => document.getElementById('context-hint').textContent"))
    print("pos:", page.evaluate("() => window._bydState.objects.get(1).position"))
    # Check whether OrbitControls is enabled and attached to the same canvas —
    # if controls captured the pointer, the app handler still ran (both fire).
    print("selectedId:", page.evaluate("() => window._bydState.selectedId"))
    ctx.close()
    browser.close()
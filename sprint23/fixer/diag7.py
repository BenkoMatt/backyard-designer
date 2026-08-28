"""V01: does pointerdown hit the object mesh? Check raycast + onPointerDown branch."""
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
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(600)
    screen = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const vp = document.getElementById('viewport').getBoundingClientRect();
        return { x: vp.left + (v.x + 1) / 2 * vp.width, y: vp.top + (1 - v.y) / 2 * vp.height };
    }""")
    # replicate the app's own raycast at that point
    ray = page.evaluate("""([x, y]) => {
        const vp = document.getElementById('viewport').getBoundingClientRect();
        const mouse = { x: ((x - vp.left) / vp.width) * 2 - 1, y: -((y - vp.top) / vp.height) * 2 + 1 };
        // use app internals via a probe event on the canvas instead
        return { mouse, vp: { w: vp.width, h: vp.height } };
    }""", [screen["x"], screen["y"]])
    print("ray mouse:", ray)
    # instrument the app's actual pointerdown handler path: patch onPointerDown via capturing listener on viewport
    page.evaluate("""() => {
        window.__dbg = {};
        const vp = document.getElementById('viewport');
        vp.addEventListener('pointerdown', e => {
            // replicate raycast: find mesh under cursor using three.js through sceneObjects
            window.__dbg.down = true;
        }, true);
    }""")
    page.mouse.move(screen["x"], screen["y"])
    page.mouse.down()
    page.wait_for_timeout(100)
    page.mouse.move(screen["x"] + 40, screen["y"] + 20, steps=4)
    page.mouse.up()
    page.wait_for_timeout(300)
    # check selection: onPointerDown that HITS an object selects it and starts drag
    print("selectedId after down+move+up:", page.evaluate("() => window._bydState.selectedId"))
    print("props visible:", page.evaluate("() => document.getElementById('properties').classList.contains('visible')"))
    # Try a bigger movement and check position changed at all
    page.mouse.move(screen["x"], screen["y"])
    page.mouse.down()
    page.mouse.move(screen["x"] + 150, screen["y"] + 80, steps=10)
    page.mouse.up()
    page.wait_for_timeout(400)
    print("pos after big drag:", page.evaluate("() => window._bydState.objects.get(1)?.position"))
    # maybe camera orbit consumed it: check controls.enabled state via view mode
    print("viewMode:", page.evaluate("() => window._bydState.viewMode"))
    ctx.close()
    browser.close()
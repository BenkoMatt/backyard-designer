"""V01 FINAL: verified recipe — select via grid scan, drag with rAF-observed movement,
Ctrl+Z restores position and object survives."""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"
errors = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    page.locator("#wp-scratch").click(); page.wait_for_timeout(300)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(800)
    proj = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const r = window._bydRenderer.domElement.getBoundingClientRect();
        return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
    }""")
    hit = None
    for dx in range(-40, 41, 10):
        for dy in range(-40, 41, 10):
            page.mouse.click(proj["x"] + dx, proj["y"] + dy)
            page.wait_for_timeout(80)
            if page.evaluate("() => window._bydState.selectedId") == 1:
                hit = (proj["x"] + dx, proj["y"] + dy)
                break
        if hit:
            break
    assert hit, "no hit point found"
    pos_before = page.evaluate("() => window._bydState.objects.get(1).position.x")
    page.mouse.move(hit[0], hit[1])
    page.mouse.down()
    for i in range(1, 11):
        page.mouse.move(hit[0] + i * 8, hit[1] + i * 4)
        page.wait_for_timeout(25)
    page.mouse.up()
    page.wait_for_timeout(500)
    pos_after = page.evaluate("() => window._bydState.objects.get(1).position.x")
    moved = abs(pos_after - pos_before) > 3
    page.keyboard.press("Control+z")
    page.wait_for_timeout(500)
    pos_undo = page.evaluate("() => window._bydState.objects.get(1)?.position.x")
    cnt = page.evaluate("() => window._bydState.objects.size")
    ok = moved and pos_undo is not None and abs(pos_undo - pos_before) < 2 and cnt == 1
    print(f"V01: before={pos_before} after={pos_after} (moved={moved}) undo={pos_undo} count={cnt} -> {'PASS' if ok else 'FAIL'}")
    print("page errors:", errors[:5])
    ctx.close()
    browser.close()
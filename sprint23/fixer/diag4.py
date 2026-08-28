"""Where do pointer events land? Check elementFromPoint + overlay interception."""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    # dismiss wizard properly first (real Escape)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(600)
    screen = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const vp = document.getElementById('viewport').getBoundingClientRect();
        return { x: vp.left + (v.x + 1) / 2 * vp.width, y: vp.top + (1 - v.y) / 2 * vp.height };
    }""")
    hit = page.evaluate("""([x, y]) => {
        const el = document.elementFromPoint(x, y);
        return el ? { tag: el.tagName, id: el.id, cls: el.className && el.className.toString().slice(0, 60) } : null;
    }""", [screen["x"], screen["y"]])
    print("elementFromPoint at object:", hit)
    # what's at the offset?
    hit2 = page.evaluate("""([x, y]) => {
        const el = document.elementFromPoint(x, y);
        return el ? { tag: el.tagName, id: el.id, cls: el.className && el.className.toString().slice(0, 60) } : null;
    }""", [screen["x"] + 80, screen["y"] + 40])
    print("elementFromPoint at +80,+40:", hit2)
    # instrument + drag
    page.evaluate("""() => {
        window.__ptr = [];
        const vp = document.getElementById('viewport');
        ['pointerdown','pointermove','pointerup'].forEach(t =>
            vp.addEventListener(t, e => window.__ptr.push({t, x: e.clientX, y: e.clientY})));
        window.__docptr = [];
        document.addEventListener('pointerdown', e => window.__docptr.push({x: e.clientX, y: e.clientY, t: e.target.tagName + '#' + (e.target.id || '')}), true);
    }""")
    page.mouse.move(screen["x"], screen["y"])
    page.mouse.down()
    page.mouse.move(screen["x"] + 80, screen["y"] + 40, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)
    print("vp ptr events:", len(page.evaluate("() => window.__ptr")), " doc ptr:", json.dumps(page.evaluate("() => window.__docptr"))[:300])
    print("pos:", page.evaluate("() => window._bydState.objects.get(1)?.position"))
    browser.close()
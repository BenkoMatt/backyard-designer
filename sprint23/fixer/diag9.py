"""V01: find the real canvas (renderer.domElement) and its size/position."""
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
    info = page.evaluate("""() => {
        const canvases = Array.from(document.querySelectorAll('canvas'));
        return canvases.map(c => {
            const r = c.getBoundingClientRect();
            return { id: c.id, cls: c.className.toString().slice(0,40), parent: c.parentElement.id || c.parentElement.className.toString().slice(0,30),
                     x: r.left, y: r.top, w: r.width, h: r.height };
        });
    }""")
    print(json.dumps(info, indent=1))
    # renderer canvas size vs CSS
    rd = page.evaluate("() => { const c = window._bydRenderer && window._bydRenderer.domElement; if (!c) return null; const r = c.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height, attrW: c.width, attrH: c.height }; }")
    print("renderer.domElement rect:", rd)
    vp = page.evaluate("() => { const r = document.getElementById('viewport').getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; }")
    print("viewport rect:", vp)
    ctx.close()
    browser.close()
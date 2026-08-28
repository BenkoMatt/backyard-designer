"""V13/V14 diagnosis: loadDesign with dup ids [7,7,8] -> what happened?"""
import json
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8304/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    data = {"version": 1, "nextId": 5, "yard": {"width": 50, "depth": 100, "shape": "rectangle"},
            "objects": [
                {"id": 7, "type": "bush_round", "params": {}, "position": {"x": 5, "y": 0, "z": 5}, "rotation": 0, "scale": 1},
                {"id": 7, "type": "hedge_formal", "params": {}, "position": {"x": -5, "y": 0, "z": 5}, "rotation": 0, "scale": 1},
                {"id": 8, "type": "tree_deciduous", "params": {}, "position": {"x": 0, "y": 0, "z": 10}, "rotation": 0, "scale": 1}]}
    r = page.evaluate("""data => {
        window.loadDesign(data);
        return {
            count: window._bydState.objects.size,
            nextId: window._bydState.nextId,
            types: Array.from(window._bydState.objects.values()).map(o => ({id: o.id, t: o.type})),
            toast: document.getElementById('toast').textContent
        };
    }""", data)
    print("V13 result:", json.dumps(r, indent=1))
    # is loadDesign the wrapper (line 14818) that re-parses?
    print("loadDesign name:", page.evaluate("() => window.loadDesign.name"))
    print("loadDesign src head:", page.evaluate("() => window.loadDesign.toString().slice(0, 300)"))
    ctx.close()
    browser.close()
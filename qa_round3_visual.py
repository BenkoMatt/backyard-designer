#!/usr/bin/env python3
"""Round 3 visual bug test - screenshots of every object + scenes"""
import json, os
from playwright.sync_api import sync_playwright

URL = "http://localhost:8772/index.html"
DIR = "/tmp/r3-visual"
os.makedirs(DIR, exist_ok=True)

results = {"objects": {}, "scenes": {}}
bugs = []

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--use-gl=swiftshader']
    )
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))

    def setup(width=50, depth=100, shape="rectangle"):
        page.goto(URL, wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(1000)
        if shape == "L":
            page.evaluate("""() => {
                const card = document.querySelector('.shape-card[data-shape="L"]');
                if (card) card.click();
            }""")
            page.wait_for_timeout(200)
        page.click("#wizard-next")
        page.wait_for_timeout(300)
        page.fill("#wiz-width", str(width))
        page.fill("#wiz-depth", str(depth))
        page.wait_for_timeout(200)
        page.click("#wizard-finish")
        page.wait_for_timeout(1500)
        page.evaluate("() => document.querySelectorAll('.cat-section').forEach(s => s.classList.remove('collapsed'))")
        page.wait_for_timeout(200)
        errors.clear()

    OBJECT_NAMES = [
        "Privacy Fence", "Picket Fence", "Pergola", "Garden Shed",
        "In-Ground Pool", "Hot Tub",
        "Shade Tree", "Evergreen Tree", "Bush / Shrub", "Hedge Row",
        "Patio", "Deck", "Walkway", "Raised Garden Bed", "Retaining Wall", "Lawn Area",
        "Fire Pit", "Patio Chair", "Patio Table", "Lounge Chair", "Grill"
    ]

    for obj_name in OBJECT_NAMES:
        safe = obj_name.replace(" ", "_").replace("/", "_")
        setup()
        clicked = page.evaluate(f"""() => {{
            const items = document.querySelectorAll('.lib-item');
            for (const item of items) {{
                if (item.textContent.includes('{obj_name}')) {{ item.click(); return true; }}
            }}
            return false;
        }}""")
        page.wait_for_timeout(800)
        if not clicked:
            bugs.append({"obj": obj_name, "issue": "Not found in library", "severity": "High"})
            continue
        if errors:
            bugs.append({"obj": obj_name, "issue": f"Add error: {errors[:2]}", "severity": "Critical"})

        # 3D screenshot
        page.screenshot(path=f"{DIR}/{safe}_3d.png")

        # 2D screenshot
        page.click("button[data-view='2d']")
        page.wait_for_timeout(600)
        page.screenshot(path=f"{DIR}/{safe}_2d.png")

        # Properties panel?
        props = page.evaluate("() => document.getElementById('properties')?.classList.contains('visible')")
        dim = page.evaluate("() => document.getElementById('dim-readout')?.textContent?.trim()")
        grids = page.evaluate("() => document.getElementById('grid-labels')?.querySelectorAll('.grid-label')?.length || 0")

        results["objects"][obj_name] = {
            "errors": len(errors), "props": props,
            "dim": dim[:80] if dim else None, "grids": grids
        }

        # Back to 3D
        page.click("button[data-view='3d']")
        page.wait_for_timeout(400)

        # Color change
        has_color = page.evaluate("""() => {
            const input = document.querySelector('input[data-param="color"]');
            return !!input;
        }""")
        if has_color:
            page.evaluate("""() => {
                const input = document.querySelector('input[data-param="color"]');
                if (input) { input.value = '#FF0000'; input.dispatchEvent(new Event('change', {bubbles:true})); }
            }""")
            page.wait_for_timeout(400)
            page.screenshot(path=f"{DIR}/{safe}_color.png")
            if errors:
                bugs.append({"obj": obj_name, "issue": f"Color error: {errors[:1]}", "severity": "Medium"})

        # Max size
        page.evaluate("""() => {
            document.querySelectorAll('input[data-param]').forEach(input => {
                if (input.type === 'number' && input.max) {
                    input.value = input.max; input.dispatchEvent(new Event('change', {bubbles:true}));
                }
            });
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=f"{DIR}/{safe}_max.png")
        if errors:
            bugs.append({"obj": obj_name, "issue": f"Max size error: {errors[:1]}", "severity": "High"})

        # Min size
        page.evaluate("""() => {
            document.querySelectorAll('input[data-param]').forEach(input => {
                if (input.type === 'number' && input.min) {
                    input.value = input.min; input.dispatchEvent(new Event('change', {bubbles:true}));
                }
            });
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=f"{DIR}/{safe}_min.png")
        if errors:
            bugs.append({"obj": obj_name, "issue": f"Min size error: {errors[:1]}", "severity": "High"})

        # Rotation
        page.evaluate("""() => document.querySelector('.rotate-btn[data-rotate="90"]')?.click()""")
        page.wait_for_timeout(400)
        page.screenshot(path=f"{DIR}/{safe}_rot90.png")

    # Multi-object scenes
    # Pool + Deck
    setup()
    page.evaluate("""() => {
        const items = document.querySelectorAll('.lib-item');
        for (const item of items) {
            if (item.textContent.includes('In-Ground Pool') || item.textContent.includes('Deck')) item.click();
        }
    }""")
    page.wait_for_timeout(1500)
    page.screenshot(path=f"{DIR}/scene_pool_deck_3d.png")
    page.click("button[data-view='2d']")
    page.wait_for_timeout(600)
    page.screenshot(path=f"{DIR}/scene_pool_deck_2d.png")
    results["scenes"]["pool+deck"] = len(errors)
    if errors: bugs.append({"scene": "pool+deck", "issue": f"Errors: {errors[:1]}", "severity": "Medium"})

    # Patio set
    setup()
    page.evaluate("""() => {
        const items = document.querySelectorAll('.lib-item');
        for (const item of items) {
            if (item.textContent.includes('Patio') || item.textContent.includes('Grill') || item.textContent.includes('Chair')) item.click();
        }
    }""")
    page.wait_for_timeout(1500)
    page.screenshot(path=f"{DIR}/scene_patio_set_3d.png")
    results["scenes"]["patio_set"] = len(errors)

    # All 21
    setup()
    page.evaluate("() => { document.querySelectorAll('.lib-item').forEach(i => i.click()); }")
    page.wait_for_timeout(2500)
    page.screenshot(path=f"{DIR}/scene_all21_3d.png")
    page.click("button[data-view='2d']")
    page.wait_for_timeout(600)
    page.screenshot(path=f"{DIR}/scene_all21_2d.png")
    results["scenes"]["all21"] = len(errors)
    if errors: bugs.append({"scene": "all21", "issue": f"Errors: {errors[:1]}", "severity": "High"})

    # L-shape
    setup(shape="L")
    page.evaluate("() => { document.querySelectorAll('.lib-item').forEach(i => i.click()); }")
    page.wait_for_timeout(2500)
    page.screenshot(path=f"{DIR}/scene_lshape_3d.png")
    page.click("button[data-view='2d']")
    page.wait_for_timeout(600)
    page.screenshot(path=f"{DIR}/scene_lshape_2d.png")
    results["scenes"]["lshape"] = len(errors)
    if errors: bugs.append({"scene": "L-shape", "issue": f"Errors: {errors[:1]}", "severity": "High"})

    # Tiny 10x10
    setup(10, 10)
    page.evaluate("() => { document.querySelectorAll('.lib-item').forEach(i => i.click()); }")
    page.wait_for_timeout(2500)
    page.screenshot(path=f"{DIR}/scene_tiny_10x10.png")
    results["scenes"]["tiny"] = len(errors)
    if errors: bugs.append({"scene": "10x10", "issue": f"Errors: {errors[:1]}", "severity": "High"})

    # Huge 200x500
    setup(200, 500)
    page.evaluate("() => { document.querySelectorAll('.lib-item').forEach(i => i.click()); }")
    page.wait_for_timeout(2500)
    page.screenshot(path=f"{DIR}/scene_huge_200x500.png")
    results["scenes"]["huge"] = len(errors)
    if errors: bugs.append({"scene": "200x500", "issue": f"Errors: {errors[:1]}", "severity": "High"})

    # Terrain + objects
    setup()
    page.evaluate("() => { document.querySelectorAll('.lib-item').forEach(i => i.click()); }")
    page.wait_for_timeout(2000)
    page.click("#terrain-btn")
    page.wait_for_timeout(400)
    canvas = page.query_selector("canvas")
    if canvas:
        box = canvas.bounding_box()
        page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
        page.mouse.down()
        page.mouse.move(box["x"] + box["width"]/2 + 80, box["y"] + box["height"]/2 + 40)
        page.wait_for_timeout(200)
        page.mouse.up()
        page.wait_for_timeout(500)
    page.screenshot(path=f"{DIR}/scene_terrain_3d.png")
    page.click("#terrain-btn")
    page.wait_for_timeout(300)
    results["scenes"]["terrain"] = len(errors)
    if errors: bugs.append({"scene": "terrain", "issue": f"Errors: {errors[:1]}", "severity": "High"})

    results["bugs"] = bugs
    results["total_errors"] = len(errors)
    results["screenshot_count"] = len(os.listdir(DIR))
    browser.close()

print(json.dumps(results, indent=2))
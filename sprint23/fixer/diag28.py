"""Diagnose why wizard stays open after Escape in this flow: maybe the wizard
finish/skip button must run. Read the wizard close paths."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8304/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    print("wizard display before:", repr(page.evaluate("() => document.getElementById('wizard').style.display")))
    # is the wizard actually covering the screen?
    print("wizard rect:", page.evaluate("() => { const r = document.getElementById('wizard').getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height}; }"))
    print("wiz computed display:", page.evaluate("() => getComputedStyle(document.getElementById('wizard')).display"))
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    print("wizard display after Esc:", repr(page.evaluate("() => document.getElementById('wizard').style.display")))
    # what happens on the wizard finish button? (real path users take)
    page.reload(); page.wait_for_timeout(1500)
    # click through the wizard: finish button
    btns = page.evaluate("() => Array.from(document.querySelectorAll('#wizard button')).map(b => ({id: b.id, text: b.textContent.trim().slice(0,30)}))")
    print("wizard buttons:", btns)
    ctx.close()
    browser.close()
#!/usr/bin/env python3
"""One-off: capture the first-run wizard screenshot (fresh profile each launch)."""
import os
from playwright.sync_api import sync_playwright

MODE = os.environ.get("BYD_MODE", "before")
OUT = f"/root/byd22-visual-consistency/reports/sprint22_shots/{MODE}"
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader"])
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto("http://localhost:8175/index.html", wait_until="load", timeout=30000)
    page.wait_for_timeout(900)
    page.screenshot(path=f"{OUT}/wizard.png")
    vis = page.evaluate("() => { const w = document.querySelector('#wizard .wizard-panel'); if (!w) return null; const cs = getComputedStyle(w); const r = w.getBoundingClientRect(); return {radius: cs.borderRadius, padding: cs.padding, w: Math.round(r.width), h: Math.round(r.height)}; }")
    print("wizard panel:", vis)
    browser.close()
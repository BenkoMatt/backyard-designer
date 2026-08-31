"""Measure tool-dock vs dock-panel overlap + status-bar overlaps (observation only)."""
import json
import os
from playwright.sync_api import sync_playwright
from s23a_common import load_app, to_advanced
import s23a_common
s23a_common.URL = "http://localhost:8092/index.html"

PROBE = """() => {
  const r = {};
  for (const sel of ['#tool-dock', '#dock-panel-container', '#status-bar', '#view-controls', '#sidebar', '#bottom-left-toolbar']) {
    const el = document.querySelector(sel);
    if (!el) { r[sel] = null; continue; }
    const b = el.getBoundingClientRect();
    r[sel] = { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height),
               z: getComputedStyle(el).zIndex };
  }
  // measure widest tab
  let tw = 0;
  document.querySelectorAll('.td-tab').forEach(t => { tw = Math.max(tw, t.getBoundingClientRect().width); });
  r['.td-tab max width'] = Math.round(tw);
  return r;
}"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    load_app(page)
    to_advanced(page)
    print(json.dumps(page.evaluate(PROBE), indent=1))
    # open underground dock, take focused screenshot of the area
    page.click('.td-tab[data-dock="underground"]')
    page.wait_for_timeout(500)
    page.screenshot(path="s23b_before_3_dock_area.png", clip={"x": 0, "y": 480, "width": 640, "height": 320})
    browser.close()
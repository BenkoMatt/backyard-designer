"""The CSS says left:340px but measured x=620 — probe AFTER the welcome prompt dismissal
vs before, and check whether a JS transform/margin happens later. Sample rect over time."""
import sys
import time as _t
sys.path.insert(0, "/root/byd29r-modals")
from r3_common import load_app, make_page
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page, errors = make_page(p)
    load_app(page)
    for i in range(8):
        r = page.evaluate("() => { const b = document.getElementById('bottom-left-toolbar').getBoundingClientRect();"
                          " return {x: Math.round(b.x), w: Math.round(b.width), h: Math.round(b.height)}; }")
        print(_t.strftime("%H:%M:%S"), r)
        _t.sleep(1)
    # also try at 1024
    page.set_viewport_size({"width": 1024, "height": 768})
    _t.sleep(1.5)
    r = page.evaluate("() => { const b = document.getElementById('bottom-left-toolbar').getBoundingClientRect();"
                      " const s = document.querySelector('#scale-bar').getBoundingClientRect();"
                      " return {x: Math.round(b.x), w: Math.round(b.width), h: Math.round(b.height), scaleRight: Math.round(s.right)}; }")
    print("1024x768:", r)
    browser.close()
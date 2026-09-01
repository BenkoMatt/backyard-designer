"""Precise geometry probe: scale-bar vs sun-btn vs toolbar at both resolutions, both modes."""
import json
import sys

sys.path.insert(0, "/root/byd29r-modals")
from r3_common import load_app, make_page, to_advanced
from playwright.sync_api import sync_playwright

out = {}
with sync_playwright() as p:
    for (w, h) in [(1280, 800), (1600, 900)]:
        browser, page, errors = make_page(p, w, h)
        load_app(page)
        key = f"{w}x{h}_basic"
        out[key] = page.evaluate("""() => {
        const r = (s) => { const e = document.querySelector(s); if (!e) return null;
            const b = e.getBoundingClientRect(); return {x: Math.round(b.x), right: Math.round(b.right), y: Math.round(b.y), bottom: Math.round(b.bottom), w: Math.round(b.width), h: Math.round(b.height)}; };
        const tb = r('#bottom-left-toolbar');
        const kids = [...document.querySelectorAll('#bottom-left-toolbar > button')].map(b => {
            const bb = b.getBoundingClientRect();
            return {id: b.id, x: Math.round(bb.x), right: Math.round(bb.right), y: Math.round(bb.y)};
        });
        return {scalebar: r('#scale-bar'), toolbar: tb, kids,
                sunbtn: r('#sun-btn'), statusbar: r('#status-bar'),
                viewcontrols: r('#view-controls'), viewkids: [...document.querySelectorAll('#view-controls button')].slice(0,3).map(b=>{const bb=b.getBoundingClientRect();return {id:b.id,x:Math.round(bb.x),y:Math.round(bb.y),right:Math.round(bb.right)};})};
    }""")
        print(key, json.dumps(out[key]))
        browser.close()

with open("/tmp/r3_geo.json", "w") as f:
    json.dump(out, f, indent=1)
"""Probe topbar overflow state + the bottom-center '5 ft' segmented control + status bar,
at 1280x800 and 1600x900, Basic and Advanced. Read-only DOM probes."""
import json
import sys

sys.path.insert(0, "/root/byd29r-modals")
from r3_common import load_app, make_page, to_advanced
from playwright.sync_api import sync_playwright

out = {}
with sync_playwright() as p:
    for (w, h) in [(1280, 800), (1600, 900)]:
        for mode in ["basic", "advanced"]:
            browser, page, errors = make_page(p, w, h)
            load_app(page)
            if mode == "advanced":
                to_advanced(page)
            key = f"{w}x{h}_{mode}"
            out[key] = page.evaluate("""() => {
        const tb = document.getElementById('topbar');
        const tbR = tb.getBoundingClientRect();
        const btns = [...tb.querySelectorAll('.tb-btn')].map(b => {
            const r = b.getBoundingClientRect();
            return {id: b.id, x: Math.round(r.x), right: Math.round(r.right), w: Math.round(r.width),
                    clipped: r.right > innerWidth + 1 || r.x < -1,
                    fullyVisible: r.right <= innerWidth && r.x >= 0,
                    visible: r.width > 0 && getComputedStyle(b).display !== 'none'};
        });
        // what is the bottom-center '5 ft' element?
        const cands = [];
        document.querySelectorAll('#viewport, #viewport *').forEach(e => {
            const r = e.getBoundingClientRect();
            if (r.width > 0 && r.y + r.height > innerHeight - 90 && r.y < innerHeight - 10 &&
                r.x > 300 && r.x + r.width < innerWidth - 200) {
                const cs = getComputedStyle(e);
                if (cs.position === 'absolute' || cs.position === 'fixed') {
                    cands.push({id: e.id || e.className, x: Math.round(r.x), y: Math.round(r.y),
                                w: Math.round(r.width), h: Math.round(r.height), txt: (e.textContent||'').trim().slice(0,25)});
                }
            }
        });
        const sbTool = document.getElementById('sb-tool');
        const fpsItem = document.getElementById('sb-fps-item');
        return {topbar: {clientW: tb.clientWidth, scrollW: tb.scrollWidth,
                         overflow: tb.scrollWidth > tb.clientWidth + 2,
                         scrolledEnd: tb.classList.contains('scrolled-end')},
                btns: btns.filter(b => b.visible),
                bottomCenter: cands.slice(0, 12),
                sbTool: sbTool ? sbTool.textContent : null,
                fpsHidden: fpsItem ? fpsItem.hidden : null};
    }""")
            print(key, json.dumps(out[key]["topbar"]))
            for b in out[key]["btns"]:
                if b["clipped"]:
                    print("  CLIPPED:", b)
            print("  bottomCenter:", json.dumps(out[key]["bottomCenter"]))
            print("  sbTool:", out[key]["sbTool"], "fpsHidden:", out[key]["fpsHidden"])
            browser.close()

with open("/tmp/r3_probe_topbar.json", "w") as f:
    json.dump(out, f, indent=1)
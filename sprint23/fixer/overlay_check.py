"""Trace the gate's state at the btn-shortcuts click: after '?' opens guide, Escape
closes it, F1 opens, Escape closes. Now click #btn-shortcuts times out => an overlay
intercepts pointer events. Which? Probe after simulating that exact sequence."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://localhost:8304/index.html", timeout=30000)
    page.wait_for_timeout(2500)
    page.keyboard.press('Shift+Slash'); page.wait_for_timeout(400)
    page.keyboard.press('Escape'); page.wait_for_timeout(300)
    page.keyboard.press('F1'); page.wait_for_timeout(400)
    page.keyboard.press('Escape'); page.wait_for_timeout(300)
    st = page.evaluate("""() => {
        const ids = ['welcome-prompt', 'cmd-palette-overlay', 'shortcuts-modal', 'help-modal', 'wizard'];
        const out = {};
        for (const id of ids) {
            const el = document.getElementById(id);
            out[id] = el ? {cls: el.className, disp: getComputedStyle(el).display, pe: getComputedStyle(el).pointerEvents} : 'absent';
        }
        out.topAtBtn = (() => {
            const b = document.getElementById('btn-shortcuts');
            const r = b.getBoundingClientRect();
            const el = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
            return el ? (el.id || el.className || el.tagName) : 'none';
        })();
        return out;
    }""")
    import json
    print(json.dumps(st, indent=1))
    browser.close()
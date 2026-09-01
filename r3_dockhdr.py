"""DOM-verify: dock-terrain header buttons vs panel right edge; label sprite anchor;
share-url-box height; cmd palette input border."""
import sys, json
sys.path.insert(0, "/root/byd29r-modals")
from r3_common import load_app, make_page
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page, errors = make_page(p)
    load_app(page)
    page.locator(".td-tab[data-dock='terrain']").click(force=True)
    page.wait_for_timeout(700)
    out = page.evaluate("""() => {
    const d = document.getElementById('dock-terrain');
    const dr = d.getBoundingClientRect();
    const hdr = d.querySelector('.dock-panel-header');
    const hr = hdr ? hdr.getBoundingClientRect() : null;
    const btns = [...d.querySelectorAll('.dock-panel-header button')].map(b => {
        const r = b.getBoundingClientRect();
        return {cls: b.className, x: Math.round(r.x), right: Math.round(r.right), w: Math.round(r.width),
                outsidePanel: r.right > dr.right + 0.5 || r.x < dr.x - 0.5};
    });
    const input = document.getElementById('cmd-palette-input');
    const cs = input ? getComputedStyle(input) : null;
    return {panel: {x: Math.round(dr.x), right: Math.round(dr.right), w: Math.round(dr.width)},
            header: hr ? {x: Math.round(hr.x), right: Math.round(hr.right)} : null,
            headerBtns: btns,
            cmdInputBorderBottom: cs ? cs.borderBottomWidth + ' ' + cs.borderBottomStyle : null};
}""")
    print(json.dumps(out, indent=1))
    browser.close()
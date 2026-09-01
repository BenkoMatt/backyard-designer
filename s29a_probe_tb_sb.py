"""S29 Agent 1 — probe topbar right-edge clipping + sidebar scroll cue (read-only)."""
import json
import sys
sys.path.insert(0, "/root/byd29-audit-core")
from s29a_common import load_app, make_browser, dismiss_overlays, to_advanced
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page, errors = make_browser(p, 1280, 800)
    load_app(page, fresh=False)
    dismiss_overlays(page)
    r = page.evaluate("""() => {
        const out = {};
        const tb = document.getElementById('topbar');
        const tr = tb.getBoundingClientRect();
        out.topbar = {x:tr.x, y:tr.y, w:tr.width, h:tr.height};
        out.tb_scrollW = tb.scrollWidth; out.tb_clientW = tb.clientWidth;
        out.tb_overflow = getComputedStyle(tb).overflow + '/' + getComputedStyle(tb).overflowX;
        // last button position
        const btns = tb.querySelectorAll('.tb-btn');
        const last = btns[btns.length-1];
        const lr = last.getBoundingClientRect();
        out.last_btn = {id:last.id, x:lr.x, right:lr.right, w:lr.width, clipped: lr.right > window.innerWidth};
        out.btn_count = btns.length;
        // every tb-btn right edge
        out.clipped_btns = [];
        btns.forEach(b => {
            const r2 = b.getBoundingClientRect();
            if (r2.right > window.innerWidth + 0.5 || r2.left < -0.5)
                out.clipped_btns.push({id: b.id, left: r2.left, right: r2.right});
        });
        // sidebar scroll cue
        const sb = document.getElementById('sidebar');
        out.sidebar = {clientH: sb.clientHeight, scrollH: sb.scrollHeight, at_bottom: sb.scrollHeight - sb.clientHeight - sb.scrollTop < 2};
        const lib = document.getElementById('library');
        const items = lib.querySelectorAll('.lib-item');
        const lastit = items[items.length-1].getBoundingClientRect();
        out.last_item = {y: lastit.y, bottom: lastit.bottom, h: lastit.height};
        out.item_count = items.length;
        out.sb_padding_bottom = getComputedStyle(sb).paddingBottom;
        const sbar = document.getElementById('status-bar');
        const sr = sbar.getBoundingClientRect();
        out.status_bar = {y: sr.y, h: sr.height, bottom: sr.bottom};
        return out;
    }""")
    print(json.dumps(r, indent=1))

    to_advanced(page)
    r2 = page.evaluate("""() => {
        const tb = document.getElementById('topbar');
        const btns = tb.querySelectorAll('.tb-btn');
        const out = {clipped: []};
        btns.forEach(b => {
            const r2 = b.getBoundingClientRect();
            if (r2.right > window.innerWidth + 0.5) out.clipped.push({id:b.id, right:r2.right});
        });
        out.scrollW = tb.scrollWidth;
        return out;
    }""")
    print("advanced:", json.dumps(r2))
    print("ERRORS:", errors[:5])
    browser.close()
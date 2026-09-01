"""Measure what a compact toolbar would need to fit 6 buttons in one row at 1280."""
import sys
sys.path.insert(0, "/root/byd29r-modals")
from r3_common import load_app, make_page
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page, errors = make_page(p)
    load_app(page)
    data = page.evaluate("""() => {
    const kids = [...document.querySelectorAll('#bottom-left-toolbar > button')];
    const widths = kids.map(b => Math.round(b.getBoundingClientRect().width));
    const total = widths.reduce((a,b)=>a+b,0);
    const gaps = (kids.length - 1) * 6; // gap:6px
    return {widths, total, gaps, totalWithGaps: total + gaps,
            scalebarRight: Math.round(document.querySelector('#scale-bar').getBoundingClientRect().right),
            viewControlsLeft: Math.round(document.querySelector('#view-controls').getBoundingClientRect().x)};
}""")
    print(data)
    # current: total 614 with gaps. Available span at 1280: from toolbar.x 620 to view-controls 1224 => 604. 614 > 604 → wraps.
    # Needed savings: 614-604=10px + safety. Reduce per-button padding from 7px 14px to 7px 10px → saves ~8px/button * 6 = 48px.
    browser.close()
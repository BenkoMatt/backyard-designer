"""Why is #bottom-left-toolbar at x620 when CSS says left:340px? Probe computed style."""
import sys
sys.path.insert(0, "/root/byd29r-modals")
from r3_common import load_app, make_page
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser, page, errors = make_page(p)
    load_app(page)
    data = page.evaluate("""() => {
    const tb = document.getElementById('bottom-left-toolbar');
    const cs = getComputedStyle(tb);
    const rules = [];
    for (const sheet of document.styleSheets) {
        try {
            for (const r of sheet.cssRules) {
                if (r.selectorText && r.selectorText.includes('bottom-left-toolbar')) {
                    rules.push(r.selectorText + ' {' + (r.style.cssText || '').slice(0, 120) + '}');
                }
            }
        } catch (e) {}
    }
    return {left: cs.left, right: cs.right, transform: cs.transform, marginLeft: cs.marginLeft,
            inlineStyle: tb.getAttribute('style'), rules: rules.slice(0, 8)};
}""")
    import json
    print(json.dumps(data, indent=1))
    browser.close()
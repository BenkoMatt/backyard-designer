"""The wizard is absent and wp hidden; Escape #1 OPENED the welcome prompt (focus wp-scratch).
So Escape is being handled somewhere that re-opens welcome? Check: maybe Escape with nothing
open calls initWithYard?? No - look: after Escape, wpVisible True. Check the wizard Escape
handler at ~8093 - if wizard-modal is absent but handler still runs? Probe the palette flow
with welcome prompt properly dismissed first."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://localhost:8304/index.html", timeout=30000)
    page.wait_for_timeout(2500)
    # dismiss welcome prompt via Escape first (it opens on Escape? weird) - click wp-scratch
    page.keyboard.press('Escape'); page.wait_for_timeout(400)
    wp = page.evaluate("() => { const wp = document.getElementById('welcome-prompt'); return wp ? wp.classList.contains('visible') : false; }")
    print('wp after Escape:', wp)
    if wp:
        page.click('#wp-scratch')
        page.wait_for_timeout(400)
    # Now palette flow
    page.keyboard.press('Control+k'); page.wait_for_timeout(400)
    cls = page.evaluate("() => document.getElementById('cmd-palette-overlay').className")
    print('palette after Ctrl+K:', cls)
    page.keyboard.press('Escape'); page.wait_for_timeout(300)
    cls2 = page.evaluate("() => document.getElementById('cmd-palette-overlay').className")
    print('palette after Escape:', cls2)
    # delete flow
    placed = page.evaluate("""() => {
        const id = window._test.addObject('fence_privacy', {}, { x: -12, y: 0, z: -12 });
        window.selectObject(id);
        const st = window._test.state;
        return { id, selected: st.selectedId, count: st.objects.size };
    }""")
    print('placed:', placed)
    page.keyboard.press('Delete'); page.wait_for_timeout(400)
    s3 = page.evaluate("() => { const st = window._test.state; return {selectedId: st.selectedId, count: st.objects.size}; }")
    print('after Delete:', s3)
    browser.close()
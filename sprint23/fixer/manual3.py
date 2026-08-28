"""Reproduce the 3 S22 failures manually against 8304 to see what state is live:
1) Ctrl+K opens palette -> Escape closes?  2) _test.addObject + selectObject + Delete
3) Shift+Slash opens shortcuts guide."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto("http://localhost:8304/index.html", timeout=30000)
    page.wait_for_timeout(2500)

    # test handles available?
    th = page.evaluate("() => ({test: typeof window._test, addObject: window._test ? typeof window._test.addObject : null, selectObject: typeof window.selectObject})")
    print('handles:', th)

    # 3) Shift+Slash
    page.keyboard.press('Shift+Slash')
    page.wait_for_timeout(400)
    pr = page.evaluate("() => { const el = document.getElementById('shortcuts-modal'); if (!el) return {exists:false}; const cs = getComputedStyle(el); return {exists: true, open: el.classList.contains('visible') && cs.display !== 'none'}; }")
    print('shift-slash probe:', pr)
    page.keyboard.press('Escape'); page.wait_for_timeout(300)

    # 1) palette
    page.keyboard.press('Control+k'); page.wait_for_timeout(400)
    s1 = page.evaluate("() => { const cp = document.getElementById('cmd-palette-overlay'); return {cls: cp ? cp.className : null, disp: cp ? getComputedStyle(cp).display : null}; }")
    print('palette after Ctrl+K:', s1)
    page.keyboard.press('Escape'); page.wait_for_timeout(300)
    s2 = page.evaluate("() => { const cp = document.getElementById('cmd-palette-overlay'); return {cls: cp ? cp.className : null, disp: cp ? getComputedStyle(cp).display : null}; }")
    print('palette after Escape:', s2)

    # 2) place+select+delete
    placed = page.evaluate("""() => {
        if (!window._test || !window._test.addObject) return { error: 'no _test.addObject' };
        const id = window._test.addObject('fence_privacy', {}, { x: -12, y: 0, z: -12 });
        window.selectObject(id);
        const st = window._test.state;
        return { id, selected: st.selectedId, count: st.objects.size };
    }""")
    print('placed:', placed)
    page.keyboard.press('Delete'); page.wait_for_timeout(400)
    s3 = page.evaluate("() => { const st = window._test.state; return {selectedId: st.selectedId, count: st.objects.size}; }")
    print('after Delete:', s3)
    print('pageerrors:', errs[:3])
    browser.close()
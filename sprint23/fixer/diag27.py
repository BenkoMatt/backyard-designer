"""V04 case 2/3: dismiss wizard via real Escape FIRST (it intercepts clicks)."""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"
errors = []

def setup(page, dismiss_wp=True):
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape"); page.wait_for_timeout(600)  # wizard
    if dismiss_wp:
        try:
            wp = page.locator("#wp-scratch")
            if wp.count() > 0 and wp.is_visible():
                wp.click(); page.wait_for_timeout(300)
        except Exception:
            pass
    # verify wizard actually closed
    wiz = page.evaluate("() => document.getElementById('wizard').style.display")
    if wiz != 'none':
        page.keyboard.press("Escape"); page.wait_for_timeout(500)

with sync_playwright() as p:
    browser = p.chromium.launch()

    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V04:" + str(e)))
    setup(page, dismiss_wp=False)
    wiz_state = page.evaluate("() => document.getElementById('wizard').style.display")
    print("wizard state after setup:", repr(wiz_state))
    page.click("#btn-help")
    page.wait_for_timeout(300)
    page.keyboard.press("F1")
    page.wait_for_timeout(300)
    st1 = page.evaluate("""() => ({ help: document.getElementById('help-modal').classList.contains('visible'),
        sc: document.getElementById('shortcuts-modal').classList.contains('visible') })""")
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    st2 = page.evaluate("""() => ({ help: document.getElementById('help-modal').classList.contains('visible'),
        sc: document.getElementById('shortcuts-modal').classList.contains('visible') })""")
    ok = st1["help"] and st1["sc"] and not st2["sc"] and st2["help"]
    print(("PASS " if ok else "FAIL ") + f"V04 help+shortcuts: afterF1={st1} afterEsc={st2}")
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    st3 = page.evaluate("() => document.getElementById('help-modal').classList.contains('visible')")
    print(("PASS " if not st3 else "FAIL ") + "V04 second Esc closes help")
    ctx.close()

    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    setup(page)
    page.click("#btn-help"); page.wait_for_timeout(300)
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    closed = page.evaluate("() => !document.getElementById('help-modal').classList.contains('visible')")
    print(("PASS " if closed else "FAIL ") + "V04 single help modal Esc")
    ctx.close()

    ctx2 = browser.new_context(viewport={"width": 1280, "height": 900})
    page2 = ctx2.new_page()
    page2.goto(BASE, timeout=30000)
    page2.wait_for_timeout(1800)
    page2.keyboard.press("Escape"); page.wait_for_timeout(500)
    w = page2.evaluate("() => document.getElementById('wizard').style.display")
    toast = page2.evaluate("() => document.getElementById('toast').textContent")
    print(("PASS " if w == "none" else "FAIL ") + f"V04 wizard-alone Esc (display={w!r} toast={toast!r})")
    ctx2.close()
    browser.close()
    print("errors:", errors[:5])
"""V04 full re-verify after open-stack change: wizard+guide, help+shortcuts, single modals."""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"
errors = []

def setup(page, dismiss_wp=True):
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    if dismiss_wp:
        try:
            wp = page.locator("#wp-scratch")
            if wp.count() > 0 and wp.is_visible():
                wp.click(); page.wait_for_timeout(300)
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch()

    # Case 1: wizard + guide -> one Escape closes guide only
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V04:" + str(e)))
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("F1"); page.wait_for_timeout(300)
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    r = page.evaluate("""() => ({ wiz: document.getElementById('wizard').style.display !== 'none',
        guide: document.getElementById('shortcuts-modal').classList.contains('visible') })""")
    ok = not r["guide"] and r["wiz"]
    print(("PASS " if ok else "FAIL ") + f"V04 wizard+guide one Esc: {r}")
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    r2 = page.evaluate("() => document.getElementById('wizard').style.display === 'none'")
    print(("PASS " if r2 else "FAIL ") + "V04 second Esc closes wizard")
    ctx.close()

    # Case 2: help + shortcuts -> Escape closes shortcuts (topmost), help stays
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V04:" + str(e)))
    setup(page, dismiss_wp=False)
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

    # Case 3: single modal Escape still closes (regression check)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append("V04:" + str(e)))
    setup(page, dismiss_wp=False)
    page.click("#btn-help"); page.wait_for_timeout(300)
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    closed = page.evaluate("() => !document.getElementById('help-modal').classList.contains('visible')")
    print(("PASS " if closed else "FAIL ") + "V04 single modal Esc")
    # share modal (opened via openModal? check)
    page.evaluate("() => { const b = document.getElementById('btn-share'); if (b) b.click(); }")
    page.wait_for_timeout(300)
    sh = page.evaluate("() => document.getElementById('share-modal').classList.contains('visible')")
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    share_closed = page.evaluate("() => !document.getElementById('share-modal').classList.contains('visible')")
    print(("PASS " if share_closed else "FAIL ") + f"V04 share modal Esc (was open={sh_open})".replace("sh_open", str(sh_open)) if (sh_open := sh) else "share modal did not open (check button id)")
    print("errors:", errors[:5])
    ctx.close()
    browser.close()
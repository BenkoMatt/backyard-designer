"""V04 retest: wizard+guide one-Escape cascade (fix verification) + wizard-alone."""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"
errors = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    # wizard is open on fresh load (display '' = visible via CSS flex)
    w = page.evaluate("() => document.getElementById('wizard').style.display")
    print("wizard initial:", repr(w))
    page.keyboard.press("F1"); page.wait_for_timeout(300)
    before = page.evaluate("""() => ({
        wiz: document.getElementById('wizard').style.display !== 'none',
        guide: document.getElementById('shortcuts-modal').classList.contains('visible')})""")
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    after = page.evaluate("""() => ({
        wiz: document.getElementById('wizard').style.display !== 'none',
        guide: document.getElementById('shortcuts-modal').classList.contains('visible'),
        toast: document.getElementById('toast').textContent})""")
    ok = before["wiz"] and before["guide"] and not after["guide"] and after["wiz"]
    print(f"V04 cascade: before={before} after={after} -> {'PASS' if ok else 'FAIL'}")
    # second Escape closes the wizard (now topmost) and runs its side effect
    page.keyboard.press("Escape"); page.wait_for_timeout(500)
    wiz_after2 = page.evaluate("() => document.getElementById('wizard').style.display === 'none'")
    print(f"V04 second Esc closes wizard: {'PASS' if wiz_after2 else 'FAIL'}")
    # wizard-alone Escape still works
    page.reload(); page.wait_for_timeout(1500)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    w2 = page.evaluate("() => document.getElementById('wizard').style.display === 'none'")
    print(f"V04 wizard-alone Esc closes: {'PASS' if w2 else 'FAIL'}")
    print("errors:", errors[:5])
    ctx.close()
    browser.close()
"""After Escape fails to close palette: check the wizard/welcome-prompt state and what
Escape actually does. Also try Escape twice, and check _modalOpenStack."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://localhost:8304/index.html", timeout=30000)
    page.wait_for_timeout(2500)
    probe = page.evaluate("""() => ({
        stack: window._modalOpenStack || null,
        wpVisible: (() => { const wp = document.getElementById('welcome-prompt'); return wp ? wp.classList.contains('visible') : 'absent'; })(),
        wizardVisible: (() => { const w = document.getElementById('wizard-modal'); return w ? w.classList.contains('visible') : 'absent'; })(),
        paletteCls: document.getElementById('cmd-palette-overlay').className,
    })""")
    print('before any key:', probe)
    page.keyboard.press('Escape'); page.wait_for_timeout(300)
    probe2 = page.evaluate("""() => ({
        stack: window._modalOpenStack || null,
        wpVisible: (() => { const wp = document.getElementById('welcome-prompt'); return wp ? wp.classList.contains('visible') : 'absent'; })(),
        wizardVisible: (() => { const w = document.getElementById('wizard-modal'); return w ? w.classList.contains('visible') : 'absent'; })(),
        paletteCls: document.getElementById('cmd-palette-overlay').className,
        focus: document.activeElement ? (document.activeElement.id || document.activeElement.tagName) : null,
    })""")
    print('after Escape #1:', probe2)
    browser.close()
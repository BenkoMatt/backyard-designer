"""Compare: on ORIG (8306), does Escape also open the welcome prompt? If yes, the s22 gate
used to pass because the wizard was PRESENT at boot and Escape dismissed it. Check wizard
presence on both."""
from playwright.sync_api import sync_playwright

for port in (8304, 8306):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(f"http://localhost:{port}/index.html", timeout=30000)
        page.wait_for_timeout(2500)
        st = page.evaluate("""() => ({
            wizard: !!document.getElementById('wizard-modal'),
            wp: (() => { const w = document.getElementById('welcome-prompt'); return w ? w.className : 'absent'; })(),
            wizardHTMLLen: (document.getElementById('wizard-modal') || {innerHTML:''}).innerHTML.length,
            escHandlerCount: undefined,
        })""")
        print(f'port {port}:', st)
        # press Escape and watch what closes/opens
        page.keyboard.press('Escape'); page.wait_for_timeout(400)
        st2 = page.evaluate("""() => ({
            wp: (() => { const w = document.getElementById('welcome-prompt'); return w ? w.className : 'absent'; })(),
            wizard: (() => { const w = document.getElementById('wizard-modal'); return w ? w.className : 'absent'; })(),
            active: document.activeElement ? (document.activeElement.id || document.activeElement.tagName) : null,
        })""")
        print(f'port {port} after Esc:', st2)
        browser.close()
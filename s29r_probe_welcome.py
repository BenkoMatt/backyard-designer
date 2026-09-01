#!/usr/bin/env python3
"""Find how the welcome-prompt is dismissed (real click path)."""
from playwright.sync_api import sync_playwright

URL = "http://localhost:8220/index.html"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1280, "height": 800})
    pg.goto(URL, wait_until="networkidle", timeout=30000)
    pg.wait_for_timeout(1500)
    pg.evaluate("() => { try{localStorage.removeItem('backyard-recovery-snapshot');}catch(e){} }")
    pg.reload(wait_until="networkidle"); pg.wait_for_timeout(1500)
    skip = pg.locator("#wizard-skip")
    if skip.count() > 0:
        skip.click(); pg.wait_for_timeout(900)
    info = pg.evaluate("""() => {
      const wp = document.getElementById('welcome-prompt');
      if (!wp) return {present: false};
      const btns = [...wp.querySelectorAll('button, .wp-btn, [role=button]')].map(b => ({
        id: b.id, cls: (b.className||'').toString().slice(0,40), text: b.textContent.trim().slice(0,40)}));
      return {present: true, visible: wp.classList.contains('visible'), btns};
    }""")
    print(info)
    # try each dismissal
    for sel in ["#wp-start", "#wp-dismiss", ".wp-start", ".wp-close", "button"]:
        loc = pg.locator(f"#welcome-prompt {sel}") if sel != "button" else pg.locator("#welcome-prompt button")
        if loc.count() == 0:
            print("no match:", sel); continue
        try:
            loc.first.click(timeout=3000)
            pg.wait_for_timeout(700)
            still = pg.evaluate("() => document.getElementById('welcome-prompt')?.classList.contains('visible')")
            print(f"clicked {sel} -> welcome still visible: {still}")
            if not still:
                break
        except Exception as e:
            print("fail", sel, str(e)[:100])
    b.close()
print("DONE")
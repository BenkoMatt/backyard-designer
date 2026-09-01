#!/usr/bin/env python3
"""Probe why #bottom-left-toolbar is only 220px wide."""
from playwright.sync_api import sync_playwright

URL = "http://localhost:8095/index.html"
INIT_STORAGE = """
  try {
    localStorage.setItem('backyard-onboarding-state', JSON.stringify({
        completedSteps: ['welcome-scratch'], tourCompleted: true,
        welcomeShown: true, dismissedAt: 1, featuresUsed: {}}));
    localStorage.removeItem('backyard-design-autosave');
  } catch(e) {}
"""

PROBE = """() => {
    const tb = document.getElementById('bottom-left-toolbar');
    const cs = getComputedStyle(tb);
    const vp = document.getElementById('viewport');
    return {
        parent: tb.parentElement ? (tb.parentElement.id || tb.parentElement.className) : null,
        offsetParent: tb.offsetParent ? (tb.offsetParent.id || tb.offsetParent.className) : null,
        inlineStyle: tb.getAttribute('style'),
        maxWidth: cs.maxWidth, width: cs.width, left: cs.left, bottom: cs.bottom,
        vpRect: vp ? vp.getBoundingClientRect().width : null,
        tbRect: (()=>{const r=tb.getBoundingClientRect();return [r.left,r.top,r.width,r.height];})(),
        btnCount: tb.querySelectorAll('button').length,
        cls: tb.className
    };
}"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = ctx.new_page()
    page.add_init_script(INIT_STORAGE)
    page.goto(URL, wait_until='load', timeout=30000)
    page.wait_for_timeout(2500)
    page.evaluate("() => { const w=document.getElementById('wizard'); if(w) w.style.display='none'; const wp=document.getElementById('welcome-prompt'); if(wp) wp.style.display='none'; }")
    page.wait_for_timeout(300)
    import json
    print(json.dumps(page.evaluate(PROBE), indent=1))
    page.click('.lib-item')
    page.wait_for_timeout(600)
    print(json.dumps(page.evaluate(PROBE), indent=1))
    browser.close()
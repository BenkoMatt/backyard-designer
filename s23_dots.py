#!/usr/bin/env python3
"""Identify the '...' fragment at top of the object library sidebar."""
import os
from playwright.sync_api import sync_playwright
URL = os.environ.get("BASE_URL", "http://localhost:8095/index.html")
INIT = """
  try {
    localStorage.setItem('backyard-onboarding-state', JSON.stringify({
        completedSteps: ['welcome-scratch'], tourCompleted: true,
        welcomeShown: true, dismissedAt: 1, featuresUsed: {}}));
    localStorage.removeItem('backyard-design-autosave');
  } catch(e) {}
"""
PROBE = """() => {
    const els = document.elementsFromPoint(85, 60);
    const stack = els.map(e => {
        const r = e.getBoundingClientRect();
        return (e.id ? '#'+e.id : e.className.toString().split(' ')[0] || e.tagName)
            + ' t=' + Math.round(r.top) + ' h=' + Math.round(r.height);
    }).slice(0, 6);
    // sidebar children near the top
    const sb = document.getElementById('sidebar');
    const kids = [...sb.children].slice(0, 5).map(k => {
        const r = k.getBoundingClientRect();
        return (k.id ? '#'+k.id : k.className.toString().split(' ')[0] || k.tagName)
            + ' "' + k.textContent.trim().slice(0,20) + '" t=' + Math.round(r.top);
    });
    return {stack, kids, sbScrollTop: Math.round(sb.scrollTop)};
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={'width': 1280, 'height': 800}).new_page()
    pg.add_init_script(INIT)
    pg.goto(URL, wait_until='load', timeout=30000)
    pg.wait_for_timeout(2200)
    pg.evaluate("() => { const w=document.getElementById('wizard'); if (w) w.style.display='none';"
                " const wp=document.getElementById('welcome-prompt'); if (wp) wp.style.display='none'; }")
    import json
    print(json.dumps(pg.evaluate(PROBE), indent=1))
    b.close()
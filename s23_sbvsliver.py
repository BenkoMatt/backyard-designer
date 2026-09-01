#!/usr/bin/env python3
"""Check sidebar top sliver: who renders at (87,50) in advanced mode?"""
import os, json
from playwright.sync_api import sync_playwright
URL = os.environ.get("BASE_URL", "http://localhost:8095/index.html")
INIT = """
  try {
    localStorage.setItem('backyard-onboarding-state', JSON.stringify({
        completedSteps: ['welcome-scratch'], tourCompleted: true,
        welcomeShown: true, dismissedAt: 1, featuresUsed: {}}));
    localStorage.setItem('byd-design-mode', 'advanced');
    localStorage.removeItem('backyard-design-autosave');
  } catch(e) {}
"""
PROBE = """() => {
    const els = document.elementsFromPoint(87, 50);
    return els.map(e => {
        const r = e.getBoundingClientRect();
        return (e.id ? '#'+e.id : (e.className.toString().split(' ')[0] || e.tagName))
            + ' [' + Math.round(r.left) + ',' + Math.round(r.top) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height) + ']'
            + ' "' + (e.textContent || '').trim().slice(0, 16) + '"';
    }).slice(0, 6);
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={'width': 1280, 'height': 800}).new_page()
    pg.add_init_script(INIT)
    pg.goto(URL, wait_until='load', timeout=30000)
    pg.wait_for_timeout(2500)
    pg.evaluate("() => { const w=document.getElementById('wizard'); if (w) w.style.display='none';"
                " const wp=document.getElementById('welcome-prompt'); if (wp) wp.style.display='none'; }")
    print(json.dumps(pg.evaluate(PROBE), indent=1))
    b.close()
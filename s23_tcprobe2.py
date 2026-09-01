#!/usr/bin/env python3
"""Measure terrain-controls header geometry after panel is really open."""
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
    const tc = document.getElementById('terrain-controls');
    if (!tc) return {error: 'no #terrain-controls'};
    const vis = tc.classList.contains('visible');
    const title = tc.querySelector('.title');
    const btns = [...tc.querySelectorAll('[data-terrain-minimize], .minimize')];
    return {vis, btnCount: btns.length,
            titleFound: !!title,
            tcH: Math.round(tc.getBoundingClientRect().height)};
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={'width': 1280, 'height': 800}).new_page()
    pg.add_init_script(INIT)
    pg.goto(URL, wait_until='load', timeout=30000)
    pg.wait_for_timeout(2200)
    pg.evaluate("() => { const w=document.getElementById('wizard'); if (w) w.style.display='none';"
                " const wp=document.getElementById('welcome-prompt'); if (wp) wp.style.display='none'; }")
    pg.click('#terrain-btn')
    pg.wait_for_timeout(700)
    print(pg.evaluate(PROBE))
    b.close()
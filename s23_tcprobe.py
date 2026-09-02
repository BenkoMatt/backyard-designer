#!/usr/bin/env python3
"""Measure the terrain-controls minimize button + title geometry precisely."""
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
    document.querySelector('#terrain-btn').click();
    const tc = document.getElementById('terrain-controls');
    if (!tc || !tc.classList.contains('visible')) return {error: 'panel not visible'};
    const title = tc.querySelector('.title');
    const btns = [...tc.querySelectorAll('[data-terrain-minimize], .minimize')];
    const tr = title.getBoundingClientRect();
    const out = {titleRight: Math.round(tr.right), titleTop: Math.round(tr.top),
                 titleBottom: Math.round(tr.bottom)};
    out.btns = btns.map(b => { const r = b.getBoundingClientRect();
        return {txt: b.textContent.trim(), l: Math.round(r.left), t: Math.round(r.top),
                r2: Math.round(r.right), b2: Math.round(r.bottom)}; });
    const el = document.elementFromPoint(557, (out.btns[0]?.t ?? tr.top) + 8);
    out.atXY = el ? (el.tagName + '.' + el.className.toString().split(' ')[0]) : null;
    return out;
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={'width': 1280, 'height': 800}).new_page()
    pg.add_init_script(INIT)
    pg.goto(URL, wait_until='load', timeout=30000)
    pg.wait_for_timeout(2200)
    pg.evaluate("() => { const w=document.getElementById('wizard'); if (w) w.style.display='none';"
                " const wp=document.getElementById('welcome-prompt'); if (wp) wp.style.display='none'; }")
    print(pg.evaluate(PROBE))
    b.close()
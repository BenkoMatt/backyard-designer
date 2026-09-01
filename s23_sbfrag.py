#!/usr/bin/env python3
"""What element renders the fragment at (85,45) when sidebar is scroll-bottomed?"""
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
    const sb = document.getElementById('sidebar');
    sb.scrollTop = sb.scrollHeight;
    document.querySelectorAll('.cat-section.collapsed .cat-title').forEach(t => t.click());
    const els = document.elementsFromPoint(85, 45).map(e =>
        (e.id ? '#'+e.id : e.className.toString().split(' ')[0] || e.tagName));
    // main sidebar container top edge in viewport
    const r = sb.getBoundingClientRect();
    return {stack: els.slice(0, 5), sbTop: Math.round(r.top), sbScrollTop: Math.round(sb.scrollTop)};
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
    pg.evaluate("() => { const sb = document.getElementById('sidebar'); sb.scrollTop = sb.scrollHeight; }")
    pg.wait_for_timeout(600)
    print(pg.evaluate(PROBE))
    b.close()
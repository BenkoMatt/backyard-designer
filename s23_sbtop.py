#!/usr/bin/env python3
"""Inspect the sidebar top area at scroll-bottom (what the vision shot shows)."""
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
    const titles = [...sb.querySelectorAll('.cat-title')];
    const first = titles[0];
    const r = first.getBoundingClientRect();
    const out = {firstTitle: first.textContent.trim().slice(0, 30),
                 firstTop: Math.round(r.top), firstBottom: Math.round(r.bottom)};
    // anything ABOVE the first cat-title inside the sidebar (clipped fragment?)
    const header = sb.querySelector('.sidebar-header');
    if (header) { const hr = header.getBoundingClientRect();
        out.headerText = header.textContent.trim().slice(0,30);
        out.headerTop = Math.round(hr.top); out.headerBottom = Math.round(hr.bottom); }
    // what is at y=45 x=85? elementFromPoint
    const el = document.elementFromPoint(85, 45);
    out.atXY = el ? (el.className.toString().slice(0,40) + ' <' + el.tagName + '>') : null;
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
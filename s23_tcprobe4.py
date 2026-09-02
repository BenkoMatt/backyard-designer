#!/usr/bin/env python3
"""Measure header layout inside #dock-terrain-content (the real visible panel)."""
import os, json
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
    const header = document.querySelector('#dock-terrain-content .terrain-controls-header');
    const title = header.querySelector('.title');
    const btn = header.querySelector('[data-terrain-minimize], .minimize');
    const tr = title.getBoundingClientRect(), br = btn.getBoundingClientRect();
    const hr = header.getBoundingClientRect();
    return {headerL: Math.round(hr.left), headerR: Math.round(hr.right),
            titleR: Math.round(tr.right), btnL: Math.round(br.left), btnR: Math.round(br.right),
            btnT: Math.round(br.top), btnB: Math.round(br.bottom),
            gap: Math.round(br.left - tr.right), btnOverlapsTitle: br.left < tr.right,
            headerCS: getComputedStyle(header).display + ' / ' + getComputedStyle(header).justifyContent};
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
    print(json.dumps(pg.evaluate(PROBE), indent=1))
    b.close()
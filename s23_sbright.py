#!/usr/bin/env python3
"""Empty status-bar segments at far right? Inspect status-bar children."""
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
    const sb = document.getElementById('status-bar');
    const kids = [...sb.children].map(k => {
        const r = k.getBoundingClientRect();
        return (k.id ? '#'+k.id : k.className.split(' ')[0]) + ' "' + k.textContent.trim().slice(0,18) + '"'
            + ' w=' + Math.round(r.width);
    });
    // rightmost 220px: any elements?
    const sr = sb.getBoundingClientRect();
    const rightZone = [...sb.querySelectorAll('*')].filter(e => {
        const r = e.getBoundingClientRect();
        return r.right > sr.right - 220;
    }).map(e => (e.id ? '#'+e.id : e.className.split(' ')[0]) + '"' + e.textContent.trim().slice(0,12) + '"');
    return {kids, rightZone: rightZone.slice(0, 8), sbRight: Math.round(sr.right)};
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
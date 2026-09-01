#!/usr/bin/env python3
"""Sidebar top sliver at ~y52-64 (below topbar bottom edge 52)."""
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
    const sb = document.getElementById('sidebar');
    const r = sb.getBoundingClientRect();
    // first child positions
    const kids = [...sb.children].slice(0, 5).map(k => {
        const kr = k.getBoundingClientRect();
        return (k.id ? '#' + k.id : k.className.toString().split(' ')[0] || k.tagName)
            + ' t=' + Math.round(kr.top) + ' h=' + Math.round(kr.height)
            + ' "' + k.textContent.trim().slice(0, 14) + '"';
    });
    // sample points y=53..66 at x=87
    const smp = [];
    for (let y = 52; y <= 66; y += 2) {
        const e = document.elementFromPoint(87, y);
        smp.push(y + ':' + (e ? (e.id ? '#'+e.id : e.className.toString().split(' ')[0] || e.tagName) : 'null'));
    }
    return {sbTop: Math.round(r.top), kids, smp};
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
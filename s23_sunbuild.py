#!/usr/bin/env python3
"""Geometry: Sun toolbar button row (orphan row?) + BUILD group contents."""
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
    const sun = document.getElementById('sun-btn');
    const tb = document.getElementById('bottom-left-toolbar');
    const btns = [...tb.querySelectorAll('button')].map(b => {
        const r = b.getBoundingClientRect();
        return {id: b.id || b.className.split(' ')[0], t: Math.round(r.top), l: Math.round(r.left)};
    });
    const sr = sun.getBoundingClientRect();
    // BUILD group in the floating sculpt rail
    const groups = [...document.querySelectorAll('.sc-group, [class*=sculpt-group], .dock-group')].map(g => {
        const r = g.getBoundingClientRect();
        return {cls: g.className.toString().slice(0,30), txt: g.textContent.trim().slice(0,26),
                t: Math.round(r.top), h: Math.round(r.height), visible: r.height > 0};
    });
    return {toolbarRows: [...new Set(btns.map(b => b.t))], sunTop: Math.round(sr.top),
            sunLeft: Math.round(sr.left), toolbarMaxWidth: getComputedStyle(tb).maxWidth,
            groups: groups.slice(0, 8)};
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={'width': 1280, 'height': 800}).new_page()
    pg.add_init_script(INIT)
    pg.goto(URL, wait_until='load', timeout=30000)
    pg.wait_for_timeout(2200)
    pg.evaluate("() => { const w=document.getElementById('wizard'); if (w) w.style.display='none';"
                " const wp=document.getElementById('welcome-prompt'); if (wp) wp.style.display='none'; }")
    print(json.dumps(pg.evaluate(PROBE), indent=1)[:2200])
    b.close()
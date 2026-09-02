#!/usr/bin/env python3
"""Verify the toast-over-dim-readout case (vision finding on agent3-after-toast)."""
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
GEOM = """() => {
    const ids = ['toast', 'dim-readout'];
    const out = {};
    for (const id of ids) {
        const el = document.getElementById(id);
        if (!el) { out[id] = null; continue; }
        const cs = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        const vis = cs.display !== 'none' && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.05;
        out[id] = (vis && r.width > 0) ? {l: r.left, t: r.top, r2: r.right, b: r.bottom} : null;
    }
    return out;
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={'width': 1280, 'height': 800}).new_page()
    pg.add_init_script(INIT)
    pg.goto(URL, wait_until='load', timeout=30000)
    pg.wait_for_timeout(2500)
    pg.evaluate("() => { const w = document.getElementById('wizard'); if (w) w.style.display='none';"
                " const wp = document.getElementById('welcome-prompt'); if (wp) wp.style.display='none'; }")
    pg.click('.lib-item')
    try:
        pg.wait_for_function("document.getElementById('toast').classList.contains('visible')", timeout=4000)
    except Exception:
        pass
    pg.wait_for_timeout(400)
    g = pg.evaluate(GEOM)
    print(g)
    t, d = g.get('toast'), g.get('dim-readout')
    if t and d:
        ov = not (t['r2'] <= d['l'] or t['l'] >= d['r2'] or t['b'] <= d['t'] or t['t'] >= d['b'])
        print('OVERLAP toast/dim-readout:', ov)
    else:
        print('no overlap geometry (one or both hidden)')
    b.close()
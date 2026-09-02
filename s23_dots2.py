#!/usr/bin/env python3
"""Find the visual '...' fragment: probe recent-title row innerHTML + geometry."""
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
    // sample a vertical strip of the sidebar at x=85, find any element whose
    // visible text is only dots
    const sb = document.getElementById('sidebar');
    const found = [];
    for (let y = 52; y < 210; y += 4) {
        const els = document.elementsFromPoint(85, y);
        for (const e of els) {
            if (e.children.length === 0 && e.textContent.trim().match(/^[.·•…\\u2026]+$/)) {
                const r = e.getBoundingClientRect();
                found.push({tag: e.tagName, cls: e.className.toString().slice(0,25),
                            txt: JSON.stringify(e.textContent.trim().slice(0,8)),
                            t: Math.round(r.top), h: Math.round(r.height)});
            }
        }
        if (found.length > 2) break;
    }
    // gs hint close button overlap?
    const gsc = document.getElementById('getting-started-close');
    const gr = gsc ? gsc.getBoundingClientRect() : null;
    const gs = document.getElementById('getting-started-hint');
    const g = gs.getBoundingClientRect();
    return {dots: found, gsClose: gr ? {t: Math.round(gr.top), b: Math.round(gr.bottom),
            r2: Math.round(gr.right)} : null, gsHint: {t: Math.round(g.top), b: Math.round(g.bottom)}};
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={'width': 1280, 'height': 800}).new_page()
    pg.add_init_script(INIT)
    pg.goto(URL, wait_until='load', timeout=30000)
    pg.wait_for_timeout(2200)
    pg.evaluate("() => { const w=document.getElementById('wizard'); if (w) w.style.display='none';"
                " const wp=document.getElementById('welcome-prompt'); if (wp) wp.style.display='none'; }")
    print(json.dumps(pg.evaluate(PROBE), indent=1))
    b.close()
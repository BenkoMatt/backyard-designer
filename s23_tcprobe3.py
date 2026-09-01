#!/usr/bin/env python3
"""What does #terrain-btn actually open in basic mode? Dump geometry of candidates."""
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
    const cand = ['#terrain-controls', '#dock-terrain', '#dock-terrain-content',
                  '.dock-panel-body', '#terrain-height-legend'];
    const out = {};
    for (const sel of cand(cand => cand)) {}
    function cand(f){return null}
    return out;
}"""
PROBE2 = """() => {
    const sels = ['#terrain-controls', '#dock-terrain', '#dock-terrain-content', '#dock-underground'];
    const out = {};
    for (const s of sels) {
        const el = document.querySelector(s);
        if (!el) { out[s] = null; continue; }
        const cs = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        out[s] = {cls: el.className.toString().slice(0, 50),
                  vis: el.classList.contains('visible'), disp: cs.display,
                  h: Math.round(r.height), top: Math.round(r.top)};
    }
    // any element containing the text 'Terrain Controls'
    const all = [...document.querySelectorAll('div,span,h2,h3,h4')].filter(e =>
        e.textContent.trim().startsWith('Terrain Controls') && e.children.length <= 2);
    out.titles = all.map(e => { const r = e.getBoundingClientRect();
        return {cls: e.className.toString().slice(0,30), l: Math.round(r.left),
                t: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height),
                html: e.outerHTML.slice(0, 140)}; }).slice(0, 3);
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
    pg.click('#terrain-btn')
    pg.wait_for_timeout(700)
    d = pg.evaluate(PROBE2)
    print(json.dumps(d, indent=1)[:1800])
    b.close()
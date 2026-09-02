#!/usr/bin/env python3
"""Reproduce the two remaining vision-flagged overlaps (tooltip burying)."""
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
GEOM = """() => {
    const pick = sel => {
        const el = document.querySelector(sel);
        if (!el) return null;
        const cs = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        if (cs.display === 'none' || parseFloat(cs.opacity) < 0.05) return null;
        return {l: Math.round(r.left), t: Math.round(r.top), r2: Math.round(r.right), b: Math.round(r.bottom), z: cs.zIndex};
    };
    return {
        hint: pick('#context-hint'),
        excavate_panel: pick('#excavate-panel'),
        dock_underground: pick('#dock-underground'),
        help_panel: pick('.help-panel'),
        help_scroll: (() => { const p = document.querySelector('.help-panel'); if (!p) return null;
            return {sh: p.scrollHeight, ch: p.clientHeight, st: p.scrollTop}; })(),
        tip: pick('.hint-tooltip, #hint-tooltip'),
    };
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={'width': 1280, 'height': 800}).new_page()
    pg.add_init_script(INIT)
    pg.goto(URL, wait_until='load', timeout=30000)
    pg.wait_for_timeout(2500)
    pg.evaluate("() => { const w=document.getElementById('wizard'); if (w) w.style.display='none';"
                " const wp=document.getElementById('welcome-prompt'); if (wp) wp.style.display='none'; }")

    # Case A: excavate (underground) -> hint vs excavate panel / dock
    pg.click('#excavate-btn', force=True)
    pg.wait_for_timeout(900)
    gA = pg.evaluate(GEOM)
    print('UNDERGROUND-ADVANCED:', json.dumps(gA))
    pg.screenshot(path='reports/sprint23_shots/agent3-after-underground-hint.png')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)

    # Case B: basic mode terrain panel -> tooltip vs panel
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    pg.click('#terrain-btn'); pg.wait_for_timeout(600)
    gB = pg.evaluate(GEOM)
    print('BASIC-TERRAIN:', json.dumps(gB))
    pg.screenshot(path='reports/sprint23_shots/agent3-after-terrain-hint.png')
    b.close()
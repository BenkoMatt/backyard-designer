#!/usr/bin/env python3
"""Live geometry repro for Sprint 23 toast/overlay hygiene (Agent 3)."""
import json, sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:8095/index.html"

INIT_STORAGE = """
  try {
    localStorage.setItem('backyard-onboarding-state', JSON.stringify({
        completedSteps: ['welcome-scratch'], tourCompleted: true,
        welcomeShown: true, dismissedAt: 1, featuresUsed: {}}));
    localStorage.removeItem('backyard-design-autosave');
  } catch(e) {}
"""

DISMISS_WIZARD = """() => {
    const w = document.getElementById('wizard');
    if (w) w.style.display = 'none';
    const wp = document.getElementById('welcome-prompt');
    if (wp) wp.style.display = 'none';
}"""

PROBE = """() => {
    const r = el => { const e = document.getElementById(el); if (!e) return null;
        const b = e.getBoundingClientRect();
        return {left: Math.round(b.left), top: Math.round(b.top), right: Math.round(b.right), bottom: Math.round(b.bottom)}; };
    const tb = document.getElementById('bottom-left-toolbar');
    const btns = tb ? [...tb.querySelectorAll('button')].map(b => {
        const rc = b.getBoundingClientRect();
        return { id: b.id, left: Math.round(rc.left), top: Math.round(rc.top),
                 right: Math.round(rc.right), bottom: Math.round(rc.bottom) };
    }) : [];
    const t = document.getElementById('toast');
    const tr = t ? t.getBoundingClientRect() : null;
    return {
        toast: tr ? {left: Math.round(tr.left), top: Math.round(tr.top), right: Math.round(tr.right), bottom: Math.round(tr.bottom), visible: t.classList.contains('visible')} : null,
        toolbar: r('bottom-left-toolbar'),
        tbBtns: btns,
        hint: r('context-hint'),
        badge: r('grid-level-badge'),
        dg: r('depth-gauge-overlay'),
        atmos: r('atmosphere-banner') || r('atmosphere-badge'),
        rb: r('recovery-banner'),
        vh: window.innerHeight, vw: window.innerWidth
    };
}"""

def overlap(toast, b):
    if not toast or not b: return False
    return not (toast['right'] <= b['left'] or toast['left'] >= b['right'] or
                toast['bottom'] <= b['top'] or toast['top'] >= b['bottom'])

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = ctx.new_page()
    page.add_init_script(INIT_STORAGE)
    page.goto(URL, wait_until='load', timeout=30000)
    page.wait_for_timeout(2500)
    page.evaluate(DISMISS_WIZARD)
    page.wait_for_timeout(300)

    # BEFORE shot
    page.screenshot(path='reports/sprint23_shots/toast-before-1.png')

    # add an item via real click (first lib item) -> toast + toolbar rewrap
    page.click('.lib-item')
    try:
        page.wait_for_function("document.getElementById('toast').classList.contains('visible')", timeout=3000)
    except Exception:
        print("toast never became visible!")
    page.wait_for_timeout(400)
    g = page.evaluate(PROBE)
    print(json.dumps(g, indent=1))
    t = g.get('toast')
    hits = [b['id'] for b in g['tbBtns'] if overlap(t, b)]
    print("TOAST-OVERLAP-BUTTONS:", hits)
    page.screenshot(path='reports/sprint23_shots/toast-before-2.png')

    # hint geometry (context-hint) with toolbar
    print("hint rect:", g.get('hint'), "toolbar:", g.get('toolbar'))
    browser.close()
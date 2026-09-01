#!/usr/bin/env python3
"""Diagnose sidebar item clipping: does the sidebar list actually overflow its padding?"""
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
    const items = [...sb.querySelectorAll('.lib-item')];
    const last = items[items.length - 1];
    const status = document.getElementById('status-bar');
    const lr = last.getBoundingClientRect(), sr = status.getBoundingClientRect();
    // where is the sidebar's bottom edge vs the viewport?
    const sbr = sb.getBoundingClientRect();
    return {lastBottom: Math.round(lr.bottom), statusTop: Math.round(sr.top),
            sidebarBottom: Math.round(sbr.bottom),
            atScrollBottom: sb.scrollTop + sb.clientHeight >= sb.scrollHeight - 2,
            scrollTop: Math.round(sb.scrollTop), scrollHeight: sb.scrollHeight,
            clientH: sb.clientHeight,
            overlap: lr.bottom > sr.top};
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={'width': 1280, 'height': 800}).new_page()
    pg.add_init_script(INIT)
    pg.goto(URL, wait_until='load', timeout=30000)
    pg.wait_for_timeout(2200)
    pg.evaluate("() => { const w=document.getElementById('wizard'); if (w) w.style.display='none';"
                " const wp=document.getElementById('welcome-prompt'); if (wp) wp.style.display='none'; }")
    # NO scrolling — this is what the vision shots show
    r = pg.evaluate(PROBE)
    print('UNSCROLLED:', r)
    pg.screenshot(path='reports/sprint23_shots/agent3-sidebar-unscrolled.png')
    pg.evaluate("() => { const sb = document.getElementById('sidebar'); sb.scrollTop = sb.scrollHeight; }")
    pg.wait_for_timeout(500)
    r2 = pg.evaluate(PROBE)
    print('SCROLLED  :', r2)
    b.close()
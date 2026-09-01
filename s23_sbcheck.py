#!/usr/bin/env python3
"""Probe: at REAL scroll-bottom does the last lib-item clear the status bar?"""
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
    sb.scrollTop = sb.scrollHeight;
    const items = [...sb.querySelectorAll('.lib-item')];
    const last = items[items.length - 1];
    const status = document.getElementById('status-bar');
    const lr = last.getBoundingClientRect(), sr = status.getBoundingClientRect();
    return {scrollBottom: sb.scrollTop + sb.clientHeight >= sb.scrollHeight - 2,
            lastBottom: Math.round(lr.bottom), statusTop: Math.round(sr.top),
            pad: parseFloat(getComputedStyle(sb).paddingBottom),
            overlap: lr.bottom > sr.top};
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for mode in ('basic', 'advanced'):
        pg = b.new_context(viewport={'width': 1280, 'height': 800}).new_page()
        pg.add_init_script(INIT + f"\nlocalStorage.setItem('byd-design-mode','{mode}');")
        pg.goto(URL, wait_until='load', timeout=30000)
        pg.wait_for_timeout(2200)
        pg.evaluate("() => { const w=document.getElementById('wizard'); if (w) w.style.display='none';"
                    " const wp=document.getElementById('welcome-prompt'); if (wp) wp.style.display='none'; }")
        r = pg.evaluate(PROBE)
        print(mode, r)
        pg.context.close()
    b.close()
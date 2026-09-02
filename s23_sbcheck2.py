#!/usr/bin/env python3
"""Replicate the gate's SIDEBAR_SCROLL_BOTTOM exactly (click collapsed titles)."""
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
SCROLL = """() => {
    const sb = document.getElementById('sidebar');
    document.querySelectorAll('.cat-section.collapsed .cat-title').forEach(t => t.click());
    sb.scrollTop = sb.scrollHeight;
}"""
PROBE = """() => {
    const items = [...document.querySelectorAll('.lib-item')];
    const last = items[items.length - 1];
    const sb = document.getElementById('sidebar');
    const r = last.getBoundingClientRect();
    const sTop = document.getElementById('status-bar').getBoundingClientRect().top;
    return {lastBottom: Math.round(r.bottom), statusTop: Math.round(sTop),
            overlap: r.bottom > sTop + 1,
            atScrollBottom: sb.scrollTop + sb.clientHeight >= sb.scrollHeight - 4};
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
        pg.evaluate(SCROLL)
        pg.wait_for_timeout(700)
        r = pg.evaluate(PROBE)
        print(mode, r)
        pg.context.close()
    b.close()
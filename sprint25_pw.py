#!/usr/bin/env python3
"""Sprint 25 helper: Playwright driver with real CDP input helpers (no app-function calls for UI paths)."""
from playwright.sync_api import sync_playwright

URL = "http://localhost:8323/index.html"


def launch(width=1280, height=800):
    p = sync_playwright().start()
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": width, "height": height})
    page = ctx.new_page()
    page.goto(URL)
    page.wait_for_timeout(2600)
    return p, browser, ctx, page


def dismiss_wizard(page):
    """Dismiss first-run wizard via real clicks if present."""
    page.wait_for_timeout(400)
    for sel in ('#wizard-next', '#wizard-skip', '#welcome-prompt button'):
        el = page.query_selector(sel)
        if el and el.is_visible():
            el.click()
            page.wait_for_timeout(500)


def shot(page, path):
    page.screenshot(path=path)
    print(f"saved {path}")


def geometry(page):
    """DOM geometry: off-viewport / overflowing visible elements (floating panels & controls)."""
    return page.evaluate("""() => {
      const vw = innerWidth, vh = innerHeight;
      const out = [];
      const sels = '.panel,.dock,.modal,#topbar,#bottom-left-toolbar,#status-bar,#props-panel,.tb-group,' +
        '#terrain-controls,#layers-panel,#sun-panel,#cost-panel,#season-panel,#growth-panel,#permit-panel,' +
        '#cmd-palette,#ctx-menu,#batch-bar,#sculpt-restore-pill,#context-hint,#walk-hint,#grid-level-badge,' +
        '#atmosphere-badge,#progressive-hint,#buried-objects-panel,#cross-section-panel,#terrain-analysis-panel,' +
        '#innovation-panel,#excavate-panel,.s21-collapse-btn';
      document.querySelectorAll(sels).forEach(el => {
        if (!(el instanceof HTMLElement)) return;
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return;
        const r = el.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) return;
        const clipped = (r.left < -1 || r.top < -1 || r.right > vw + 1 || r.bottom > vh + 1);
        out.push({sel: el.id ? '#'+el.id : '.'+String(el.className).split(' ')[0],
                  x: Math.round(r.left), y: Math.round(r.top),
                  w: Math.round(r.width), h: Math.round(r.height),
                  clipped, hscroll: el.scrollWidth > el.clientWidth + 1,
                  vscroll: el.scrollHeight > el.clientHeight + 1});
      });
      return {vw, vh, docHScroll: document.documentElement.scrollWidth > vw,
              els: out};
    }""")
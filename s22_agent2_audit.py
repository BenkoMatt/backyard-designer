#!/usr/bin/env python3
"""Sprint 22 Agent 2 — DOM audit of icon-only buttons, tooltips, cursor, empty state, wizard text.

Read-only probes (page.evaluate only for reads/attribute listing) over live CDP.
"""
import json
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8425/index.html"

INIT_STORAGE = """
  try {
    localStorage.setItem('backyard-onboarding-state', JSON.stringify({
        completedSteps: ['welcome-scratch'], tourCompleted: true,
        welcomeShown: true, dismissedAt: 1, featuresUsed: {}
    }));
    localStorage.setItem('byd-design-mode', 'basic');
    localStorage.removeItem('backyard-design-autosave');
  } catch(e) {}
"""

AUDIT_JS = """() => {
  const out = {iconOnlyMissingTitle: [], iconOnlyHasTitle: [], buttonsNoFocusStyle: [],
               canvas: null, bodyCursor: null, dockHeaderBtns: null, wizard: null,
               welcomePrompt: null, emptyStateEls: null, vcTitles: null};

  const isIconOnly = (el) => {
    const t = (el.textContent || '').trim();
    // text lives in a nested label span (dock tabs have visible labels) -> not icon-only
    if (el.querySelector('.td-label, .wp-qa-text, .label, .dims')) return false;
    return t.length === 0 || t.length <= 2;
  };

  document.querySelectorAll('button').forEach((b) => {
    if (!isIconOnly(b)) return;
    const cs = getComputedStyle(b);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const title = b.getAttribute('title');
    const rec = {
      id: b.id || null, cls: (b.className || '').toString().slice(0, 60),
      label: (b.getAttribute('aria-label') || '').slice(0, 60),
      title: title ? title.slice(0, 90) : null,
      visible: r2(b)
    };
    if (title && title.trim()) out.iconOnlyHasTitle.push(rec);
    else out.iconOnlyMissingTitle.push(rec);
  });
  out.vcTitles = Array.from(document.querySelectorAll('.vc-btn')).map(b => ({
    id: b.id, title: b.getAttribute('title'), aria: b.getAttribute('aria-label')
  }));
  out.dockHeaderBtns = Array.from(document.querySelectorAll('[data-dock-close],[data-dock-minimize]')).slice(0,2).map(b => ({
    cls: b.className, title: b.getAttribute('title'), aria: b.getAttribute('aria-label')
  }));

  function r2(el) { try { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; } catch(e){ return true; } }

  const c = document.querySelector('#viewport canvas');
  out.canvas = c ? getComputedStyle(c).cursor : null;
  out.bodyCursor = getComputedStyle(document.body).cursor;
  out.viewportCursor = (() => { const v = document.getElementById('viewport'); return v ? getComputedStyle(v).cursor : null; })();

  // focus-visible coverage: count buttons whose computed outline-width would be 0 on focus-visible
  // (approximation: stylesheet coverage via matchMedia-free probe on a temp button)
  const probe = document.createElement('button');
  probe.id = '__s22_focus_probe';
  probe.style.cssText = 'position:fixed;left:-9999px;top:0;';
  document.body.appendChild(probe);
  probe.focus();
  out.probeFocusVisible = (() => { try {
      const cs = getComputedStyle(probe);
      return {ow: cs.outlineWidth, os: cs.outlineStyle, oc: cs.outlineColor};
  } finally { probe.remove(); } })();

  out.wizard = {panelHTML: document.getElementById('wizard-panel').innerHTML.slice(0, 200),
                display: getComputedStyle(document.getElementById('wizard')).display};

  const wp = document.getElementById('welcome-prompt');
  out.welcomePrompt = {exists: !!wp, visible: wp.classList.contains('visible'),
                       title: (document.getElementById('wp-title')||{}).textContent || null};

  out.emptyStateEls = {
    progressiveHint: !!document.getElementById('progressive-hint'),
    progressiveHintText: (document.getElementById('progressive-hint')||{}).textContent || null,
    emptyState: !!document.getElementById('empty-state'),
    statusText: (document.getElementById('status-bar')||{}).textContent || null,
    statusBarText: (document.querySelector('#status-bar')||{}).textContent || null
  };
  return out;
}"""

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(BASE, wait_until="domcontentloaded")
        page.evaluate(INIT_STORAGE)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("() => !!(window._test && window._test.yardMesh)", timeout=30000)
        page.wait_for_timeout(800)
        res = page.evaluate(AUDIT_JS)
        browser.close()
    print(json.dumps(res, indent=1))

if __name__ == "__main__":
    run()
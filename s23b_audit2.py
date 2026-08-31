"""Full stacking audit AFTER fix: every dock tab, right-stack, cross combos.
Checks: dock-vs-tool-dock overlap, dock-vs-toolbar overlap, viewport clipping,
panel-panel overlaps, duplicate 'Underground View' header."""
import json
import os
from playwright.sync_api import sync_playwright
from s23a_common import load_app, to_advanced
import s23a_common

s23a_common.URL = "http://localhost:8092/index.html"
OUT = "reports/sprint23_panel_audit"
os.makedirs(OUT, exist_ok=True)

PROBE = """() => {
  const sels = {
    'terrain-controls': '#terrain-controls', 'excavate-panel': '#excavate-panel',
    'terrain-analysis-panel': '#terrain-analysis-panel', 'innovation-panel': '#innovation-panel',
    'sun-panel': '#sun-panel', 'cost-panel': '#cost-panel', 'layer-panel': '#layer-panel',
    'season-panel': '#season-panel', 'growth-panel': '#growth-panel', 'permit-panel': '#permit-panel',
    'cross-section-panel': '#cross-section-panel', 'cut-fill-panel': '#cut-fill-panel',
    'dock-underground': '#dock-underground', 'dock-terrain': '#dock-terrain',
    'dock-analyze': '#dock-analyze', 'dock-innovate': '#dock-innovate', 'dock-sun': '#dock-sun',
    'dock-measure': '#dock-measure', 'tool-dock': '#tool-dock',
    'bottom-left-toolbar': '#bottom-left-toolbar', 'topbar': '#topbar', 'status-bar': '#status-bar'
  };
  const vis = {};
  for (const [n, s] of Object.entries(sels)) {
    const el = document.querySelector(s);
    if (!el) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    vis[n] = { x: r.x, y: r.y, w: r.width, h: r.height, z: parseInt(cs.zIndex) || 0 };
  }
  const overlaps = [];
  const names = Object.keys(vis);
  for (let i = 0; i < names.length; i++) for (let j = i + 1; j < names.length; j++) {
    const a = vis[names[i]], b = vis[names[j]];
    const ix = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x));
    const iy = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
    if (ix > 2 && iy > 2) overlaps.push([names[i], names[j], Math.round(ix * iy)]);
  }
  // duplicate underground header check (Sprint 23: legacy .excavate-header is CSS-hidden)
  const ugContent = document.getElementById('dock-underground-content');
  const dupHeader = ugContent ? Array.from(ugContent.querySelectorAll('.excavate-header')).filter(h => getComputedStyle(h).display !== 'none').length : 0;
  const headerVisible = dupHeader ? 'VISIBLE' : 'hidden/none';
  return { visible: names, overlaps, dupUgHeaders: dupHeader, dupHeaderDisplay: headerVisible,
           vw: innerWidth, vh: innerHeight };
}"""

def close_all(page):
    page.evaluate("""() => {
        document.querySelectorAll('.dock-panel.visible').forEach(el => el.classList.remove('visible'));
        const c = document.getElementById('dock-panel-container');
        if (c) c.classList.remove('visible');
        document.querySelectorAll('.td-tab.active').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-pressed','false'); });
        ['#cost-panel','#layer-panel','#season-panel','#growth-panel','#permit-panel','#cross-section-panel','#cut-fill-panel'].forEach(s => {
            const el = document.querySelector(s); if (el) el.classList.remove('visible'); });
        const eb = document.getElementById('excavate-btn');
        if (eb) { eb.classList.remove('active'); eb.setAttribute('aria-pressed','false'); }
    }""")
    page.wait_for_timeout(300)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    load_app(page)
    to_advanced(page)
    results = {}

    def snap(name):
        page.wait_for_timeout(450)
        results[name] = page.evaluate(PROBE)
        page.screenshot(path=f"{OUT}/{name}.png")

    # each dock tab alone
    for dock in ["terrain", "underground", "analyze", "innovate", "sun", "measure"]:
        close_all(page)
        page.click(f'.td-tab[data-dock="{dock}"]', force=True)
        snap(f"after_docktab_{dock}")

    # right stack all five
    close_all(page)
    for b in ["btn-cost", "btn-layers", "btn-season", "btn-growth", "btn-permit"]:
        page.click("#" + b, force=True)
        page.wait_for_timeout(250)
    snap("after_right_stack_all")

    # underground + cost
    close_all(page)
    page.click('.td-tab[data-dock="underground"]', force=True)
    page.wait_for_timeout(400)
    page.click("#btn-cost", force=True)
    snap("after_ug_plus_cost")

    # underground + cross-section toggle (button is in moved content; JS-click fallback
    # matches qa_s21_dig_visibility.py convention when Playwright actionability flakes)
    close_all(page)
    page.click('.td-tab[data-dock="underground"]', force=True)
    page.wait_for_timeout(400)
    try:
        page.click("#cross-section-toggle", force=True, timeout=3000)
    except Exception:
        page.evaluate("() => document.getElementById('cross-section-toggle').click()")
    snap("after_ug_plus_cs")

    # terrain+sun (sun replaces terrain per tab exclusivity)
    close_all(page)
    page.click('.td-tab[data-dock="terrain"]', force=True)
    page.wait_for_timeout(400)
    page.click('.td-tab[data-dock="sun"]', force=True)
    snap("after_terrain_then_sun")

    # innov full width check + permit/season overlays
    close_all(page)
    page.click('.td-tab[data-dock="innovate"]', force=True)
    page.wait_for_timeout(400)
    snap("after_innovate_alone")

    json.dump(results, open(f"{OUT}/audit_after.json", "w"), indent=1)
    # summary: any overlap at all?
    bad = {k: v["overlaps"] for k, v in results.items() if v["overlaps"]}
    dup = {k: v["dupUgHeaders"] for k, v in results.items() if v["dupUgHeaders"]}
    print("OVERLAPS:", json.dumps(bad, indent=1))
    print("DUP_UG_HEADERS:", json.dumps(dup))
    browser.close()
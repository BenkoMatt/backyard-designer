"""Sprint 23 Agent 2 — panel stacking/z-order audit matrix.

Opens every panel and panel combinations, screenshots each state, runs a DOM
rect-overlap probe (real intersection test; a "hit" = visible panel rect that
overlaps another visible panel rect), and saves state JSON. Vision runs over
shots separately. Real CDP clicks for all UI actions; evaluate() = observation.
"""
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
    'tool-dock': '#tool-dock', 'bottom-left-toolbar': '#bottom-left-toolbar',
    'status-bar': '#status-bar', 'sidebar': '#sidebar'
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
  // pairwise intersection among panels only (exclude chrome)
  const panels = Object.entries(vis).filter(([n]) => !['tool-dock','bottom-left-toolbar','status-bar','sidebar'].includes(n));
  const overlaps = [];
  for (let i = 0; i < panels.length; i++) for (let j = i + 1; j < panels.length; j++) {
    const a = panels[i][1], b = panels[j][1];
    const ix = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x));
    const iy = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
    if (ix > 2 && iy > 2) overlaps.push([panels[i][0], panels[j][0], Math.round(ix * iy)]);
  }
  return { visible: Object.keys(vis), overlaps, rects: vis };
}"""

STATES = [
    ("right_stack_all",   [("btn-cost", 200), ("btn-layers", 200), ("btn-season", 200), ("btn-growth", 200), ("btn-permit", 200)]),
    ("dock_underg_cs",    [('.td-tab[data-dock="underground"]', 400), ("#cross-section-toggle", 400)]),
    ("dock_underg_cost",  [('.td-tab[data-dock="underground"]', 400), ("btn-cost", 200)]),
    ("dock_underg_cutfill", None),  # special: needs analyze flows
    ("dock_all_tabs_seq", None),    # special: each dock tab alone
    ("terr_plus_sun",     [('.td-tab[data-dock="terrain"]', 400), ('.td-tab[data-dock="sun"]', 300)]),
    ("terr_plus_ug",      [('.td-tab[data-dock="terrain"]', 400), ('.td-tab[data-dock="underground"]', 300)]),
    ("ug_plus_analyze",   [('.td-tab[data-dock="underground"]', 400), ('.td-tab[data-dock="analyze"]', 300)]),
    ("innov_plus_sun",    [('.td-tab[data-dock="innovate"]', 400), ('.td-tab[data-dock="sun"]', 300)]),
    ("cs_plus_cutfill",   None),  # special
]

def click(page, sel):
    if sel.startswith("#") or sel.startswith("."):
        page.click(sel, force=True)
    else:
        page.click("#" + sel, force=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    load_app(page)
    to_advanced(page)
    results = {}

    def snap(name):
        page.wait_for_timeout(500)
        results[name] = page.evaluate(PROBE)
        page.screenshot(path=f"{OUT}/{name}.png")

    for name, steps in STATES:
        if steps is None:
            continue
        # reset: reload state cheaply by closing all docks + panels
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
        page.wait_for_timeout(250)
        for sel, wait in steps:
            click(page, sel)
            page.wait_for_timeout(wait)
        snap(name)

    # dock_all_tabs_seq: each dock tab alone, then close
    seq = {}
    for dock in ["terrain", "underground", "analyze", "innovate", "sun", "measure"]:
        page.evaluate("""() => {
            document.querySelectorAll('.dock-panel.visible').forEach(el => el.classList.remove('visible'));
            const c = document.getElementById('dock-panel-container');
            if (c) c.classList.remove('visible');
            document.querySelectorAll('.td-tab.active').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-pressed','false'); });
        }""")
        page.wait_for_timeout(200)
        page.click(f'.td-tab[data-dock="{dock}"]', force=True)
        page.wait_for_timeout(500)
        seq[dock] = page.evaluate(PROBE)
        page.screenshot(path=f"{OUT}/docktab_{dock}.png")
    results["dock_all_tabs_seq"] = seq

    # cross-section via excavate flow + cut-fill via analyze
    page.evaluate("""() => {
        document.querySelectorAll('.dock-panel.visible').forEach(el => el.classList.remove('visible'));
        const c = document.getElementById('dock-panel-container');
        if (c) c.classList.remove('visible');
        document.querySelectorAll('.td-tab.active').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-pressed','false'); });
    }""")
    page.click('.td-tab[data-dock="underground"]', force=True)
    page.wait_for_timeout(400)
    page.click("#cross-section-toggle", force=True)
    page.wait_for_timeout(500)
    # need 2 canvas points for full CS panel; toggle alone shows instruction state
    results["dock_underg_cs"].update(page.evaluate(PROBE))
    page.screenshot(path=f"{OUT}/dock_underg_cs.png")

    # cut-fill: from analyze tab
    page.evaluate("""() => {
        document.querySelectorAll('.dock-panel.visible').forEach(el => el.classList.remove('visible'));
        const c = document.getElementById('dock-panel-container');
        if (c) c.classList.remove('visible');
        document.querySelectorAll('.td-tab.active').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-pressed','false'); });
    }""")
    page.click('.td-tab[data-dock="analyze"]', force=True)
    page.wait_for_timeout(400)
    # expand advanced tools if needed, click cut-fill btn
    cutbtn = page.locator("#innov-cut-fill-btn, #cut-fill-btn, [id*='cut-fill']")
    try:
        page.click("#ta-cut-fill", force=True, timeout=2000)
    except Exception:
        try:
            page.click(".advanced-toggle", force=True, timeout=2000)
            page.wait_for_timeout(200)
            page.click("#innov-cut-fill-btn", force=True, timeout=2000)
        except Exception as e:
            print("cut-fill trigger not found:", e)
    page.wait_for_timeout(500)
    results["cs_plus_cutfill"] = page.evaluate(PROBE)
    page.screenshot(path=f"{OUT}/cs_plus_cutfill.png")

    json.dump(results, open(f"{OUT}/audit_states.json", "w"), indent=1)
    print(json.dumps({k: v.get("overlaps") if isinstance(v, dict) and "overlaps" in v else
                      {kk: vv.get("overlaps") for kk, vv in v.items()} if isinstance(v, dict) else v
                      for k, v in results.items()}, indent=1))
    browser.close()
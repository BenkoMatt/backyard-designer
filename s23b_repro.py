"""Sprint 23 Agent 2 — reproduce the double 'Underground View' panel bug.

Opens the Underground dock tab, then clicks the #excavate-btn launcher, then
screenshots + audits DOM geometry (rects, computed display) of both panels.
READ-ONLY on the app: real CDP clicks only; evaluate() for observation.
"""
import json
import os
from playwright.sync_api import sync_playwright
from s23a_common import load_app, to_advanced, record, RESULTS, summary_and_exit

PORT = int(os.environ.get("S23B_PORT", "8092"))
os.environ.setdefault("S23B_URL_OVERRIDE", "1")
import s23a_common
s23a_common.URL = f"http://localhost:{PORT}/index.html"

PROBE = """() => {
  const ids = ['excavate-panel', 'dock-underground', 'dock-panel-container'];
  const out = {};
  for (const id of ids) {
    const el = document.getElementById(id);
    if (!el) { out[id] = null; continue; }
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    out[id] = {
      classes: el.className,
      display: cs.display,
      visibility: cs.visibility,
      rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      childCount: el.children.length,
      text: (el.innerText || '').slice(0, 80),
    };
  }
  return out;
}"""

with sync_playwright() as p:
    browser, page, errors = None, None, []
    from s23a_common import make_page
    browser, page, errors = make_page(p, 1280, 800)
    load_app(page)
    to_advanced(page)

    # Step 1: click the Underground dock tab (real CDP click)
    page.click('.td-tab[data-dock="underground"]')
    page.wait_for_timeout(600)
    print("AFTER dock tab click:", json.dumps(page.evaluate(PROBE), indent=1))
    page.screenshot(path="s23b_before_1_docktab_only.png")

    # Step 2: click the Excavate launcher button too (real CDP click)
    page.click('#excavate-btn')
    page.wait_for_timeout(600)
    print("\nAFTER excavate btn click:", json.dumps(page.evaluate(PROBE), indent=1))
    page.screenshot(path="s23b_before_2_docktab_plus_excavate.png")

    # Also click the excavate panel's own close button if it has children
    shell = page.evaluate("""() => {
      const el = document.getElementById('excavate-panel');
      return el ? {kids: el.children.length, visible: el.classList.contains('visible')} : null;
    }""")
    print("\nexcavate-panel shell state:", json.dumps(shell))

summary_and_exit()
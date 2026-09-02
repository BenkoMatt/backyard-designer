#!/usr/bin/env python3
"""S29 Agent 3 Phase 2: dock panels sweep — terrain + underground (also analyze/innovate/sun
for context), zero-scroll mandate at 1280x800 AND 1600x900.

Each: real CDP click on td-tab, capture, vision verdict, DOM scroll-overflow probe.
Also minimize/close affordances, and dock open+closed states.
"""
import json
import sys

sys.path.insert(0, "/root/byd29-audit-modals")
from playwright.sync_api import sync_playwright
from s29a_common import (capture, is_clean, make_page, overlay_probe,
                         shot_path, vision_qa)

FINDINGS = []


def dock_probe(page):
    """Read-only: for every visible dock panel, measure scroll overflow of the panel body."""
    return page.evaluate("""() => {
    const out = [];
    const docks = ['dock-terrain','dock-underground','dock-analyze','dock-innovate','dock-sun'];
    for (const id of docks) {
      const d = document.getElementById(id);
      if (!d || !d.classList.contains('visible')) continue;
      const body = d.querySelector('.dock-panel-body');
      const dr = d.getBoundingClientRect();
      const rec = {id, x:Math.round(dr.x), y:Math.round(dr.y), w:Math.round(dr.width),
                   h:Math.round(dr.height), bottom: Math.round(dr.bottom)};
      if (body) {
        rec.bodyScrollH = body.scrollHeight;
        rec.bodyClientH = body.clientHeight;
        rec.scrollOverflow = body.scrollHeight - body.clientHeight;
      }
      const dScroll = d.scrollHeight - d.clientHeight;
      rec.panelScrollOverflow = dScroll;
      out.push(rec);
    }
    return out;
}""")


def judge(page, name, label, res_wh):
    path = shot_path(name)
    page.screenshot(path=path)
    verdict = vision_qa(path)
    probe = dock_probe(page)
    sidecar(name, {"surface": name, "label": label, "verdict": verdict,
                   "dock_probe": probe, "res": res_wh})
    tag = "CLEAN" if is_clean(verdict) else "DIRTY"
    print(f"[{tag}] {name} :: {verdict.strip()[:130].replace(chr(10),' | ')}")
    print(f"    probe: {json.dumps(probe)[:260]}")
    FINDINGS.append({"surface": name, "label": label, "verdict": verdict,
                     "probe": probe, "clean": is_clean(verdict), "res": res_wh})


from s29a_common import sidecar


def run_res(p, w, h, tag):
    browser, page, errors = make_page(p, w, h)
    page.goto("http://localhost:8186/index.html", wait_until="networkidle")
    page.wait_for_timeout(1800)
    page.locator("#wizard-skip").click()
    page.wait_for_timeout(1200)
    # welcome prompt appears; dismiss via its own Escape (real key) then wiggle mouse to keep hint away
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    for i in range(4):
        page.mouse.move(400 + i * 40, 300)
        page.wait_for_timeout(250)
    page.locator("#mode-toggle button[data-mode='advanced']").click()
    page.wait_for_timeout(700)

    # ---- terrain dock ----
    page.locator(".td-tab[data-dock='terrain']").click()
    page.wait_for_timeout(900)
    judge(page, f"dock_terrain_open_{tag}", "Terrain dock panel open", (w, h))

    # expand all 3 accordions via real clicks
    accs = page.locator("#dock-terrain-content .tc-acc")
    n = accs.count()
    for i in range(n):
        accs.nth(i).click()
        page.wait_for_timeout(250)
    page.wait_for_timeout(500)
    judge(page, f"dock_terrain_accordions_{tag}", "Terrain dock all accordions expanded", (w, h))

    # minimize affordance
    page.locator("#dock-terrain [data-dock-minimize]").click()
    page.wait_for_timeout(400)
    judge(page, f"dock_terrain_minimized_{tag}", "Terrain dock minimized", (w, h))
    # restore + close
    page.locator("#dock-terrain [data-dock-minimize]").click()
    page.wait_for_timeout(400)
    page.locator("#dock-terrain [data-dock-close]").click()
    page.wait_for_timeout(400)
    judge(page, f"dock_terrain_closed_{tag}", "Terrain dock closed (tabs visible)", (w, h))

    # ---- underground dock ----
    page.locator(".td-tab[data-dock='underground']").click()
    page.wait_for_timeout(900)
    judge(page, f"dock_underground_open_{tag}", "Underground dock panel open", (w, h))
    page.locator("#dock-underground [data-dock-close]").click()
    page.wait_for_timeout(400)

    # ---- analyze / innovate / sun for context (mine: check scroll behavior) ----
    page.locator(".td-tab[data-dock='analyze']").click()
    page.wait_for_timeout(700)
    judge(page, f"dock_analyze_open_{tag}", "Analyze dock panel open", (w, h))
    page.locator("#dock-analyze [data-dock-close]").click()
    page.wait_for_timeout(300)

    page.locator(".td-tab[data-dock='innovate']").click()
    page.wait_for_timeout(700)
    judge(page, f"dock_innovate_open_{tag}", "Pro Tools dock panel open", (w, h))
    # expand advanced tools toggle
    adv = page.locator("#dock-innovate-content .advanced-toggle")
    if adv.count() > 0:
        adv.click()
        page.wait_for_timeout(400)
        judge(page, f"dock_innovate_adv_{tag}", "Pro Tools advanced expanded", (w, h))
    page.locator("#dock-innovate [data-dock-close]").click()
    page.wait_for_timeout(300)

    page.locator(".td-tab[data-dock='sun']").click()
    page.wait_for_timeout(700)
    judge(page, f"dock_sun_open_{tag}", "Sun dock panel open", (w, h))
    page.locator("#dock-sun [data-dock-close]").click()
    page.wait_for_timeout(300)

    print("PAGE_ERRORS:", errors[:3])
    browser.close()


def main():
    with sync_playwright() as p:
        run_res(p, 1280, 800, "1280")
        run_res(p, 1600, 900, "1600")
    with open("/root/byd29-audit-modals/reports/s29_shots/phase2_results.json", "w") as f:
        json.dump(FINDINGS, f, indent=1)
    dirty = [f for f in FINDINGS if not f["clean"]]
    print(f"\n=== Phase 2 done: {len(FINDINGS)} shots, {len(dirty)} dirty ===")
    for d in dirty:
        print("DIRTY:", d["surface"], "::", d["verdict"][:180].replace("\n", " | "))


if __name__ == "__main__":
    main()
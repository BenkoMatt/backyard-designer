"""F4 verification with real clicks: minimize terrain dock panel via its minimize button."""
import json
import sys

sys.path.insert(0, "/root/byd29r-modals")
from r3_common import load_app, make_page, shot_path
from playwright.sync_api import sync_playwright


def rect(page, sel):
    return page.evaluate("(s) => { const e = document.querySelector(s); if (!e) return null;"
                         " const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);"
                         " return {x: r.x, y: r.y, w: r.width, h: r.height,"
                         " display: cs.display, visibility: cs.visibility}; }", sel)


def overlap(a, b):
    if not a or not b:
        return None
    ox = max(0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    oy = max(0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    return {"ox": round(ox), "oy": round(oy)}


with sync_playwright() as p:
    browser, page, errors = make_page(p)
    load_app(page)
    # dismiss welcome prompt if visible (real clicks)
    wp = page.locator("#welcome-prompt")
    if wp.count() > 0 and wp.is_visible():
        scratch = page.locator("#wp-scratch")
        if scratch.count() > 0 and scratch.is_visible():
            scratch.click()
            page.wait_for_timeout(600)
        else:
            rl = page.locator("#wp-remind-later")
            if rl.count() > 0 and rl.is_visible():
                rl.click()
                page.wait_for_timeout(600)
    # open terrain dock via real tab click
    tab = page.locator(".td-tab[data-dock='terrain']")
    tab.click(force=True)
    page.wait_for_timeout(700)
    # minimize via real click on the dock's minimize button
    minbtn = page.locator("#dock-terrain [data-dock-minimize]").first
    if minbtn.count() == 0:
        minbtn = page.locator("#terrain-controls .minimize-btn, #terrain-min-btn").first
    print("minbtn count:", minbtn.count())
    if minbtn.count() > 0:
        minbtn.click()
        page.wait_for_timeout(700)
    pill = rect(page, "#sculpt-restore-pill")
    scalebar = rect(page, "#scale-bar, .scale-bar")
    sundock = rect(page, "#dock-sun")
    sunbtn = rect(page, "#sun-btn")
    def rnd(d):
        return d and {k: (round(v) if isinstance(v, (int, float)) else v) for k, v in d.items() if k in ('x','y','w','h','display')}
    out = {"pill": rnd(pill), "scalebar": rnd(scalebar), "dock_sun": rnd(sundock), "sun_btn": rnd(sunbtn)}
    if pill and pill["display"] != "none":
        out["overlap_scalebar"] = overlap(pill, scalebar)
        out["overlap_sunbtn"] = overlap(pill, sunbtn)
        out["overlap_docksun"] = overlap(pill, sundock)
        page.screenshot(path=shot_path("r3_fix_sculpt_restore_pill"))
        # also click the pill itself to make sure it restores the panel (real click)
        page.locator("#sculpt-restore-pill").click()
        page.wait_for_timeout(600)
        restored = page.evaluate("() => { const t = document.getElementById('dock-terrain');"
                                 " return {minimized: t ? t.classList.contains('minimized') : null,"
                                 " pillVisible: document.getElementById('sculpt-restore-pill').classList.contains('visible')}; }")
        out["after_pill_click"] = restored
        page.screenshot(path=shot_path("r3_fix_sculpt_restore_pill_after"))
    print(json.dumps(out, indent=1))
    with open("/root/byd29r-modals/reports/s29_shots/r3_f4_pill_results.json", "w") as f:
        json.dump(out, f, indent=1)
    browser.close()
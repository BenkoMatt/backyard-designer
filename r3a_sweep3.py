"""S29 R3 Part 2c — finish the sweep: 1600x900 docks (adv+basic) + 1280 basic underground
via REAL terrain-raise bury flow. Fixed is_clean (not-CLEAN detection)."""
import json
import sys
import time

sys.path.insert(0, "/root/byd29r-modals")
from r3_common import (vision_qa, is_clean, load_app, make_page, shot_path, sidecar,
                       to_advanced)
from playwright.sync_api import sync_playwright

FINDINGS = []


def snap(page, name, label, probe=""):
    path = shot_path(name)
    page.screenshot(path=path)
    v = vision_qa(path)
    clean = is_clean(v)
    sidecar(name, {"surface": name, "label": label, "verdict": v, "issue": probe,
                   "clean": clean, "ts": time.strftime("%H:%M:%S"), "agent": "R3"})
    print(f"[{'CLEAN' if clean else 'DIRTY'}] {name} :: {v.strip()[:130].replace(chr(10), ' | ')}", flush=True)
    FINDINGS.append({"surface": name, "label": label, "clean": clean, "verdict": v, "issue": probe})
    return clean


def zap(page):
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)


def clean_boot(page, advanced=False):
    load_app(page)
    for _ in range(2):
        wp = page.locator("#welcome-prompt")
        if wp.count() > 0 and wp.is_visible():
            for cand in ("#wp-scratch", "#wp-remind-later"):
                b = page.locator(cand)
                if b.count() > 0 and b.is_visible():
                    b.click()
                    page.wait_for_timeout(500)
                    break
            else:
                break
        else:
            break
    if advanced:
        to_advanced(page)


DOCK_ZS = """() => {
    const d = document.getElementById('DOCKID');
    const body = d.querySelector('.dock-panel-body') || d;
    let deepest = 0;
    d.querySelectorAll('.dock-panel-body, .tc-acc-panel, .terrain-controls-body').forEach(el => {
        if (getComputedStyle(el).display !== 'none') {
            const sh = el.scrollHeight, ch = el.clientHeight;
            if (sh - ch > 2 && sh > deepest) deepest = sh;
        }
    });
    const sh = body.scrollHeight, ch = body.clientHeight;
    const r = d.getBoundingClientRect();
    return {scrollH: sh, clientH: ch, bodyOverflow: sh - ch > 2, deepestScroller: deepest,
            rect: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)},
            buried: document.querySelectorAll('#dock-underground-content .buried-item').length};
}"""

with sync_playwright() as p:
    # ============ 1600x900 pass ============
    browser, page, errors = make_page(p, 1600, 900)
    clean_boot(page, advanced=True)
    tab = page.locator(".td-tab[data-dock='terrain']")
    tab.click(force=True)
    page.wait_for_timeout(700)
    zs = page.evaluate(DOCK_ZS.replace("DOCKID", "dock-terrain"))
    print("dock terrain zero-scroll 1600 adv:", json.dumps(zs), flush=True)
    snap(page, "r3a_dock_terrain_full_1600_advanced", "dock terrain 1600x900 advanced", json.dumps(zs))
    dc = page.locator("#dock-terrain [data-dock-close]")
    if dc.count() > 0:
        dc.click()
    else:
        zap(page)
    page.wait_for_timeout(400)
    tab = page.locator(".td-tab[data-dock='underground']")
    tab.click(force=True)
    page.wait_for_timeout(700)
    zu = page.evaluate(DOCK_ZS.replace("DOCKID", "dock-underground"))
    print("dock underground zero-scroll 1600 adv:", json.dumps(zu), flush=True)
    snap(page, "r3a_dock_underground_1600_advanced", "dock underground 1600x900 advanced", json.dumps(zu))
    zap(page)
    # 1600 basic (terrain only; underground tab hidden in basic)
    bas = page.locator("#mode-toggle button[data-mode='basic']")
    if bas.count() > 0:
        bas.click()
        page.wait_for_timeout(600)
    tab = page.locator(".td-tab[data-dock='terrain']")
    tab.click(force=True)
    page.wait_for_timeout(700)
    zs = page.evaluate(DOCK_ZS.replace("DOCKID", "dock-terrain"))
    print("dock terrain zero-scroll 1600 basic:", json.dumps(zs), flush=True)
    snap(page, "r3a_dock_terrain_full_1600_basic", "dock terrain 1600x900 basic", json.dumps(zs))
    browser.close()

    # ============ 1280x800: underground with REAL buried items ============
    browser, page, errors = make_page(p, 1280, 800)
    clean_boot(page, advanced=True)
    # add two objects near center via real sidebar clicks
    items = page.locator(".lib-item")
    if items.count() > 1:
        items.nth(0).click()
        page.wait_for_timeout(700)
    if items.count() > 5:
        items.nth(5).click()
        page.wait_for_timeout(700)
    # open terrain dock, select Raise (key 1), big brush ([ several times), drag over center objects
    tab = page.locator(".td-tab[data-dock='terrain']")
    tab.click(force=True)
    page.wait_for_timeout(600)
    page.keyboard.press("Escape")  # close any hint
    page.wait_for_timeout(200)
    page.keyboard.press("1")  # Raise tool
    page.wait_for_timeout(300)
    for _ in range(8):
        page.keyboard.press("]")  # brush size up
    page.wait_for_timeout(300)
    cv = page.locator("#viewport canvas:not([id])").first
    box = cv.bounding_box()
    if box:
        cx = box["x"] + box["width"] * 0.55
        cy = box["y"] + box["height"] * 0.45
        page.mouse.move(cx, cy)
        page.mouse.down()
        for i in range(8):
            page.mouse.move(cx + (i - 4) * 8, cy + (i % 3 - 1) * 6, steps=3)
            page.wait_for_timeout(120)
        page.mouse.up()
    page.wait_for_timeout(1500)
    buried = page.evaluate("() => (window._test && window._test.getBuriedObjects ? window._test.getBuriedObjects().length : -1)")
    print("buried objects after raise-drag:", buried, flush=True)
    # switch to underground dock
    tabu = page.locator(".td-tab[data-dock='underground']")
    tabu.click(force=True)
    page.wait_for_timeout(700)
    zu = page.evaluate(DOCK_ZS.replace("DOCKID", "dock-underground"))
    print("dock underground 1280 adv w/ buried:", json.dumps(zu), flush=True)
    snap(page, "r3a_dock_underground_buried_1280_advanced", "dock underground with 2+ buried items (real raise-drag)", json.dumps(zu))
    browser.close()

with open("/root/byd29r-modals/reports/s29_shots/r3a_findings3.json", "w") as f:
    json.dump(FINDINGS, f, indent=1)
print(f"\nDONE: {len(FINDINGS)} surfaces; {sum(1 for x in FINDINGS if x['clean'])} clean, "
      f"{sum(1 for x in FINDINGS if not x['clean'])} dirty", flush=True)
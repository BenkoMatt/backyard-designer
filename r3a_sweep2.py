"""S29 R3 Part 2b — remainder of the sweep (gallery/label/print/docks) with wizard-dismiss
robustness: after reload, dismiss wizard Skip AND welcome prompt before proceeding."""
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
    """Load, kill wizard + welcome prompt via real clicks."""
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
    wiz = page.locator("#wizard")
    if wiz.count() > 0 and wiz.is_visible():
        skip = page.locator("#wizard-skip")
        if skip.count() > 0:
            skip.click()
            page.wait_for_timeout(700)
    if advanced:
        to_advanced(page)


def ensure_objects(page, n=6):
    page.evaluate("""(n) => { // SETUP: seed objects via test hook
        if (window._test && window._test.addObject) {
            const types = ['patio', 'tree_pine', 'tree_maple', 'fence', 'path', 'shed'];
            for (let i = 0; i < n; i++) window._test.addObject(types[i % types.length]);
        }
    }""", n)
    page.wait_for_timeout(800)


DOCK_ZS = """() => {
    const d = document.getElementById('DOCKID');
    const body = d.querySelector('.dock-panel-body') || d;
    const dd = document.getElementById('DOCKID');
    const csd = getComputedStyle(dd);
    let deepest = 0;
    dd.querySelectorAll('.dock-panel-body, .tc-acc-panel, .terrain-controls-body').forEach(el => {
        if (getComputedStyle(el).display !== 'none') {
            const sh = el.scrollHeight, ch = el.clientHeight;
            if (sh - ch > 2 && sh > deepest) deepest = sh;
        }
    });
    const sh = body.scrollHeight, ch = body.clientHeight;
    const r = dd.getBoundingClientRect();
    return {scrollH: sh, clientH: ch, bodyOverflow: sh - ch > 2, deepestScroller: deepest,
            rect: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)},
            buried: document.querySelectorAll('#dock-underground-content .buried-item').length};
}"""

with sync_playwright() as p:
    # ============ 1280x800 pass ============
    browser, page, errors = make_page(p, 1280, 800)
    clean_boot(page, advanced=True)
    ensure_objects(page, 6)

    # --- gallery (advanced) ---
    gb = page.locator("#btn-gallery")
    if gb.count() > 0 and gb.is_visible():
        gb.click()
        page.wait_for_timeout(900)
        snap(page, "r3a_gallery_open_1280_advanced", "gallery modal advanced")
        zap(page)
    else:
        print("gallery btn not visible", flush=True)

    # --- label-edit (advanced) ---
    lb = page.locator("#btn-label")
    if lb.count() > 0 and lb.is_visible():
        lb.click()
        page.wait_for_timeout(600)
        sbt = page.evaluate("() => document.getElementById('sb-tool').textContent")
        print("sb-tool while label armed:", sbt, flush=True)
        cv = page.locator("#viewport canvas:not([id])").first
        box = cv.bounding_box()
        if box:
            page.mouse.click(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.45)
        page.wait_for_timeout(700)
        lm = page.evaluate("() => document.getElementById('label-edit-modal').classList.contains('visible')")
        print("label-edit open after canvas click:", lm, flush=True)
        page.keyboard.type("My Patio")
        page.wait_for_timeout(300)
        snap(page, "r3a_label_edit_1280_advanced", f"label-edit modal typed; sbToolWhileArmed={sbt}")
        page.locator("#label-save-btn").click()
        page.wait_for_timeout(500)
        zap(page)

    # --- print preview FULL flow (advanced) ---
    pb = page.locator("#btn-print")
    if pb.count() > 0 and pb.is_visible():
        pb.click()
        page.wait_for_timeout(1200)
        pp = page.evaluate("""() => {
            const pv = document.getElementById('print-view');
            const img = document.getElementById('print-screenshot-img');
            const tbody = document.getElementById('print-objects-body');
            const rows = tbody ? tbody.querySelectorAll('tr').length : 0;
            const total = document.getElementById('print-total-cost') ?
                          document.getElementById('print-total-cost').textContent : null;
            return {visible: pv.classList.contains('visible'),
                    imgW: img ? Math.round(img.getBoundingClientRect().width) : 0,
                    imgLoaded: img ? (img.complete && img.naturalWidth > 0) : false,
                    objRows: rows, total: total,
                    overflow: pv.scrollHeight > pv.clientHeight ? {sh: pv.scrollHeight, ch: pv.clientHeight} : null};
        }""")
        print("print preview probe:", json.dumps(pp), flush=True)
        snap(page, "r3a_print_full_1280_advanced", "print preview full flow with objects", json.dumps(pp))
        page.locator("#print-cancel-btn").click()
        page.wait_for_timeout(400)

    # --- dock terrain zero-scroll @1280 advanced, accordions expanded ---
    tab = page.locator(".td-tab[data-dock='terrain']")
    tab.click(force=True)
    page.wait_for_timeout(700)
    acc = page.locator("#dock-terrain .advanced-toggle")
    for i in range(acc.count()):
        try:
            if acc.nth(i).is_visible() and "expanded" not in (acc.nth(i).get_attribute("class") or ""):
                acc.nth(i).click()
                page.wait_for_timeout(300)
        except Exception:
            pass
    zs = page.evaluate(DOCK_ZS.replace("DOCKID", "dock-terrain"))
    print("dock terrain zero-scroll 1280 adv:", json.dumps(zs), flush=True)
    snap(page, "r3a_dock_terrain_full_1280_advanced", "dock terrain accordions open", json.dumps(zs))
    dc = page.locator("#dock-terrain [data-dock-close]")
    if dc.count() > 0:
        dc.click()
    else:
        zap(page)
    page.wait_for_timeout(400)

    # --- dock underground zero-scroll @1280 advanced with 2 buried ---
    # bury objects: place at negative depth via test hook
    page.evaluate("""() => { // SETUP: sink two objects underground
        if (window._test && window._test.state && window._test.sceneObjects) {
            try {
                const objs = Array.from(window._test.state.objects.values());
                if (objs.length >= 2) {
                    objs.slice(0, 2).forEach(o => { if (o && o.params) o.params.buriedDepth = 4; });
                    if (typeof window._test.updateBuriedObjects === 'function') window._test.updateBuriedObjects();
                }
            } catch (e) {}
        }
    }""")
    tab = page.locator(".td-tab[data-dock='underground']")
    tab.click(force=True)
    page.wait_for_timeout(700)
    zu = page.evaluate(DOCK_ZS.replace("DOCKID", "dock-underground"))
    print("dock underground zero-scroll 1280 adv:", json.dumps(zu), flush=True)
    snap(page, "r3a_dock_underground_1280_advanced", "dock underground with buried items", json.dumps(zu))
    zap(page)

    # --- 1280 BASIC docks ---
    bas = page.locator("#mode-toggle button[data-mode='basic']")
    if bas.count() > 0:
        bas.click()
        page.wait_for_timeout(600)
    tab = page.locator(".td-tab[data-dock='terrain']")
    tab.click(force=True)
    page.wait_for_timeout(700)
    zs = page.evaluate(DOCK_ZS.replace("DOCKID", "dock-terrain"))
    print("dock terrain zero-scroll 1280 basic:", json.dumps(zs), flush=True)
    snap(page, "r3a_dock_terrain_full_1280_basic", "dock terrain basic", json.dumps(zs))
    tabu = page.locator(".td-tab[data-dock='underground']")
    tabu.click(force=True)
    page.wait_for_timeout(700)
    zu = page.evaluate(DOCK_ZS.replace("DOCKID", "dock-underground"))
    print("dock underground zero-scroll 1280 basic:", json.dumps(zu), flush=True)
    snap(page, "r3a_dock_underground_1280_basic", "dock underground basic", json.dumps(zu))
    browser.close()

    # ============ 1600x900 pass ============
    browser, page, errors = make_page(p, 1600, 900)
    clean_boot(page, advanced=True)
    ensure_objects(page, 6)
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
    # 1600 basic
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
    tabu = page.locator(".td-tab[data-dock='underground']")
    tabu.click(force=True)
    page.wait_for_timeout(700)
    zu = page.evaluate(DOCK_ZS.replace("DOCKID", "dock-underground"))
    print("dock underground zero-scroll 1600 basic:", json.dumps(zu), flush=True)
    snap(page, "r3a_dock_underground_1600_basic", "dock underground 1600x900 basic", json.dumps(zu))
    browser.close()

with open("/root/byd29r-modals/reports/s29_shots/r3a_findings2.json", "w") as f:
    json.dump(FINDINGS, f, indent=1)
print(f"\nDONE: {len(FINDINGS)} surfaces; {sum(1 for x in FINDINGS if x['clean'])} clean, "
      f"{sum(1 for x in FINDINGS if not x['clean'])} dirty", flush=True)
"""S29 R3 Part 2 — sweep the un-swept remainder on the merged tree (BEFORE state).

Surfaces: share modal, gallery, label-edit, cmd palette (Ctrl+K open/navigate/execute),
print preview full flow, dock terrain + underground ZERO-SCROLL at 1280x800 AND 1600x900,
Basic and Advanced. Real CDP events; vision verdicts via glm-5.3-flash; DOM probes.
Outputs shots r3a_<surface>_<mode>.png + verdict sidecars + r3a_findings.json.
"""
import json
import sys
import time

sys.path.insert(0, "/root/byd29r-modals")
from r3_common import (vision_qa, is_clean, load_app, make_page, shot_path, sidecar,
                       to_advanced, overlay_probe)
from playwright.sync_api import sync_playwright

FINDINGS = []


def snap(page, name, label, probe=None):
    """Screenshot + DOM probe + vision verdict + sidecar."""
    path = shot_path(name)
    page.screenshot(path=path)
    issue = probe if probe else ""
    v = vision_qa(path)
    clean = is_clean(v)
    sidecar(name, {"surface": name, "label": label, "verdict": v, "issue": issue,
                   "clean": clean, "ts": time.strftime("%H:%M:%S"), "agent": "R3"})
    tag = "CLEAN" if clean else "DIRTY"
    print(f"[{tag}] {name} :: {v.strip()[:120].replace(chr(10), ' | ')}")
    FINDINGS.append({"surface": name, "label": label, "clean": clean, "verdict": v,
                     "issue": issue})
    return clean


def zap(page):
    """Close whatever is topmost: overlays via Escape (real key)."""
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)


def dismiss_welcome(page):
    wp = page.locator("#welcome-prompt")
    if wp.count() > 0 and wp.is_visible():
        for cand in ("#wp-scratch", "#wp-remind-later"):
            b = page.locator(cand)
            if b.count() > 0 and b.is_visible():
                b.click()
                page.wait_for_timeout(500)
                return


def ensure_objects(page, n=6):
    """window._test SETUP: add a few objects so print/gallery/cost aren't empty."""
    page.evaluate("""(n) => { // SETUP (allowed): seed objects via test hook
        if (window._test && window._test.addObject) {
            const types = ['patio', 'tree_pine', 'tree_maple', 'fence', 'path', 'shed'];
            for (let i = 0; i < n; i++) window._test.addObject(types[i % types.length]);
        }
    }""", n)
    page.wait_for_timeout(800)


with sync_playwright() as p:
    # ============ 1280x800 BASIC ============
    browser, page, errors = make_page(p, 1280, 800)
    load_app(page)
    dismiss_welcome(page)
    ensure_objects(page, 6)

    # --- share modal (share is basic-visible? btn-share was clipped off at 1280 basic — open via cmd palette execute instead)
    page.keyboard.press("Control+k")
    page.wait_for_timeout(400)
    page.keyboard.type("share")
    page.wait_for_timeout(400)
    page.keyboard.press("Enter")
    page.wait_for_timeout(900)
    sm = page.evaluate("() => document.getElementById('share-modal').classList.contains('visible')")
    print("share opened:", sm)
    probe = page.evaluate("""() => {
        const qr = document.getElementById('share-qr-canvas');
        const url = document.getElementById('share-url-box');
        return {qrVisible: !!qr && qr.getBoundingClientRect().width > 0,
                urlText: url ? url.textContent.slice(0, 60) : null,
                urlH: url ? Math.round(url.getBoundingClientRect().height) : null};
    }""")
    snap(page, "r3a_share_open_1280_basic", "share modal via Ctrl+K execute", json.dumps(probe))
    zap(page)

    # --- cmd palette: open/navigate/execute (execute = open help via palette)
    page.keyboard.press("Control+k")
    page.wait_for_timeout(400)
    nav = page.evaluate("""() => {
        const items = [...document.querySelectorAll('#cmd-palette-results .cmd-item')];
        return {count: items.length, selected: items.findIndex(i => i.classList.contains('selected')),
                firstText: items[0] ? items[0].textContent.trim().slice(0, 30) : null,
                inputFocused: document.activeElement === document.getElementById('cmd-palette-input'),
                placeholder: document.getElementById('cmd-palette-input').placeholder};
    }""")
    print("cmd palette state:", nav)
    # real keyboard navigation: ArrowDown x3 then Enter to execute
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(200)
    sel = page.evaluate("() => { const s = document.querySelector('#cmd-palette-results .cmd-item.selected');"
                       " return s ? s.textContent.trim().slice(0, 40) : null; }")
    print("after 3x ArrowDown selected:", sel)
    page.keyboard.press("Enter")
    page.wait_for_timeout(900)
    execd = page.evaluate("""() => {
        const open = ['help-modal','shortcuts-modal','share-modal','templates-modal','gallery-modal','label-edit-modal','cmd-palette-overlay','print-view']
            .map(id => ({id, v: document.getElementById(id).classList.contains('visible') || document.getElementById(id).classList.contains('visible') && document.getElementById(id).style.display !== 'none'}))
            .filter(x => x.v).map(x => x.id);
        return {paletteClosed: !document.getElementById('cmd-palette-overlay').classList.contains('visible'), opened: open};
    }""")
    print("after Enter:", execd)
    page.screenshot(path=shot_path("r3a_cmd_exec_result"))
    v = vision_qa(shot_path("r3a_cmd_exec_result"))
    sidecar("r3a_cmd_exec_result", {"surface": "r3a_cmd_exec_result", "label": "cmd palette navigate+execute result (help open)",
                                    "verdict": v, "nav": nav, "selected": sel, "execd": execd, "clean": is_clean(v)})
    print(f"[{'CLEAN' if is_clean(v) else 'DIRTY'}] r3a_cmd_exec_result :: {v.strip()[:120]}")
    FINDINGS.append({"surface": "r3a_cmd_exec_result", "label": "cmd palette navigate+execute", "clean": is_clean(v),
                     "verdict": v, "issue": json.dumps({"nav": nav, "selected": sel, "execd": execd})})
    zap(page)

    # --- cmd palette typed state
    page.keyboard.press("Control+k")
    page.wait_for_timeout(300)
    page.keyboard.type("terrain")
    page.wait_for_timeout(400)
    tp = page.evaluate("() => document.querySelectorAll('#cmd-palette-results .cmd-item').length")
    page.screenshot(path=shot_path("r3a_cmd_typed_1280_basic"))
    v = vision_qa(shot_path("r3a_cmd_typed_1280_basic"))
    sidecar("r3a_cmd_typed_1280_basic", {"surface": "r3a_cmd_typed_1280_basic", "label": f"cmd palette typed 'terrain' ({tp} results)",
                                         "verdict": v, "clean": is_clean(v)})
    print(f"[{'CLEAN' if is_clean(v) else 'DIRTY'}] r3a_cmd_typed_1280_basic :: {v.strip()[:120]}")
    FINDINGS.append({"surface": "r3a_cmd_typed_1280_basic", "label": "cmd palette typed", "clean": is_clean(v), "verdict": v, "issue": ""})
    zap(page)

    # --- gallery (advanced-only button; but gallery reachable via cmd palette? try direct)
    page.evaluate("() => { document.body.classList.remove('byd-basic-mode'); }")  # read-only-ish probe aid? NO — use real toggle
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(1500)
    # real toggle to advanced
    adv = page.locator("#mode-toggle button[data-mode='advanced']")
    if adv.count() > 0:
        adv.click()
        page.wait_for_timeout(700)
    gb = page.locator("#btn-gallery")
    if gb.count() > 0 and gb.is_visible():
        gb.click()
        page.wait_for_timeout(900)
        g = page.evaluate("() => document.getElementById('gallery-modal').classList.contains('visible')")
        print("gallery open:", g)
        page.screenshot(path=shot_path("r3a_gallery_open_1280_advanced"))
        v = vision_qa(shot_path("r3a_gallery_open_1280_advanced"))
        sidecar("r3a_gallery_open_1280_advanced", {"surface": "r3a_gallery_open_1280_advanced", "label": "gallery modal advanced", "verdict": v, "clean": is_clean(v)})
        print(f"[{'CLEAN' if is_clean(v) else 'DIRTY'}] r3a_gallery_open_1280_advanced :: {v.strip()[:120]}")
        FINDINGS.append({"surface": "r3a_gallery_open_1280_advanced", "label": "gallery modal", "clean": is_clean(v), "verdict": v, "issue": ""})
        zap(page)

    # --- label-edit (advanced-only button)
    lb = page.locator("#btn-label")
    if lb.count() > 0 and lb.is_visible():
        lb.click()
        page.wait_for_timeout(600)
        # label mode active: status bar should say Label — check BEFORE placing
        sbt = page.evaluate("() => document.getElementById('sb-tool').textContent")
        print("sb-tool while label armed:", sbt)
        # open the edit modal by clicking in the yard (real click on canvas)
        cv = page.locator("#viewport canvas:not([id])").first
        box = cv.bounding_box()
        if box:
            page.mouse.click(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.45)
        page.wait_for_timeout(700)
        lm = page.evaluate("() => document.getElementById('label-edit-modal').classList.contains('visible')")
        print("label-edit open after canvas click:", lm)
        # type text (real keyboard), save
        page.keyboard.type("My Patio")
        page.wait_for_timeout(300)
        page.screenshot(path=shot_path("r3a_label_edit_1280_advanced"))
        v = vision_qa(shot_path("r3a_label_edit_1280_advanced"))
        sidecar("r3a_label_edit_1280_advanced", {"surface": "r3a_label_edit_1280_advanced", "label": "label-edit modal, typed text", "verdict": v, "clean": is_clean(v), "sbToolWhileArmed": sbt})
        print(f"[{'CLEAN' if is_clean(v) else 'DIRTY'}] r3a_label_edit_1280_advanced :: {v.strip()[:120]}")
        FINDINGS.append({"surface": "r3a_label_edit_1280_advanced", "label": "label-edit modal", "clean": is_clean(v), "verdict": v, "issue": f"sbToolWhileArmed={sbt}"})
        page.locator("#label-save-btn").click()
        page.wait_for_timeout(500)
        zap(page)

    # --- print preview FULL flow (advanced)
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
        print("print preview:", pp)
        page.screenshot(path=shot_path("r3a_print_full_1280_advanced"))
        v = vision_qa(shot_path("r3a_print_full_1280_advanced"))
        sidecar("r3a_print_full_1280_advanced", {"surface": "r3a_print_full_1280_advanced", "label": "print preview full flow with objects", "verdict": v, "clean": is_clean(v), "probe": pp})
        print(f"[{'CLEAN' if is_clean(v) else 'DIRTY'}] r3a_print_full_1280_advanced :: {v.strip()[:120]}")
        FINDINGS.append({"surface": "r3a_print_full_1280_advanced", "label": "print preview full flow", "clean": is_clean(v), "verdict": v, "issue": json.dumps(pp)})
        # close via real click
        page.locator("#print-cancel-btn").click()
        page.wait_for_timeout(400)

    # --- dock terrain zero-scroll @1280 advanced (with all 3 accordions open)
    tab = page.locator(".td-tab[data-dock='terrain']")
    tab.click(force=True)
    page.wait_for_timeout(700)
    # expand all accordions (real clicks)
    acc = page.locator("#dock-terrain .advanced-toggle, #dock-terrain .accordion-toggle")
    for i in range(acc.count()):
        try:
            if acc.nth(i).is_visible():
                acc.nth(i).click()
                page.wait_for_timeout(300)
        except Exception:
            pass
    zs = page.evaluate("""() => {
        const d = document.getElementById('dock-terrain');
        const body = d.querySelector('.dock-panel-body') || d;
        const sh = body.scrollHeight, ch = body.clientHeight;
        return {scrollH: sh, clientH: ch, overflow: sh - ch > 2,
                rect: (() => { const r = d.getBoundingClientRect(); return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)}; })()};
    }""")
    print("dock terrain zero-scroll 1280 adv:", zs)
    page.screenshot(path=shot_path("r3a_dock_terrain_full_1280_advanced"))
    v = vision_qa(shot_path("r3a_dock_terrain_full_1280_advanced"))
    sidecar("r3a_dock_terrain_full_1280_advanced", {"surface": "r3a_dock_terrain_full_1280_advanced", "label": "dock terrain accordions open", "verdict": v, "clean": is_clean(v), "zs": zs})
    print(f"[{'CLEAN' if is_clean(v) else 'DIRTY'}] r3a_dock_terrain_full_1280_advanced :: {v.strip()[:120]}")
    FINDINGS.append({"surface": "r3a_dock_terrain_full_1280_advanced", "label": "dock terrain accordions, zero-scroll", "clean": is_clean(v), "verdict": v, "issue": json.dumps(zs)})
    # close dock
    page.locator("#dock-terrain [data-dock-close]").click() if page.locator("#dock-terrain [data-dock-close]").count() > 0 else zap(page)
    page.wait_for_timeout(400)

    # --- dock underground zero-scroll @1280 advanced (with 2 buried items)
    page.evaluate("""() => { // SETUP: bury two objects
        if (window._test && window._test.addObject) {
            window._test.addObject('shed');
            window._test.addObject('tree_pine');
        }
    }""")
    tab = page.locator(".td-tab[data-dock='underground']")
    tab.click(force=True)
    page.wait_for_timeout(700)
    zu = page.evaluate("""() => {
        const d = document.getElementById('dock-underground');
        const body = d.querySelector('.dock-panel-body') || d;
        const buried = [...document.querySelectorAll('#dock-underground-content .buried-item')].length;
        return {scrollH: body.scrollHeight, clientH: body.clientHeight,
                overflow: body.scrollHeight - body.clientHeight > 2, buriedItems: buried,
                rect: (() => { const r = d.getBoundingClientRect(); return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)}; })()};
    }""")
    print("dock underground zero-scroll 1280 adv:", zu)
    page.screenshot(path=shot_path("r3a_dock_underground_1280_advanced"))
    v = vision_qa(shot_path("r3a_dock_underground_1280_advanced"))
    sidecar("r3a_dock_underground_1280_advanced", {"surface": "r3a_dock_underground_1280_advanced", "label": "dock underground with buried items", "verdict": v, "clean": is_clean(v), "zs": zu})
    print(f"[{'CLEAN' if is_clean(v) else 'DIRTY'}] r3a_dock_underground_1280_advanced :: {v.strip()[:120]}")
    FINDINGS.append({"surface": "r3a_dock_underground_1280_advanced", "label": "dock underground zero-scroll", "clean": is_clean(v), "verdict": v, "issue": json.dumps(zu)})
    zap(page)
    browser.close()

    # ============ 1600x900 pass (docks + modals spot) ============
    browser, page, errors = make_page(p, 1600, 900)
    load_app(page)
    dismiss_welcome(page)
    ensure_objects(page, 6)
    to_advanced(page)
    tab = page.locator(".td-tab[data-dock='terrain']")
    tab.click(force=True)
    page.wait_for_timeout(700)
    zs = page.evaluate("""() => {
        const d = document.getElementById('dock-terrain');
        const body = d.querySelector('.dock-panel-body') || d;
        return {scrollH: body.scrollHeight, clientH: body.clientHeight, overflow: body.scrollHeight - body.clientHeight > 2};
    }""")
    print("dock terrain zero-scroll 1600 adv:", zs)
    page.screenshot(path=shot_path("r3a_dock_terrain_1600_advanced"))
    v = vision_qa(shot_path("r3a_dock_terrain_1600_advanced"))
    sidecar("r3a_dock_terrain_1600_advanced", {"surface": "r3a_dock_terrain_1600_advanced", "label": "dock terrain 1600x900", "verdict": v, "clean": is_clean(v), "zs": zs})
    print(f"[{'CLEAN' if is_clean(v) else 'DIRTY'}] r3a_dock_terrain_1600_advanced :: {v.strip()[:120]}")
    FINDINGS.append({"surface": "r3a_dock_terrain_1600_advanced", "label": "dock terrain 1600 zero-scroll", "clean": is_clean(v), "verdict": v, "issue": json.dumps(zs)})
    page.locator("#dock-terrain [data-dock-close]").click() if page.locator("#dock-terrain [data-dock-close]").count() > 0 else zap(page)
    page.wait_for_timeout(400)

    tab = page.locator(".td-tab[data-dock='underground']")
    tab.click(force=True)
    page.wait_for_timeout(700)
    zu = page.evaluate("""() => {
        const d = document.getElementById('dock-underground');
        const body = d.querySelector('.dock-panel-body') || d;
        return {scrollH: body.scrollHeight, clientH: body.clientHeight, overflow: body.scrollHeight - body.clientHeight > 2};
    }""")
    print("dock underground zero-scroll 1600 adv:", zu)
    page.screenshot(path=shot_path("r3a_dock_underground_1600_advanced"))
    v = vision_qa(shot_path("r3a_dock_underground_1600_advanced"))
    sidecar("r3a_dock_underground_1600_advanced", {"surface": "r3a_dock_underground_1600_advanced", "label": "dock underground 1600x900", "verdict": v, "clean": is_clean(v), "zs": zu})
    print(f"[{'CLEAN' if is_clean(v) else 'DIRTY'}] r3a_dock_underground_1600_advanced :: {v.strip()[:120]}")
    FINDINGS.append({"surface": "r3a_dock_underground_1600_advanced", "label": "dock underground 1600 zero-scroll", "clean": is_clean(v), "verdict": v, "issue": json.dumps(zu)})
    zap(page)

    # 1600 basic docks
    bas = page.locator("#mode-toggle button[data-mode='basic']")
    if bas.count() > 0:
        bas.click()
        page.wait_for_timeout(600)
    tab = page.locator(".td-tab[data-dock='terrain']")
    tab.click(force=True)
    page.wait_for_timeout(700)
    zs = page.evaluate("""() => {
        const d = document.getElementById('dock-terrain');
        const body = d.querySelector('.dock-panel-body') || d;
        return {scrollH: body.scrollHeight, clientH: body.clientHeight, overflow: body.scrollHeight - body.clientHeight > 2};
    }""")
    print("dock terrain zero-scroll 1600 basic:", zs)
    page.screenshot(path=shot_path("r3a_dock_terrain_1600_basic"))
    v = vision_qa(shot_path("r3a_dock_terrain_1600_basic"))
    sidecar("r3a_dock_terrain_1600_basic", {"surface": "r3a_dock_terrain_1600_basic", "label": "dock terrain 1600x900 basic", "verdict": v, "clean": is_clean(v), "zs": zs})
    print(f"[{'CLEAN' if is_clean(v) else 'DIRTY'}] r3a_dock_terrain_1600_basic :: {v.strip()[:120]}")
    FINDINGS.append({"surface": "r3a_dock_terrain_1600_basic", "label": "dock terrain 1600 basic zero-scroll", "clean": is_clean(v), "verdict": v, "issue": json.dumps(zs)})
    browser.close()

with open("/root/byd29r-modals/reports/s29_shots/r3a_findings.json", "w") as f:
    json.dump(FINDINGS, f, indent=1)
print(f"\nDONE: {len(FINDINGS)} surfaces swept; "
      f"{sum(1 for x in FINDINGS if x['clean'])} clean, "
      f"{sum(1 for x in FINDINGS if not x['clean'])} dirty")
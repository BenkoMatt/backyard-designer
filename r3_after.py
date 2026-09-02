"""R3 AFTER verification: DOM-probe each fix + re-screenshot + vision verdict."""
import json
import sys
import time

sys.path.insert(0, "/root/byd29r-modals")
from r3_common import (vision_qa, is_clean, load_app, make_page, shot_path, sidecar,
                       to_advanced)
from playwright.sync_api import sync_playwright

RESULTS = {}


def snap(page, name, label, probe=""):
    path = shot_path(name)
    page.screenshot(path=path)
    v = vision_qa(path)
    clean = is_clean(v)
    sidecar(name, {"surface": name, "label": label, "verdict": v, "issue": probe,
                   "clean": clean, "ts": time.strftime("%H:%M:%S"), "agent": "R3-after"})
    print(f"[{'CLEAN' if clean else 'DIRTY'}] {name} :: {v.strip()[:140].replace(chr(10), ' | ')}", flush=True)
    return {"name": name, "clean": clean, "verdict": v, "probe": probe}


def zap(page):
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)


with sync_playwright() as p:
    browser, page, errors = make_page(p, 1280, 800)
    load_app(page)
    # dismiss welcome
    wp = page.locator("#welcome-prompt")
    if wp.count() > 0 and wp.is_visible():
        for cand in ("#wp-scratch", "#wp-remind-later"):
            b = page.locator(cand)
            if b.count() > 0 and b.is_visible():
                b.click()
                page.wait_for_timeout(500)
                break

    # --- A1: toolbar one row at 1280, clear of scale-bar ---
    a1 = page.evaluate("""() => {
        const sb = document.querySelector('#scale-bar').getBoundingClientRect();
        const tb = document.getElementById('bottom-left-toolbar').getBoundingClientRect();
        const kids = [...document.querySelectorAll('#bottom-left-toolbar > button')].map(b => {
            const r = b.getBoundingClientRect();
            return {id: b.id, x: Math.round(r.x), y: Math.round(r.y), right: Math.round(r.right)};
        });
        const ys = new Set(kids.map(k => k.y));
        return {scaleRight: Math.round(sb.right), toolbarH: Math.round(tb.height),
                oneRow: ys.size === 1, rows: [...ys], kids,
                minGap: Math.round(Math.min(...kids.map(k => k.x)) - sb.right)};
    }""")
    print("A1 toolbar:", json.dumps(a1), flush=True)
    RESULTS["A1_toolbar"] = a1
    page.screenshot(path=shot_path("r3_after_toolbar_1280"))
    RESULTS["A1_vision"] = snap(page, "r3_after_toolbar_1280", "toolbar one row, clear of scale-bar (AFTER)")

    # --- A2: topbar cue now shows when NOT at end ---
    a2 = page.evaluate("""() => {
        const tb = document.getElementById('topbar');
        const hasOverflow = tb.scrollWidth > tb.clientWidth + 2;
        const atEnd = tb.scrollLeft + tb.clientWidth >= tb.scrollWidth - 2;
        return {overflow: hasOverflow, scrolledEndClass: tb.classList.contains('scrolled-end'),
                cueVisibleWhenCut: hasOverflow && !atEnd ? tb.classList.contains('scrolled-end') : 'n/a'};
    }""")
    print("A2 topbar cue:", a2, flush=True)
    RESULTS["A2_topbar"] = a2

    # --- A3: share URL single line ---
    page.keyboard.press("Control+k")
    page.wait_for_timeout(400)
    page.keyboard.type("share")
    page.wait_for_timeout(300)
    page.keyboard.press("Enter")
    page.wait_for_timeout(900)
    a3 = page.evaluate("""() => {
        const u = document.getElementById('share-url-box');
        const r = u.getBoundingClientRect();
        return {h: Math.round(r.height), scrollW: u.scrollWidth, clientW: u.clientWidth,
                oneLine: r.height < 40};
    }""")
    print("A3 share url:", a3, flush=True)
    RESULTS["A3_share"] = a3
    RESULTS["A3_vision"] = snap(page, "r3_after_share_1280", "share modal (AFTER)")
    zap(page)

    # --- A4: cmd palette 1px border ---
    page.keyboard.press("Control+k")
    page.wait_for_timeout(400)
    a4 = page.evaluate("() => getComputedStyle(document.getElementById('cmd-palette-input')).borderBottomWidth")
    print("A4 cmd border:", a4, flush=True)
    RESULTS["A4_cmd_border"] = a4
    page.keyboard.type("terrain")
    page.wait_for_timeout(400)
    RESULTS["A4_vision"] = snap(page, "r3_after_cmd_typed_1280", "cmd palette typed (AFTER)")
    zap(page)

    browser.close()

    # --- A5: label tool status + anchor (advanced) ---
    browser, page, errors = make_page(p, 1280, 800)
    load_app(page)
    wp = page.locator("#welcome-prompt")
    if wp.count() > 0 and wp.is_visible():
        for cand in ("#wp-scratch", "#wp-remind-later"):
            b = page.locator(cand)
            if b.count() > 0 and b.is_visible():
                b.click()
                page.wait_for_timeout(500)
                break
    to_advanced(page)
    page.locator("#btn-label").click()
    page.wait_for_timeout(600)
    a5a = page.evaluate("() => document.getElementById('sb-tool').textContent")
    print("A5 sb-tool while armed:", a5a, flush=True)
    cv = page.locator("#viewport canvas:not([id])").first
    box = cv.bounding_box()
    if box:
        page.mouse.click(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.45)
    page.wait_for_timeout(700)
    page.keyboard.type("My Patio")
    page.wait_for_timeout(300)
    RESULTS["A5_vision_modal"] = snap(page, "r3_after_label_edit_1280", "label-edit modal (AFTER)")
    page.locator("#label-save-btn").click()
    page.wait_for_timeout(800)
    a5b = page.evaluate("() => document.getElementById('sb-tool').textContent")
    print("A5 sb-tool after save:", a5b, flush=True)
    RESULTS["A5_label"] = {"armed": a5a, "afterSave": a5b}
    # label visible in scene with anchor
    RESULTS["A5_vision_scene"] = snap(page, "r3_after_label_scene_1280", "label placed in scene with anchor stem (AFTER)")
    browser.close()

with open("/root/byd29r-modals/reports/s29_shots/r3_after_results.json", "w") as f:
    json.dump(RESULTS, f, indent=1, default=str)
print("WROTE r3_after_results.json", flush=True)
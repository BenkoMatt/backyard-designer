"""S29 R3 Part 1 — re-verify audit-modals' merged fixes landed in the merged tree (de2cae8).

Checks (DOM ground truth + screenshots, read-only probes):
  F1 sticky help header at scroll-bottom
  F2 print preview visible on screen (fixed overlay)
  F3 templates Close reachable (compact cards, Close in viewport)
  F4 sculpt-restore-pill clear of scale-bar/Sun
  F5 V01 progressive-hint hidden over open dock panels
Real CDP events for all interactions.
"""
import json
import sys

sys.path.insert(0, "/root/byd29r-modals")
from r3_common import (URL, load_app, make_page, shot_path, overlay_probe, to_advanced)
from playwright.sync_api import sync_playwright

results = {}


def rect(page, sel):
    return page.evaluate("(s) => { const e = document.querySelector(s); if (!e) return null;"
                         " const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);"
                         " return {x: r.x, y: r.y, w: r.width, h: r.height,"
                         " display: cs.display, visibility: cs.visibility, op: cs.opacity}; }", sel)


def overlap(a, b):
    if not a or not b:
        return None
    ox = max(0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    oy = max(0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    return {"ox": round(ox), "oy": round(oy)}


with sync_playwright() as p:
    browser, page, errors = make_page(p)
    load_app(page)
    print("pageerrors:", errors[:5])

    # ---- F1: sticky help header at scroll-bottom ----
    page.locator("#btn-help").click()
    page.wait_for_timeout(700)
    panel = page.locator("#help-modal .help-panel")
    panel.click()  # focus for real wheel scroll
    page.mouse.wheel(0, 5000)
    page.wait_for_timeout(500)
    page.mouse.wheel(0, 5000)
    page.wait_for_timeout(500)
    f1 = page.evaluate("""() => {
        const panel = document.querySelector('#help-modal .help-panel');
        const header = panel ? panel.querySelector('h2, .help-header, header') : null;
        const title = document.querySelector('#help-modal h2, #help-modal .help-header');
        const el = header || title;
        if (!el) return {found: false};
        const r = el.getBoundingClientRect();
        const pr = panel.getBoundingClientRect();
        // sticky: title's top should stay near panel's top even at scroll-bottom
        return {found: true, titleTop: Math.round(r.y), panelTop: Math.round(pr.y),
                scrollTop: panel.scrollTop, scrollH: panel.scrollHeight,
                clientH: panel.clientHeight, text: (el.textContent||'').trim().slice(0,30)};
    }""")
    page.screenshot(path=shot_path("r3_fix_help_scrolled_bottom"))
    results["F1_sticky_help_header"] = f1
    print("F1 sticky help header:", f1)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # ---- F2: print preview visible on screen (Advanced mode) ----
    to_advanced(page)
    btn = page.locator("#btn-print")
    if btn.count() > 0 and btn.is_visible():
        btn.click()
        page.wait_for_timeout(800)
        opened = True
    else:
        opened = False
    pv = rect(page, "#print-view")
    if pv and pv["display"] != "none":
        page.screenshot(path=shot_path("r3_fix_print_preview"))
        results["F2_print_preview_visible"] = {"visible": True, "rect": {k: (round(v) if isinstance(v, (int, float)) else v) for k, v in pv.items() if k != 'op'}}
    else:
        results["F2_print_preview_visible"] = {"visible": False, "rect": pv, "clicked": opened}
    print("F2 print preview visible:", results["F2_print_preview_visible"])
    if opened:
        # close via print view's own Close button (real click)
        pcb = page.locator("#print-cancel-btn")
        if pcb.count() > 0 and pcb.is_visible():
            pcb.click()
            page.wait_for_timeout(500)

    # ---- F3: templates Close reachable (Advanced mode) ----
    btn = page.locator("#btn-templates")
    if btn.count() > 0 and btn.is_visible():
        btn.click()
        page.wait_for_timeout(800)
        f3 = page.evaluate("""() => {
            const m = document.getElementById('templates-modal');
            if (!m) return {found: false};
            const cs = getComputedStyle(m);
            const cands = [...m.querySelectorAll('button, .modal-close, [data-close]')]
                .filter(b => /close/i.test(b.textContent || '') || /close/i.test(b.className || '') || b.getAttribute('data-close') !== null);
            let closeBtn = cands.find(b => b.getBoundingClientRect().width > 0);
            const r = closeBtn ? closeBtn.getBoundingClientRect() : null;
            const cards = m.querySelectorAll('.templates-card, .tpl-card, .tpl-item');
            return {found: true, display: cs.display, visible: m.classList.contains('visible'),
                    closeBtn: r ? {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
                                   inViewport: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight} : null,
                    cardCount: cards.length};
        }""")
        page.screenshot(path=shot_path("r3_fix_templates_close"))
        results["F3_templates_close_reachable"] = f3
        print("F3 templates Close reachable:", f3)
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    # ---- F4: sculpt-restore-pill clear of scale-bar/Sun ----
    # sculpt a bit to trigger the pill: use window._test setup to arm restore snapshot, then dig
    page.evaluate("""() => { // window._test SETUP (allowed)
        try { if (window._test && window._test.armRestore) window._test.armRestore(); } catch(e) {}
    }""")
    page.keyboard.press("5")  # dig tool
    page.wait_for_timeout(400)
    cv = page.locator("#viewport canvas:not([id])").first
    box = cv.bounding_box()
    if box:
        page.mouse.move(box["x"] + box["width"] * 0.55, box["y"] + box["height"] * 0.45)
        page.mouse.down()
        page.mouse.move(box["x"] + box["width"] * 0.55, box["y"] + box["height"] * 0.42, steps=6)
        page.mouse.up()
    page.wait_for_timeout(1200)
    pill = rect(page, "#sculpt-restore-pill, .restore-pill, #restore-pill")
    scalebar = rect(page, "#scale-bar, .scale-bar")
    sundock = rect(page, "#dock-sun, #sun-panel, .sun-panel")
    def rnd(d):
        return d and {k: (round(v) if isinstance(v, (int, float)) else v) for k, v in d.items() if k in ('x','y','w','h','display')}
    f4 = {"pill": rnd(pill),
          "scalebar": rnd(scalebar),
          "sun": rnd(sundock)}
    if pill and pill["display"] != "none":
        f4["overlap_scalebar"] = overlap(pill, scalebar)
        f4["overlap_sun"] = overlap(pill, sundock)
        page.screenshot(path=shot_path("r3_fix_sculpt_restore_pill"))
    results["F4_sculpt_restore_pill"] = f4
    print("F4 sculpt-restore-pill:", f4)

    # ---- F5: progressive-hint hidden over open dock panel ----
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    page.evaluate("() => { localStorage.setItem('backyard-progressive-hint-count', '0'); }")  # setup: force hint
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(1500)
    tab = page.locator(".td-tab[data-dock='terrain']")
    if tab.count() > 0:
        tab.click(force=True)
        page.wait_for_timeout(700)
        hint = page.evaluate("""() => {
            const h = document.getElementById('progressive-hint');
            if (!h) return {found: false};
            const cs = getComputedStyle(h);
            return {found: true, display: cs.display, visibility: cs.visibility, op: cs.opacity,
                    hidden: cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05};
        }""")
        page.screenshot(path=shot_path("r3_fix_progressive_hint_dock"))
        results["F5_progressive_hint_over_dock"] = hint
        print("F5 progressive-hint over open dock:", hint)

    browser.close()

print(json.dumps(results, indent=1))
with open("/root/byd29r-modals/reports/s29_shots/r3_fix_verify_results.json", "w") as f:
    json.dump(results, f, indent=1)
print("WROTE r3_fix_verify_results.json")
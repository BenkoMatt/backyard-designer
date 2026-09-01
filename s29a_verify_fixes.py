#!/usr/bin/env python3
"""S29 Agent 3: functional verification of the S29 fixes (B1/B2/B4/B6/B7) via real CDP flows."""
import json
import sys

sys.path.insert(0, "/root/byd29-audit-modals")
from playwright.sync_api import sync_playwright

R = []


def log(name, ok, ev=""):
    R.append({"t": name, "ok": bool(ok), "ev": str(ev)[:200]})
    print(("[PASS] " if ok else "[FAIL] ") + name + (" :: " + str(ev)[:150] if ev else ""))


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox",
                                               "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    page = b.new_page(viewport={"width": 1280, "height": 800})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto("http://localhost:8186/index.html", wait_until="networkidle")
    page.wait_for_timeout(1800)
    page.locator("#wizard-skip").click()
    page.wait_for_timeout(1300)
    # welcome prompt appears after skip; wait for it
    for i in range(6):
        page.mouse.move(500 + i * 30, 300)  # wiggle: suppresses progressive hint (mousemove)
        page.wait_for_timeout(250)
    wpv = page.evaluate("() => document.getElementById('welcome-prompt').classList.contains('visible')")
    log("welcome prompt visible after wizard skip", wpv)
    # B2: let it idle 6s WITH welcome open → hint must NOT appear (guard)
    page.wait_for_timeout(6300)
    hv = page.evaluate("() => document.getElementById('progressive-hint').classList.contains('visible')")
    log("B2: no progressive hint while welcome prompt open (6s idle)", not hv)
    # click Remind me later — must not be intercepted now
    page.locator("#wp-remind-later").click(timeout=4000)
    page.wait_for_timeout(400)
    wpv2 = page.evaluate("() => document.getElementById('welcome-prompt').classList.contains('visible')")
    log("B2: Remind-me-later clickable (welcome dismissed)", not wpv2)
    # B2: open help modal, idle 6s → hint must not appear over it
    page.locator("#mode-toggle button[data-mode='advanced']").click()
    page.wait_for_timeout(500)
    page.click("#btn-help")
    page.wait_for_timeout(6300)
    hv2 = page.evaluate("() => document.getElementById('progressive-hint').classList.contains('visible')")
    log("B2: no progressive hint over open help modal", not hv2)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # B1: print preview now a fixed overlay — report must be visible in viewport
    page.click("#btn-print")
    page.wait_for_timeout(900)
    pv = page.evaluate("""() => {
      const el = document.getElementById('print-view');
      const r = el.getBoundingClientRect();
      const h1 = el.querySelector('h1');
      const h1r = h1.getBoundingClientRect();
      const cb = document.getElementById('print-cancel-btn');
      const cbr = cb.getBoundingClientRect();
      const cbTop = document.elementFromPoint(cbr.x + cbr.width/2, cbr.y + cbr.height/2) === cb;
      return {x: r.x, y: r.y, w: r.width, h: r.height, h1y: Math.round(h1r.y), cancelVisible: cbTop && cbr.y > 0 && cbr.y < 800};
    }""")
    log("B1: print report visible on screen (fixed overlay at 0,0)", pv["y"] == 0 and pv["x"] == 0, pv)
    log("B1: report H1 title inside viewport", 0 < pv["h1y"] < 800, "h1 y=" + str(pv["h1y"]))
    log("B1: Close button visible and on top", pv["cancelVisible"])
    page.click("#print-cancel-btn")
    page.wait_for_timeout(300)

    # B4: templates modal — Close button fully inside panel, no scroll needed
    page.click("#btn-templates")
    page.wait_for_timeout(600)
    tp = page.evaluate("""() => {
      const p2 = document.querySelector('.templates-panel');
      const pr = p2.getBoundingClientRect();
      const cb = document.getElementById('templates-close-btn');
      const cr = cb.getBoundingClientRect();
      return {panelBottom: Math.round(pr.bottom), closeBottom: Math.round(cr.bottom),
              scrollNeeded: p2.scrollHeight - p2.clientHeight};
    }""")
    log("B4: templates Close button fully visible (no scroll)", tp["closeBottom"] <= tp["panelBottom"] + 1, tp)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # B6: shortcuts row shows keycaps once (keys column only)
    page.keyboard.press("?")
    page.wait_for_timeout(500)
    kb = page.evaluate("""() => {
      const row = [...document.querySelectorAll('.sc-row')].find(r => r.textContent.includes('Brush mode'));
      return row ? row.querySelectorAll('kbd').length : -1;
    }""")
    log("B6: brush-mode row has single keycap pair (2 kbd)", kb == 2, "kbd count=" + str(kb))
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # B7: sculpt-restore-pill no longer overlaps scale bar / sun button
    page.locator(".td-tab[data-dock='terrain']").click()
    page.wait_for_timeout(600)
    page.locator("#dock-terrain [data-dock-minimize]").click()
    page.wait_for_timeout(500)
    pill = page.evaluate("""() => {
      const pr = document.getElementById('sculpt-restore-pill').getBoundingClientRect();
      const sb = document.getElementById('scale-bar').getBoundingClientRect();
      const sun = document.getElementById('sun-btn').getBoundingClientRect();
      const ov = (a, b) => !(a.right < b.left || a.left > b.right || a.bottom < b.top || a.top > b.bottom);
      return {pill: {x: Math.round(pr.x), y: Math.round(pr.y), w: Math.round(pr.width), h: Math.round(pr.height)},
              hitsScaleBar: ov(pr, sb), hitsSun: ov(pr, sun)};
    }""")
    log("B7: pill does not overlap scale bar", not pill["hitsScaleBar"], pill)
    log("B7: pill does not overlap Sun button", not pill["hitsSun"])
    # pill still restores panel on real click
    page.locator("#sculpt-restore-pill").click()
    page.wait_for_timeout(500)
    restored = page.evaluate("() => !document.getElementById('dock-terrain').classList.contains('minimized')")
    log("B7: pill click restores minimized panel", restored)
    log("no page errors during verification", len(errs) == 0, "; ".join(errs[:2]))
    b.close()

with open("/root/byd29-audit-modals/reports/s29_shots/fix_verify_results.json", "w") as f:
    json.dump(R, f, indent=1)
fails = [r for r in R if not r["ok"]]
print(f"\n=== {len(R) - len(fails)}/{len(R)} passed ===")
sys.exit(1 if fails else 0)
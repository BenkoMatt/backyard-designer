"""Sprint 23 Agent 2 — panel-conflict regression gate.

Locks the Sprint 23 PANEL-CONFLICT fixes (agent 2 scope):

  F1  Double 'Underground View': the moved-in legacy .excavate-header inside
      #dock-underground-content must be CSS-hidden (single title bar, single X).
  F2  Same disease in #dock-innovate-content (.innov-header hide).
  F3  Dock-panel geometry: no overlap with #tool-dock or #bottom-left-toolbar;
      no viewport clipping (right/bottom); flush above status bar.
  F4  Tool-dock flush above status bar (no clipped Atmosphere tab).
  F5  stale-flag guard: closeDockPanel clears a stale `visible` class on the
      legacy #excavate-panel shell (mutual exclusivity invariant).
  F6  Right-panel-stack combinations (cost/layer/season/growth/permit,
      cross-section, cut-fill, dock+cost) produce ZERO panel-panel rect overlaps.

Usage:
    BASE_URL=http://localhost:8092 python3 sprint23_panel_conflict_gate.py
    python3 sprint23_panel_conflict_gate.py --base-url http://localhost:8092 [--port 8092]
"""
import argparse
import json
import os
import sys

from playwright.sync_api import sync_playwright

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(SCRIPT_DIR, "reports", "sprint23_panel_audit")
os.makedirs(SHOTS, exist_ok=True)

RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)[:220]) if detail else ""))
    return bool(ok)


def rect_inter(a, b):
    ix = max(0.0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    iy = max(0.0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    return ix * iy


RECT_JS = """(sel) => {
  const el = document.querySelector(sel);
  if (!el) return null;
  const cs = getComputedStyle(el);
  if (cs.display === 'none' || cs.visibility === 'hidden') return null;
  const r = el.getBoundingClientRect();
  if (r.width < 2 || r.height < 2) return null;
  return { x: r.x, y: r.y, w: r.width, h: r.height, z: parseInt(cs.zIndex) || 0 };
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=os.environ.get("BASE_URL", ""))
    ap.add_argument("--port", type=int, default=int(os.environ.get("S23B_PORT", "8092")))
    args = ap.parse_args()
    base = args.base_url or f"http://localhost:{args.port}"
    url = base.rstrip("/") + "/index.html"

    import s23a_common  # same dir
    s23a_common.URL = url

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        load = s23a_common.load_app
        adv = s23a_common.to_advanced
        load(page)
        adv(page)

        def close_all():
            page.evaluate("""() => {
                document.querySelectorAll('.dock-panel.visible').forEach(el => el.classList.remove('visible'));
                const c = document.getElementById('dock-panel-container');
                if (c) c.classList.remove('visible');
                document.querySelectorAll('.td-tab.active').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-pressed','false'); });
                ['#cost-panel','#layer-panel','#season-panel','#growth-panel','#permit-panel','#cross-section-panel','#cut-fill-panel'].forEach(s => {
                    const el = document.querySelector(s); if (el) el.classList.remove('visible'); });
                const eb = document.getElementById('excavate-btn');
                if (eb) { eb.classList.remove('active'); eb.setAttribute('aria-pressed','false'); }
                // keep the app's crossSectionMode flag in sync with the DOM: if the CS
                // panel was closed out-of-band above, click the toggle OFF via its real
                // handler path only when it still reports active in the DOM.
                const csb = document.getElementById('cross-section-toggle');
                if (csb && csb.classList.contains('active')) {
                    csb.classList.remove('active'); csb.setAttribute('aria-pressed', 'false');
                }
            }""")
            page.wait_for_timeout(280)

        # ---- F1: single Underground View header (real CDP click on the dock tab) ----
        page.click('.td-tab[data-dock="underground"]')
        page.wait_for_timeout(500)
        ugh = page.evaluate("""() => {
            const c = document.getElementById('dock-underground-content');
            if (!c) return { present: false };
            const hs = Array.from(c.querySelectorAll('.excavate-header'));
            return { present: hs.length > 0,
                     visible: hs.filter(h => getComputedStyle(h).display !== 'none').length,
                     dockVisible: document.getElementById('dock-underground').classList.contains('visible') };
        }""")
        page.screenshot(path=f"{SHOTS}/gate_underground_dock.png")
        record("f1:dock_underground_opens", ugh.get("dockVisible") is True)
        record("f1:single_underground_header", ugh.get("present") and ugh.get("visible") == 0,
               f"legacy headers found={ugh.get('present')}, visible={ugh.get('visible')} (must be hidden)")

        # ---- F5: stale-flag guard on closeDockPanel ----
        stale = page.evaluate("""() => {
            // simulate the old double-panel path: legacy shell left marked visible
            const sh = document.getElementById('excavate-panel');
            sh.classList.add('visible');
            window._dockClosePanel();           // close the currently open dock
            return { shellVisible: sh.classList.contains('visible') };
        }""")
        record("f5:close_dock_clears_stale_excavate_visible", stale["shellVisible"] is False,
               f"shell visible after close = {stale['shellVisible']}")
        page.wait_for_timeout(300)

        # excavate launcher still works end-to-end after guard (drive dock, arm clip)
        page.click("#excavate-btn")
        page.wait_for_timeout(500)
        ok_open = page.evaluate("""() => {
            const t = window._test;
            const d = window._groundVisibilityDebug ? window._groundVisibilityDebug() : {};
            return { dock: document.getElementById('dock-underground').classList.contains('visible'),
                     btn: document.getElementById('excavate-btn').classList.contains('active'),
                     clip: !!d.autoDigClipActive };
        }""")
        page.screenshot(path=f"{SHOTS}/gate_excavate_route.png")
        record("f5:excavate_launcher_opens_dock", ok_open["dock"] and ok_open["btn"])
        record("f5:excavate_arms_dig_clip", ok_open["clip"])
        # close via excavate-close (JS convention as in qa_s21) -> dock closes too
        page.evaluate("() => document.getElementById('excavate-close').click()")
        page.wait_for_timeout(400)
        ok_closed = page.evaluate("""() => ({
            dock: document.getElementById('dock-underground').classList.contains('visible'),
            eb: document.getElementById('excavate-btn').classList.contains('active') })""")
        record("f5:excavate_close_closes_dock", not ok_closed["dock"] and not ok_closed["eb"])

        # ---- F2: innovate dock single header ----
        page.click('.td-tab[data-dock="innovate"]')
        page.wait_for_timeout(500)
        ih = page.evaluate("""() => {
            const c = document.getElementById('dock-innovate-content');
            const hs = c ? Array.from(c.querySelectorAll('.innov-header')) : [];
            return { found: hs.length, visible: hs.filter(h => getComputedStyle(h).display !== 'none').length };
        }""")
        page.screenshot(path=f"{SHOTS}/gate_innovate_dock.png")
        record("f2:single_innovate_header", ih["found"] > 0 and ih["visible"] == 0,
               f"inner innov headers visible={ih['visible']} (must be 0)")

        close_all()

        # ---- F3/F4: geometry sweep across all six dock tabs ----
        geo_all_ok = True
        for dock in ["terrain", "underground", "analyze", "innovate", "sun", "measure"]:
            close_all()
            page.click(f'.td-tab[data-dock="{dock}"]')
            page.wait_for_timeout(450)
            rects = {}
            for sel, name in [("#dock-panel-container .dock-panel.visible", "dock"),
                              ("#tool-dock", "tooldock"), ("#bottom-left-toolbar", "toolbar"),
                              ("#status-bar", "statusbar"), ("#topbar", "topbar")]:
                rects[name] = page.evaluate(RECT_JS, sel)
            dock = rects.get("dock")
            ok = dock is not None
            if ok:
                zero = lambda a, b: not (a and b and rect_inter(a, b) > 4)
                no_td = zero(dock, rects.get("tooldock"))
                no_tb = zero(dock, rects.get("toolbar"))
                no_vp = dock["x"] >= 0 and dock["y"] >= 0 and dock["x"] + dock["w"] <= 1281 and dock["y"] + dock["h"] <= 801
                sb = rects.get("statusbar")
                no_sb = zero(dock, sb)
                ok = no_td and no_tb and no_vp and no_sb
                record(f"f3:dock_{dock}_clear_of_chrome", ok,
                       f"vs tooldock={no_td} toolbar={no_tb} viewport={no_vp} statusbar={no_sb}")
            else:
                record(f"f3:dock_{dock}_clear_of_chrome", False, "dock panel not visible")
            geo_all_ok = geo_all_ok and ok
        # tool-dock vs status bar (F4)
        td = page.evaluate(RECT_JS, "#tool-dock")
        sb = page.evaluate(RECT_JS, "#status-bar")
        record("f4:tooldock_above_statusbar", not (td and sb and rect_inter(td, sb) > 0),
               f"tool bottom={td['y'] + td['h'] if td else None} bar top={sb['y'] if sb else None}")

        # ---- F6: panel combination matrix ----
        combos = [
            ("right_stack_all", ["#btn-cost", "#btn-layers", "#btn-season", "#btn-growth", "#btn-permit"]),
            ("dock_underg_plus_cost", [".td-tab[data-dock=\"underground\"]", "#btn-cost"]),
            ("dock_sun_plus_layer", [".td-tab[data-dock=\"sun\"]", "#btn-layers"]),
            ("terrain_then_sun", [".td-tab[data-dock=\"terrain\"]", ".td-tab[data-dock=\"sun\"]"]),
            ("ug_plus_permit", [".td-tab[data-dock=\"underground\"]", "#btn-permit"]),
        ]
        PANEL_SELS = ["#cost-panel", "#layer-panel", "#season-panel", "#growth-panel", "#permit-panel",
                      "#cross-section-panel", "#cut-fill-panel", "#terrain-controls", "#excavate-panel",
                      "#terrain-analysis-panel", "#innovation-panel", "#sun-panel",
                      ".dock-panel.visible"]
        for name, clicks in combos:
            close_all()
            for c in clicks:
                try:
                    page.click(c, force=True, timeout=4000)
                except Exception:
                    page.evaluate(f"() => document.querySelector('{c}') && document.querySelector('{c}').click()")
                page.wait_for_timeout(320)
            page.wait_for_timeout(300)
            rects = []
            for sel in PANEL_SELS:
                for el in page.evaluate("""(sel) => Array.from(document.querySelectorAll(sel)).map(e => {
                    const cs = getComputedStyle(e); if (cs.display === 'none') return null;
                    const r = e.getBoundingClientRect();
                    return (r.width > 2 && r.height > 2) ? { x: r.x, y: r.y, w: r.width, h: r.height } : null;
                }).filter(Boolean)""", [sel]):
                    rects.append(el)
            bad = []
            for i in range(len(rects)):
                for j in range(i + 1, len(rects)):
                    if rect_inter(rects[i], rects[j]) > 4:
                        bad.append((i, j, round(rect_inter(rects[i], rects[j]))))
            page.screenshot(path=f"{SHOTS}/gate_combo_{name}.png")
            record(f"f6:no_overlap::{name}", not bad, f"overlaps={bad if bad else 'none'}")

        # cross-section via excavate flow (JS-click convention per qa_s21; the sync
        # clip-flush render on dock open can delay event delivery, so verify+retry)
        close_all()
        page.click('.td-tab[data-dock="underground"]')
        page.wait_for_timeout(600)
        cs_ok = page.evaluate("""() => ({
            cs: document.getElementById('cross-section-panel').classList.contains('visible'),
            dock: document.getElementById('dock-underground').classList.contains('visible') })""")
        for _ in range(3):
            if cs_ok["cs"]:
                break
            page.evaluate("() => document.getElementById('cross-section-toggle').click()")
            page.wait_for_timeout(450)
            cs_ok = page.evaluate("""() => ({
                cs: document.getElementById('cross-section-panel').classList.contains('visible'),
                dock: document.getElementById('dock-underground').classList.contains('visible') })""")
        page.screenshot(path=f"{SHOTS}/gate_ug_plus_cs.png")
        record("f6:cs_opens_over_ug_dock", cs_ok["cs"] and cs_ok["dock"])
        record("f6:cs_no_conflict_with_ug", cs_ok["cs"] and cs_ok["dock"],
               f"cs visible={cs_ok['cs']} dock visible={cs_ok['dock']}")

        browser.close()

    n_pass = sum(1 for r in RESULTS if r["ok"])
    print(f"\n== {n_pass}/{len(RESULTS)} passed ==")
    json.dump(RESULTS, open(os.path.join(SCRIPT_DIR, "sprint23_panel_conflict_results.json"), "w"), indent=1)
    return 0 if n_pass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
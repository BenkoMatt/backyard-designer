#!/usr/bin/env python3
"""Sprint 23 Hunt A #5b — bottom-left toolbar launcher buttons vs legacy shells.

Hypothesis from code: after the Sprint 13 dock migration, #sun-btn,
#terrain-analysis-btn and #innovation-btn still toggle legacy panels that CSS
line ~"legacy toolbar" force-hides (display:none !important) AND whose
children were moved into dock panels — while #excavate-btn WAS updated to
drive its dock. Verify live: click each launcher, then check whether ANY
visible UI appears (button active state, legacy panel computed display,
matching dock visibility).

Real input: locator clicks only. evaluate = observation.
"""
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, "/root/backyard-designer")
from s23a_common import (RESULTS, dump, load_app, make_page, record, shot,
                         summary_and_exit, to_advanced)

LAUNCHERS = [
    ("sun", "#sun-btn", "#sun-panel", 'dock-sun'),
    ("analysis", "#terrain-analysis-btn", "#terrain-analysis-panel", 'dock-analyze'),
    ("innovate", "#innovation-btn", "#innovation-panel", 'dock-innovate'),
    ("excavate", "#excavate-btn", "#excavate-panel", 'dock-underground'),
]


def ui_snapshot(page, dock_selector):
    return page.evaluate("""([dockSel]) => ({
        legacyVisible: (function(){
            const ids=['sun-panel','terrain-analysis-panel','innovation-panel','excavate-panel'];
            for (const id of ids){ const el=document.getElementById(id);
                if (el && el.classList.contains('visible') && getComputedStyle(el).display!=='none') return id; }
            return null; })(),
        dockVisible: (function(sel){ const el=document.querySelector(sel);
            return !!(el && el.classList.contains('visible')); })(dockSel),
        anyVisibleNewUI: (function(){
            const dock=document.querySelector('.dock-panel.visible');
            const floating=['cost-panel','layer-panel','cross-section-panel','cut-fill-panel'];
            const fp=floating.some(id=>{const el=document.getElementById(id);
                return el && el.classList.contains('visible') && getComputedStyle(el).display!=='none';});
            return { dock: !!dock, dockId: dock?dock.id:null, floating: fp }; })(),
    })""", [dock_selector])


def main():
    with sync_playwright() as p:
        browser, page, errs = make_page(p)
        load_app(page)
        to_advanced(page)  # several launcher buttons/tabs are advanced-only

        for name, btn_sel, _legacy, dock_sel in LAUNCHERS:
            btn = page.locator(btn_sel)
            if btn.count() == 0 or not btn.is_visible():
                record(f"{name}_btn_present", False, f"{btn_sel} missing/hidden")
                continue
            btn.click()
            page.wait_for_timeout(600)
            snap = ui_snapshot(page, f"#{dock_sel}")
            btn_active = page.evaluate(
                """(sel) => document.querySelector(sel).classList.contains('active')""",
                btn_sel)
            record(f"{name}_btn_click_opens_something",
                   snap["dockVisible"] or snap["legacyVisible"] or snap["anyVisibleNewUI"]["floating"],
                   f"snap={snap} btnActive={btn_active}")
            # reset: toggle back off for next iteration
            if btn_active:
                btn.click()
                page.wait_for_timeout(400)

        # --- 2nd path: the DOCK TABS work (feature exists, launcher is broken) ---
        for name, dock_tab, dock_sel in [("sun", "sun", "dock-sun"),
                                         ("analysis", "analyze", "dock-analyze"),
                                         ("innovate", "innovate", "dock-innovate")]:
            tab = page.locator(f'.td-tab[data-dock="{dock_tab}"]')
            if tab.count() == 0:
                record(f"{name}_docktab_opens_dock", False, "tab missing")
                continue
            tab.click()
            page.wait_for_timeout(600)
            vis = page.evaluate(
                f"() => document.getElementById('{dock_sel}').classList.contains('visible')")
            record(f"{name}_docktab_opens_dock", vis, f"dock {dock_sel} visible={vis}")
            # close again for a clean slate
            close = page.locator(f"#{dock_sel} button.close[data-dock-close]")
            if close.count() > 0:
                close.first.click()
                page.wait_for_timeout(300)

        # ================= Cross-section panel (real toggles) =================
        # #cross-section-toggle lives in the excavate panel content, which was
        # moved into dock-underground — open that dock first (real click on the
        # working excavate launcher).
        page.locator("#excavate-btn").click()
        page.wait_for_timeout(600)
        cs = page.locator("#cross-section-toggle")
        record("cross_section_toggle_present", cs.count() == 1 and cs.is_visible())
        cs.click()
        page.wait_for_timeout(600)
        st = page.evaluate("""() => ({
            pressed: document.getElementById('cross-section-toggle').getAttribute('aria-pressed'),
            panelVisible: (function(){ const el=document.getElementById('cross-section-panel');
                return el.classList.contains('visible') && getComputedStyle(el).display!=='none'; })(),
            canvas: !!document.getElementById('cross-section-canvas'),
        })""")
        record("cross_section_opens_visible_panel",
               st["pressed"] == "true" and st["panelVisible"], f"state={st}")
        page.screenshot(path="/tmp/s23a_6_crosssection.png")
        cs.click()
        page.wait_for_timeout(400)
        st2 = page.evaluate("""() => ({
            pressed: document.getElementById('cross-section-toggle').getAttribute('aria-pressed'),
            panelVisible: (function(){ const el=document.getElementById('cross-section-panel');
                return el.classList.contains('visible') && getComputedStyle(el).display!=='none'; })(),
        })""")
        record("cross_section_toggles_off",
               st2["pressed"] == "false" and not st2["panelVisible"], f"state={st2}")

        shot(page, 7)
        record("console:no_page_errors", not errs, "; ".join(errs[:3]))
        browser.close()
    return summary_and_exit()


if __name__ == "__main__":
    sys.exit(main())
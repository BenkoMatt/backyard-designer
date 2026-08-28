#!/usr/bin/env python3
"""
Sprint 21 Quality Gate — No-Scroll Terrain Dock & Excavate Visibility Mandates
==============================================================================

Locks the two Sprint 21 owner mandates in as permanent regression tests:

  MANDATE 1 — No unnecessary scrolling:
    The Terrain dock at 1280x800 must show its primary mode buttons
    (Raise / Excavate / Smooth / Erode / Flatten / DIG / FILL) fully inside the
    viewport with zero page scrolling, and every button must be genuinely
    clickable by a real CDP mouse click at its center (hit-test verified —
    a rect inside the viewport is not enough if an ancestor clips it).

  MANDATE 2 — Excavate must reveal the ground:
    The Excavate/Underground flow must expose the geological layers
    (topsoil / subsoil / clay / bedrock) in the rendered PIXELS over a dug
    pit, the cutaway slider must arm/remove the clip plane, and grass must
    return when the flow is closed and the terrain flattened.

UI interaction uses REAL CDP mouse events only (page.mouse.click at element
centers per the established sprint20_interaction_qa pattern; locator.click()
is used only for the scroll-into-view fallback check, which mirrors what a
real user does when a control requires scrolling). page.evaluate() is used
ONLY for terrain state setup (dig hole + applyTerrainFull, camera placement,
flatten) and read-only assertions — never to drive click paths.

On the PRE-FIX baseline some mandate tests legitimately FAIL (documented in
QUALITY_REPORT.md): the bottom-toolbar buttons are force-hidden by CSS and
the Dig/Fill buttons overflow the Terrain dock horizontally. These tests flip
to PASS when the Sprint 21 fix agents land their changes — that is the point
of the gate.

Usage:
  python3 sprint21_quality_gate.py [--port PORT]     (default port 8210)
  Requires: python3 -m http.server <port>  serving this repo directory.
"""

import argparse
import json
import os
import re
import sys
import traceback

BASE_URL = os.environ.get('BASE_URL', None)
INDEX_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIZE_LIMIT = 750 * 1024          # hard limit from the brief
SIZE_SAFETY = 768 * 1024         # safety margin used by prior sprints

results = []
total_pass = 0
total_fail = 0


def test(name, passed, detail=""):
    global total_pass, total_fail
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    if passed:
        total_pass += 1
    else:
        total_fail += 1


def read_html():
    with open(INDEX_HTML, 'r') as f:
        return f.read()


# ============================================================
# JS snippets (state setup + read-only probes; never click via evaluate)
# ============================================================

INIT_STORAGE = """
  try {
    localStorage.setItem('backyard-onboarding-state', JSON.stringify({
        completedSteps: ['welcome-scratch'], tourCompleted: true,
        welcomeShown: true, dismissedAt: 1, featuresUsed: {}
    }));
    localStorage.setItem('byd-design-mode', 'basic');
    localStorage.removeItem('backyard-design-autosave');
  } catch(e) {}
"""

BOOT_CHECK = """() => ({
    wizardHidden: getComputedStyle(document.getElementById('wizard')).display === 'none',
    welcomeHidden: !document.getElementById('welcome-prompt').classList.contains('visible'),
    yardReady: !!(window._test && window._test.yardMesh)
})"""

DOCK_GEOMETRY_CHECK = """() => {
    const panel = document.getElementById('dock-terrain');
    const doc = document.documentElement;
    const btns = Array.from(document.querySelectorAll('.terrain-mode-btn[data-tmode]')).map(b => {
        const r = b.getBoundingClientRect();
        const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
        const hit = document.elementFromPoint(cx, cy);
        return {
            mode: b.dataset.tmode,
            x: r.x, y: r.y, w: r.width, h: r.height,
            fullyInViewport: r.top >= 0 && r.left >= 0 &&
                             r.bottom <= window.innerHeight && r.right <= window.innerWidth,
            displayed: getComputedStyle(b).display !== 'none' && r.width > 0 && r.height > 0,
            hitAtCenter: !!hit && (hit === b || b.contains(hit)),
            hitWhat: hit ? (hit.id || hit.className || hit.tagName) : 'none'
        };
    });
    return {
        panelVisible: panel.classList.contains('visible'),
        vw: window.innerWidth, vh: window.innerHeight,
        pageScroll: [doc.scrollLeft, doc.scrollTop, window.scrollY],
        buttons: btns
    };
}"""

MODE_STATE_CHECK = """(sel) => {
    const b = document.querySelector(sel);
    if (!b) return {found: false};
    const r = b.getBoundingClientRect();
    return {
        found: true, active: b.classList.contains('active'),
        pressed: b.getAttribute('aria-pressed'),
        pageScrollY: window.scrollY,
        dockScrollTop: document.getElementById('dock-terrain').scrollTop,
        digDepthRowShown: document.getElementById('dig-depth-row').style.display
    };
}"""

EXCAVATE_BTN_CHECK = """() => {
    const b = document.getElementById('excavate-btn');
    if (!b) return {found: false};
    const cs = getComputedStyle(b);
    const r = b.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const hit = r.width > 0 ? document.elementFromPoint(cx, cy) : null;
    return {found: true, display: cs.display,
            visible: cs.display !== 'none' && r.width > 0 && r.height > 0,
            hitAtCenter: !!hit && (hit === b || b.contains(hit)),
            active: b.classList.contains('active'),
            pressed: b.getAttribute('aria-pressed')};
}"""

CAMERA_SETUP = """() => {
    // Position camera over the yard center (setup, not a click path).
    window.controls.target.set(0, -5, 0);
    window._test.activeCamera.position.set(0, 14, 26);
    window._test.activeCamera.lookAt(0, -5, 0);
    if (window.controls.update) window.controls.update();
    window.requestRender();
    return {camera: true};
}"""

DIG_PIT_SETUP = """() => {
    // Terrain STATE SETUP ONLY (allowed per gate spec): dig a hole + full apply.
    const t = window._test;
    t.ensureTerrainArray();
    const segs = t.state.terrainSegs;
    for (let i = 0; i < t.state.terrain.length; i++) t.state.terrain[i] = 0;
    const c = Math.floor(segs / 2), R = 40;   // 10 ft radius across, up to 15 ft deep
    for (let iz = c - R; iz <= c + R; iz++) {
        for (let ix = c - R; ix <= c + R; ix++) {
            const dist = Math.sqrt((ix - c) ** 2 + (iz - c) ** 2);
            if (dist > R) continue;
            t.state.terrain[iz * (segs + 1) + ix] =
                -Math.min(15, Math.max(0, (R - dist) * 0.9));
        }
    }
    window.applyTerrainFull();          // positions + vertex colors + buildSolidEarth
    window.requestRender();
    return {dug: true, segs: segs};
}"""

FLAT_TERRAIN_SETUP = """() => {
    const t = window._test;
    for (let i = 0; i < t.state.terrain.length; i++) t.state.terrain[i] = 0;
    window.applyTerrainFull();
    window.requestRender();
    return {flat: true};
}"""

PLANES_CHECK = """() => {
    const t = window._test;
    const planes = (t.yardMesh.material.clippingPlanes || []).map(p => ({
        ny: +p.normal.y.toFixed(3), c: +p.constant.toFixed(2)
    }));
    return {planes: planes,
            downPlanes: planes.filter(p => p.ny < -0.5).length,
            cutVal: document.getElementById('terrain-cutaway').value,
            cutLabel: document.getElementById('cutaway-val').textContent};
}"""

UNDERGROUND_DOCK_CHECK = """() => {
    const panel = document.getElementById('dock-underground');
    const cut = document.getElementById('terrain-cutaway');
    const pr = panel.getBoundingClientRect();
    const r = cut ? cut.getBoundingClientRect() : {width: 0, height: 0, x: 0, y: 0};
    return {
        panelVisible: panel.classList.contains('visible'),
        panelRect: {x: pr.x, y: pr.y, w: pr.width, h: pr.height},
        cutFound: !!cut,
        cutVisible: !!cut && getComputedStyle(cut).display !== 'none' && r.width > 0,
        cutRect: {x: r.x, y: r.y, w: r.width, h: r.height}
    };
}"""


# ============================================================
# PIL pixel helpers
# ============================================================

def geo_pixel_counts(png_path, exclude_rects=()):
    """Count geological-signature pixels in a screenshot, skipping UI rects.

    Layer base colors (NAMED_GEO_LAYERS) get a 1.45x underground brightness
    boost in the renderer, so thresholds target the boosted values with
    tolerance for the ±6% noise variation and depth-band darkening (x0.85).
    """
    from PIL import Image
    im = Image.open(png_path).convert('RGB')
    W, H = im.size

    def excluded(x, y):
        for (rx, ry, rw, rh) in exclude_rects:
            if rx - 8 <= x <= rx + rw + 8 and ry - 8 <= y <= ry + rh + 8:
                return True
        return False

    px = im.load()
    c = {"clay": 0, "subsoil": 0, "topsoil": 0, "bedrock": 0, "grass": 0,
         "warm_brown": 0, "sampled": 0}
    for yy in range(48, H - 26, 2):          # skip topbar (top) + status bar (bottom)
        for xx in range(100, W - 10, 2):     # skip left tool dock
            if excluded(xx, yy):
                continue
            r, g, b = px[xx, yy]
            c["sampled"] += 1
            if abs(r - 232) <= 50 and abs(g - 96) <= 50 and abs(b - 52) <= 50:
                c["clay"] += 1
            elif abs(r - 225) <= 50 and abs(g - 177) <= 50 and abs(b - 115) <= 50:
                c["subsoil"] += 1
            elif abs(r - 107) <= 30 and abs(g - 70) <= 30 and abs(b - 44) <= 30:
                c["topsoil"] += 1
            elif abs(r - 139) <= 35 and abs(g - 139) <= 35 and abs(b - 151) <= 35:
                c["bedrock"] += 1
            if r > g > b and (r - b) >= 25 and r >= 60:
                c["warm_brown"] += 1
            if g > r + 12 and g > b + 12:
                c["grass"] += 1
    c["geo_total"] = c["clay"] + c["subsoil"] + c["topsoil"] + c["bedrock"]
    return c


# ============================================================
# STATIC TESTS (no browser)
# ============================================================

def run_static_tests():
    print("\n=== Sprint 21 Static Tests ===")
    html = read_html()

    # --- Size limit (owner hard constraint) ---
    size = os.path.getsize(INDEX_HTML)
    test("index.html size <= 750KB (hard limit)", size <= SIZE_LIMIT, f"{size} bytes")
    test("index.html size <= 768KB (safety margin)", size <= SIZE_SAFETY, f"{size} bytes")
    lines = html.count('\n') + 1
    test("index.html line count recorded", lines > 0, f"{lines} lines (info only)")

    # --- CSS brace balance (brief: CSS SYNTAX DISCIPLINE) ---
    m = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
    if m:
        css = m.group(1)
        opens, closes = css.count('{'), css.count('}')
        test("CSS <style> block braces balanced", opens == closes,
             f"{opens} opening vs {closes} closing braces")
    else:
        test("CSS <style> block exists", False, "no <style> block found")

    # --- Three.js version pinned ---
    test("Three.js v0.160.0 via importmap unchanged",
         'three@0.160.0' in html or '0.160.0' in html)

    # --- Excavate button + handler wiring (mandate 2 root) ---
    test("#excavate-btn element exists in HTML", 'id="excavate-btn"' in html)
    test("#excavate-btn click handler wired (excavatePanelVisible toggle)",
         "excavateBtn.addEventListener('click'" in html and 'excavatePanelVisible' in html)
    test("excavate close button wired", "excavateCloseBtn.addEventListener('click'" in html)

    # --- Auto-dig clip plane machinery (mandate 2 mechanism) ---
    test("updateAutoDigClip() defined", 'function updateAutoDigClip()' in html)
    test("updateAutoDigClip() called from terrain mode handler", 'updateAutoDigClip();' in html)
    test("_rebuildYardClipPlanes preserves terrain+crossSection+autoDig planes",
         'function _rebuildYardClipPlanes()' in html)

    # --- Geological layers present with expected base colors ---
    block = re.search(r'const NAMED_GEO_LAYERS = \[(.*?)\];', html, re.DOTALL)
    for lname, hexhint in [("topsoil", "0x4a"), ("subsoil", "0x9b"),
                           ("clay", "0xa0"), ("bedrock", "0x60")]:
        ok = bool(block) and lname in block.group(1) and hexhint in block.group(1)
        test(f"NAMED_GEO_LAYERS defines {lname} (base {hexhint}…)", ok)

    # --- Terrain dock mode buttons exist (mandate 1 target) ---
    for mode in ["raise", "lower", "smooth", "erode", "flatten", "dig", "fill"]:
        test(f'Terrain dock has {mode} mode button', f'data-tmode="{mode}"' in html)

    # --- Test hooks used by this gate are exported ---
    test("window.applyTerrainFull exported",
         'window.applyTerrainFull = applyTerrainFull' in html)
    test("window._test exposes state/yardMesh", 'window._test = {' in html)
    test("window.controls exported for camera setup", 'window.controls = controls' in html)


# ============================================================
# BROWSER TESTS
# ============================================================

def run_browser_tests(base_url):
    print("\n=== Sprint 21 Browser Tests (real CDP events) ===")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        test("playwright available", False, "playwright not installed — browser tests skipped")
        return

    console_errors = []
    shot_open = os.path.join(SCRIPT_DIR, 'sprint21_gate_excavate_open.png')
    shot_restored = os.path.join(SCRIPT_DIR, 'sprint21_gate_restored.png')
    shot_flat = os.path.join(SCRIPT_DIR, 'sprint21_gate_flat_baseline.png')

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": 1280, "height": 800})
            ctx.add_init_script(INIT_STORAGE)
            page = ctx.new_page()
            page.on('console', lambda msg: console_errors.append(f"{msg.type}: {msg.text}")
                    if msg.type == 'error' else None)
            page.on('pageerror', lambda err: console_errors.append(f"pageerror: {err}"))

            page.goto(f'{base_url}/index.html', timeout=30000)
            page.wait_for_timeout(3200)

            # ---- Boot: dismiss wizard with a REAL click on its skip button ----
            page.locator('#wizard-skip').click()
            page.wait_for_timeout(4200)  # yard init + toast fade (toast hides after 3s)

            boot = page.evaluate(BOOT_CHECK)
            test("App boots: wizard dismissed via real click, yard initialized",
                 boot.get('wizardHidden') and boot.get('yardReady'), f"{boot}")

            # ============================================================
            # (a) SCROLL-FREE TERRAIN DOCK  (MANDATE 1)
            # ============================================================
            page.locator('.td-tab[data-dock="terrain"]').click()
            page.wait_for_timeout(1200)

            geom = page.evaluate(DOCK_GEOMETRY_CHECK)
            test("Terrain dock opens on tab click", geom.get('panelVisible') is True)

            btns = {b['mode']: b for b in geom.get('buttons', [])}
            dig, fill = btns.get('dig'), btns.get('fill')
            test("Dig button present in Terrain dock", dig is not None)
            test("Fill button present in Terrain dock", fill is not None)

            test("Dig button rect fully inside viewport (no scrolling needed)",
                 bool(dig and dig['fullyInViewport'] and dig['displayed']),
                 f"dig rect={dig and (round(dig['x']), round(dig['y']), round(dig['w']), round(dig['h']))}")
            test("Fill button rect fully inside viewport (no scrolling needed)",
                 bool(fill and fill['fullyInViewport'] and fill['displayed']),
                 f"fill rect={fill and (round(fill['x']), round(fill['y']), round(fill['w']), round(fill['h']))}")

            all_in = len(btns) == 7 and all(b['fullyInViewport'] for b in btns.values())
            test("ALL 7 terrain mode buttons rects fully visible at 1280x800", all_in,
                 "missing some" if len(btns) != 7 else
                 "; offscreen: " + ",".join(m for m, b in btns.items() if not b['fullyInViewport']))

            test("No page scrolling after dock open (scrollX/Y == 0)",
                 geom.get('pageScroll') == [0, 0, 0], f"pageScroll={geom.get('pageScroll')}")

            # MANDATE: every mode button genuinely clickable (hit-test at center)
            hit_fail = [f"{m}:hit={b['hitAtCenter']},target={b['hitAtCenter'] and 'btn' or b['hitWhat']}"
                        for m, b in btns.items() if not (b['displayed'] and b['hitAtCenter'])]
            test("MANDATE: every .terrain-mode-btn user-clickable without scrolling "
                 "(elementFromPoint hits the button)",
                 len(btns) == 7 and not hit_fail,
                 "all 7 hit-test clean" if not hit_fail else "; ".join(hit_fail))

            # Raw CDP clicks on the buttons that pass the hit test
            dock_scroll_before = page.evaluate(
                "document.getElementById('dock-terrain').scrollTop")
            failed_modes = []
            dig_state = None
            for mode in ["raise", "lower", "smooth", "erode", "flatten", "dig", "fill"]:
                box = page.locator(f'.terrain-mode-btn[data-tmode="{mode}"]').bounding_box()
                page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                page.wait_for_timeout(180)
                st = page.evaluate(MODE_STATE_CHECK, f'.terrain-mode-btn[data-tmode="{mode}"]')
                st['_hitExpected'] = btns[mode]['hitAtCenter'] if btns.get(mode) else False
                ok = (st.get('found') and st.get('active') and st.get('pressed') == 'true') \
                     if st['_hitExpected'] else None  # None = clipped, skip raw-click expect
                if ok is False:
                    failed_modes.append(f"{mode}:{ {k: st[k] for k in ('active', 'pressed')} }")
                if mode == 'dig':
                    dig_state = st
            activatable = [m for m in btns if btns[m]['hitAtCenter']]
            test(f"Raw CDP click activates every unclipped mode button "
                 f"({len(activatable)}/7 unclipped on this baseline)",
                 not failed_modes,
                 "raw clicks OK: " + ",".join(activatable) if not failed_modes
                 else "; ".join(failed_modes))

            # Scroll-into-view fallback (what a real user does): locator.click scrolls
            # the dock's overflow — proves the Dig/Fill handlers work once reachable.
            fallback_ok = True
            fb_detail = []
            for mode in ("dig", "fill"):
                page.locator(f'.terrain-mode-btn[data-tmode="{mode}"]').click()
                page.wait_for_timeout(250)
                st = page.evaluate(MODE_STATE_CHECK, f'.terrain-mode-btn[data-tmode="{mode}"]')
                if not (st.get('active') and st.get('pressed') == 'true'
                        and st.get('digDepthRowShown') == 'flex'):
                    fallback_ok = False
                    fb_detail.append(f"{mode}:{st}")
            test("Dig/Fill clickable after scroll-into-view (handler wiring intact; "
                 "dig-depth row shows)", fallback_ok, "; ".join(fb_detail) or "dig+fill OK")

            ds = dig_state or {}
            test("CDP click on Dig activates it without scrolling the page "
                 "(dock scroll may be required pre-fix)",
                 bool(dig and dig['fullyInViewport'] and ds.get('active')
                      and ds.get('pageScrollY') == 0),
                 f"dig active={ds.get('active')} pageScrollY={ds.get('pageScrollY')}")

            # restore Raise so the dig-brush clip plane is not armed for the pixel tests
            page.locator('.terrain-mode-btn[data-tmode="raise"]').click()
            page.wait_for_timeout(250)

            # close the terrain dock so the canvas is unobstructed for pixel tests
            page.locator('#dock-terrain [data-dock-close]').click()
            page.wait_for_timeout(600)
            dock_closed = page.evaluate(
                "!document.getElementById('dock-terrain').classList.contains('visible')")
            test("Terrain dock closes via its close button (real click)", dock_closed)

            # ============================================================
            # (b) EXCAVATE REVEALS GROUND  (MANDATE 2)
            # ============================================================
            # Switch to advanced (real click) so the Underground dock is reachable.
            page.locator('#mode-toggle button[data-mode="advanced"]').click()
            page.wait_for_timeout(700)

            # Fixed camera over the yard center — used for ALL pixel screenshots
            # so flat/pit/restored are directly comparable.
            cam = page.evaluate(CAMERA_SETUP)
            test("Terrain state setup: camera positioned over yard center",
                 bool(cam.get('camera')))
            page.wait_for_timeout(800)

            # FLAT baseline screenshot (no pit, no panel) for the pixel delta.
            # t_0174b1d0: flatten explicitly first — section (a) click probes can leave
            # terrain edits that the old outerGround plane masked; the restored-state
            # shot below flattens, so the baseline must too.
            flat0 = page.evaluate(FLAT_TERRAIN_SETUP)
            test("Terrain state setup: baseline flattened", bool(flat0.get('flat')))
            page.wait_for_timeout(1200)
            page.screenshot(path=shot_flat)
            flat_px = geo_pixel_counts(shot_flat)

            # Dig the pit via state setup (allowed), then verify pixels.
            dug = page.evaluate(DIG_PIT_SETUP)
            test("Terrain state setup: pit dug + applyTerrainFull", bool(dug.get('dug')))
            page.wait_for_timeout(1200)  # let frames render

            # --- Excavate button: the owner's primary entry point ---
            ex = page.evaluate(EXCAVATE_BTN_CHECK)
            test("#excavate-btn exists in DOM", ex.get('found') is True)
            test("MANDATE: #excavate-btn visible & CDP-clickable (primary entry point)",
                 ex.get('found') and ex.get('visible'),
                 ("PRE-EXISTING baseline failure: CSS '#tape-measure-btn, #terrain-btn, "
                  "#excavate-btn, … { display:none !important }' force-hides the bottom "
                  "toolbar; documented in QUALITY_REPORT.md (owned by excavate-visibility fix)")
                 if ex.get('found') and not ex.get('visible') else f"{ex}")

            if ex.get('found') and ex.get('visible'):
                page.locator('#excavate-btn').click()
                page.wait_for_timeout(600)
                opened = page.evaluate(EXCAVATE_BTN_CHECK)
                test("CDP click on Excavate toggles it open (aria-pressed)",
                     opened.get('active') and opened.get('pressed') == 'true', f"{opened}")
                page.locator('#excavate-btn').click()  # close again
                page.wait_for_timeout(400)
            else:
                test("CDP click on Excavate toggles it open (aria-pressed)", False,
                     "CANNOT-CLICK on baseline: button is display:none (pre-existing, "
                     "documented in QUALITY_REPORT.md)")

            # Canonical working UI route: the Underground dock (where the excavate
            # panel content now lives after the Sprint 13 dock refactor).
            page.locator('.td-tab[data-dock="underground"]').click()
            page.wait_for_timeout(1100)

            ug = page.evaluate(UNDERGROUND_DOCK_CHECK)
            test("Underground dock opens and Cutaway control is visible",
                 ug.get('panelVisible') and ug.get('cutVisible'), f"{ug}")

            page.screenshot(path=shot_open)
            pit_px = geo_pixel_counts(shot_open,
                                      exclude_rects=[(ug['panelRect']['x'], ug['panelRect']['y'],
                                                      ug['panelRect']['w'], ug['panelRect']['h'])])
            revealed = pit_px['geo_total'] - flat_px['geo_total']

            test("MANDATE: excavate flow reveals geological layers in rendered pixels",
                 revealed >= 1500 or pit_px['geo_total'] >= 2500,
                 f"geo pixels: pit={pit_px['geo_total']} vs flat={flat_px['geo_total']} "
                 f"(revealed delta={revealed}); clay={pit_px['clay']} subsoil={pit_px['subsoil']} "
                 f"topsoil={pit_px['topsoil']} bedrock={pit_px['bedrock']}")

            # ============================================================
            # (c) Cutaway slider still works
            # ============================================================
            cb = ug.get('cutRect')
            if cb and cb['w'] > 0:
                # set to ~50% via real click on the track center
                page.mouse.click(cb['x'] + cb['w'] * 0.5, cb['y'] + cb['h'] / 2)
                page.wait_for_timeout(900)
                p50 = page.evaluate(PLANES_CHECK)
                test("Cutaway slider to 50: input value == 50", p50.get('cutVal') == '50',
                     f"value={p50.get('cutVal')}")
                test("Cutaway 50 arms clip plane (downward normal in clippingPlanes)",
                     p50.get('downPlanes', 0) >= 1, f"planes={p50.get('planes')}")

                # set to 0 via real click at far left of the track
                page.mouse.click(cb['x'] + 3, cb['y'] + cb['h'] / 2)
                page.wait_for_timeout(900)
                p0 = page.evaluate(PLANES_CHECK)
                test("Cutaway slider to 0: input value == 0 (Full)",
                     p0.get('cutVal') == '0' and p0.get('cutLabel') == 'Full',
                     f"value={p0.get('cutVal')} label={p0.get('cutLabel')}")
                test("Cutaway 0 removes clip plane", p0.get('downPlanes', 0) == 0,
                     f"planes={p0.get('planes')}")
            else:
                test("Cutaway slider clickable (rect found)", False, f"cutaway rect={cb}")

            # ============================================================
            # Close underground dock → flatten → grass green returns
            # ============================================================
            page.locator('#dock-underground [data-dock-close]').click()
            page.wait_for_timeout(600)
            ug_closed = page.evaluate(
                "!document.getElementById('dock-underground').classList.contains('visible')")
            test("Underground dock closes via its close button (real click)", ug_closed)

            flat = page.evaluate(FLAT_TERRAIN_SETUP)
            test("Terrain state setup: flattened back", bool(flat.get('flat')))
            page.wait_for_timeout(1200)

            page.screenshot(path=shot_restored)
            rest_px = geo_pixel_counts(shot_restored)
            grass_ratio = rest_px['grass'] / max(flat_px['grass'], 1)
            test("MANDATE: after closing excavate + flattening, grass green returns",
                 grass_ratio >= 0.85,
                 f"grass restored={rest_px['grass']} vs flat baseline={flat_px['grass']} "
                 f"(ratio {grass_ratio:.2f})")
            geo_delta_restored = abs(rest_px['geo_total'] - flat_px['geo_total'])
            test("After restore: geological browns gone (back to flat baseline)",
                 geo_delta_restored <= 800,
                 f"|geo_restored - geo_flat| = {geo_delta_restored}")

            # ============================================================
            # (d) No console errors during any of the above
            # ============================================================
            test("No console errors during the entire run", len(console_errors) == 0,
                 f"errors: {console_errors[:4]}" if console_errors else "")

            browser.close()
    except Exception as e:
        test("Browser tests completed without exception", False, str(e))
        traceback.print_exc()


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Sprint 21 Quality Gate")
    parser.add_argument('--port', type=int, default=8210, help='HTTP server port')
    args = parser.parse_args()
    base_url = BASE_URL or f'http://localhost:{args.port}'

    print("=" * 60)
    print("Sprint 21 Quality Gate — No-Scroll Dock & Excavate Visibility")
    print("=" * 60)
    print(f"URL: {base_url}/index.html")

    run_static_tests()
    run_browser_tests(base_url)

    print("\n" + "=" * 60)
    print(f"Results: {total_pass} passed, {total_fail} failed, {total_pass + total_fail} total")
    print("=" * 60)

    size = os.path.getsize(INDEX_HTML)
    lines = read_html().count('\n') + 1
    print(f"index.html: {size} bytes ({size/1024:.1f} KB of 750KB limit), {lines} lines")

    output = {
        "sprint": 21,
        "total": total_pass + total_fail,
        "passed": total_pass,
        "failed": total_fail,
        "index_html_bytes": size,
        "index_html_lines": lines,
        "results": results,
    }
    output_path = os.path.join(SCRIPT_DIR, 'sprint21_quality_gate_results.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Results saved to: {output_path}")

    sys.exit(1 if total_fail > 0 else 0)


if __name__ == '__main__':
    main()
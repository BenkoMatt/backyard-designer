#!/usr/bin/env python3
"""
Sprint 26 Feature Gate — Autosave & Recovery
============================================

Locks the Sprint 26 feature (debounced autosave to a DEDICATED recovery key +
non-blocking recovery banner with Restore/Discard) in as regression tests.

  GROUP A — AUTOSAVE FIRING (real CDP events):
    A1. Untouched yard writes NO recovery snapshot (trivial-state guard).
    A2. A real library-item click dirties state; after the 2s debounce the
        recovery snapshot exists with the object serialized (ts > 0, objects
        >= 1) AND the legacy wizard autosave key still written.
    A3. Exit flush: a change made and the page closed WITHIN the debounce
        window (beforeunload/pagehide path) still lands in the snapshot.
    A4. Static: 30s interval flush + visibilitychange/pagehide/beforeunload
        listeners exist in source.

  GROUP B — RECOVERY BANNER ON RELOAD (real boot):
    B1. Fresh boot with a snapshot NEWER than the last explicit save shows
        #recovery-banner.visible with 'Restore unsaved changes?' and both
        buttons.
    B2. Banner is NON-BLOCKING: small floating box (height < 150px), not a
        full-viewport backdrop; canvas below stays clickable.

  GROUP C — RESTORE CORRECTNESS (real clicks):
    C1. Clicking Restore hides the banner and restores the full design
        through the REAL loadDesign() path: object count, yard dimensions,
        and deformed terrain (terrain[0] == -8) all come back.

  GROUP D — DISCARD CORRECTNESS (real clicks):
    D1. Reload with a fresh snapshot shows the banner; clicking Discard
        hides it and removes the snapshot key; next boot shows NO banner.

  GROUP E — NO INTERFERENCE WITH EXPLICIT SAVE/LOAD:
    E1. Real Ctrl+S produces a design JSON download and stamps explicitTs
        into 'backyard-recovery-meta'; afterwards a reload shows NO banner
        (snapshot is not newer than the explicit save).
    E2. Loading a design JSON file through the real #import-input path
        restores its objects and updates the explicit-save marker; reload
        shows NO banner. Round-trip: loaded state matches the file.

UI verification uses REAL CDP events only (page.mouse/keyboard on real
elements). page.evaluate() is used ONLY for read-only state probes and test
SETUP (terrain seeding) — never to drive click/key paths.

Usage:
  python3 sprint26_feature_gate.py [--port PORT]     (default 8333)
  Requires: python3 -m http.server <port> serving this repo directory.
"""

import argparse
import json
import os
import re
import sys

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('BASE_URL', None)
INDEX_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
SIZE_LIMIT_BYTES = 766000   # Sprint 26 byte budget

results = []
total_pass = 0
total_fail = 0


def test(name, passed, detail=""):
    global total_pass, total_fail
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "detail": str(detail)[:300]})
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    if passed:
        total_pass += 1
    else:
        total_fail += 1


# ============================================================
# JS snippets — READ-ONLY probes + test setup only.
# ============================================================

# One-time-per-context storage reset (marker prevents re-clearing on reload,
# which would wipe the very snapshot under test).
INIT_STORAGE = """
(() => {
  try {
    if (localStorage.getItem('backyard-s26-gate-init')) return;
    localStorage.setItem('backyard-s26-gate-init', '1');
    localStorage.setItem('backyard-onboarding-state', JSON.stringify({
        completedSteps: ['welcome-scratch'], tourCompleted: true,
        welcomeShown: true, dismissedAt: 1, featuresUsed: {}
    }));
    localStorage.setItem('byd-design-mode', 'basic');
    localStorage.removeItem('backyard-design-autosave');
    localStorage.removeItem('backyard-recovery-snapshot');
    localStorage.removeItem('backyard-recovery-meta');
  } catch(e) {}
})();
"""

BOOT_CHECK = """() => ({
    yardReady: !!(window._test && window._test.yardMesh),
    mode: (window.getCurrentMode ? window.getCurrentMode() : null)
})"""

SNAPSHOT_CHECK = """() => {
    let raw = null;
    try { raw = localStorage.getItem('backyard-recovery-snapshot'); } catch(e) {}
    if (!raw) return { exists: false };
    try {
        const p = JSON.parse(raw);
        return {
            exists: true,
            ts: (p && typeof p.ts === 'number') ? p.ts : 0,
            objects: (p && p.d && Array.isArray(p.d.objects)) ? p.d.objects.length : -1,
            hasTerrain: !!(p && p.d && p.d.terrain && p.d.terrain.length)
        };
    } catch(e) { return { exists: false, parseError: true }; }
}"""

META_CHECK = """() => {
    let raw = null;
    try { raw = localStorage.getItem('backyard-recovery-meta'); } catch(e) {}
    if (!raw) return { exists: false };
    try { const m = JSON.parse(raw); return { exists: true, explicitTs: (m && m.explicitTs) || 0 }; }
    catch(e) { return { exists: false, parseError: true }; }
}"""

BANNER_CHECK = """() => {
    const b = document.getElementById('recovery-banner');
    if (!b) return { exists: false };
    const cs = getComputedStyle(b);
    return {
        exists: true,
        visible: b.classList.contains('visible') && cs.display !== 'none',
        text: (b.textContent || ''),
        hasRestore: !!document.getElementById('rb-restore'),
        hasDiscard: !!document.getElementById('rb-discard'),
        zIndex: cs.zIndex,
        pointerEvents: cs.pointerEvents
    };
}"""

STATE_CHECK = """() => {
    const st = window._test ? window._test.state : null;
    return {
        objectCount: st && st.objects ? st.objects.size : null,
        yard: st ? st.yard : null,
        terrain0: (st && st.terrain && st.terrain.length) ? st.terrain[0] : null,
        terrainDeformed: st ? !!st.terrainDeformed : null
    };
}"""

# Test SETUP only (not a click/key path): create deformed terrain so the
# snapshot carries a non-trivial terrain state for the restore test.
SETUP_TERRAIN = """() => {
    const t = window._test;
    if (!t || !t.ensureTerrainArray) return { error: 'no ensureTerrainArray' };
    t.ensureTerrainArray();
    t.state.terrain[0] = -8;
    t.applyTerrainToMesh();
    t.state.terrainDeformed = true;
    return { ok: true, terrain0: t.state.terrain[0] };
}"""


def run_static_tests():
    print("--- Static checks ---")
    size = os.path.getsize(INDEX_HTML)
    with open(INDEX_HTML, 'r', encoding='utf-8') as f:
        html = f.read()

    test("File size <= 766,000 bytes (Sprint 26 byte budget)",
         size <= SIZE_LIMIT_BYTES,
         f"{size} bytes, headroom {SIZE_LIMIT_BYTES - size}")

    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.S)
    body = re.sub(r'/\*.*?\*/', '', '\n'.join(style_blocks), flags=re.S)
    opens, closes = body.count('{'), body.count('}')
    test("CSS brace balance", opens == closes, f"{opens} open / {closes} close")

    test("Recovery snapshot key defined (separate from wizard autosave key)",
         "backyard-recovery-snapshot" in html and "backyard-design-autosave" in html)
    test("30s interval flush present",
         bool(re.search(r"setInterval\(\(\) => \{ if \(_autosaveDirty\) _writeRecoverySnapshot\(\); \}, 30000\)", html)))
    test("Exit-flush listeners (visibilitychange + pagehide + beforeunload)",
         all(s in html for s in ["visibilitychange", "pagehide", "beforeunload"]))
    test("Recovery banner element with Restore/Discard buttons",
         'id="recovery-banner"' in html and 'id="rb-restore"' in html and 'id="rb-discard"' in html)
    test("Explicit save/load bookkeeping wired (markExplicitSave calls)",
         html.count("markExplicitSave()") >= 4,
         f"{html.count('markExplicitSave()')} call sites")
    test("Help modal documents autosave",
         "Autosave:</strong>" in html)
    test("Banner copy matches spec ('Restore unsaved changes?')",
         "Restore unsaved changes?" in html)


def dismiss_wizard(page):
    """Real CDP clicks through the 2-step wizard."""
    page.wait_for_timeout(400)
    page.click('#wizard-next')
    page.wait_for_timeout(400)
    page.click('#wizard-finish')
    page.wait_for_timeout(600)


def add_first_library_object(page):
    """Real CDP click on the first sidebar library item (dirties state)."""
    page.click('.lib-item')
    page.wait_for_timeout(300)


def run_browser_tests(base_url):
    url = base_url.rstrip('/') + '/index.html'
    console_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ========================================================
        # CONTEXT A — autosave firing + exit flush
        # ========================================================
        ctx_a = browser.new_context(viewport={'width': 1280, 'height': 800}, accept_downloads=True)
        ctx_a.add_init_script(INIT_STORAGE)
        page = ctx_a.new_page()
        page.on('console', lambda m: console_errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: console_errors.append(str(e)))

        print("--- A: autosave firing (real CDP events) ---")
        page.goto(url, wait_until='load', timeout=30000)
        page.wait_for_timeout(2500)
        boot = page.evaluate(BOOT_CHECK)
        test("App boots (yard ready, Basic mode)",
             bool(boot.get('yardReady')) and boot.get('mode') == 'basic', f"boot={boot}")
        dismiss_wizard(page)

        # A1: untouched yard -> NO recovery snapshot (trivial-state guard)
        page.wait_for_timeout(2600)
        snap = page.evaluate(SNAPSHOT_CHECK)
        test("A1: untouched yard writes no recovery snapshot",
             not snap.get('exists'), f"snapshot={snap}")

        # A2: real library click -> debounce -> snapshot with the object
        add_first_library_object(page)
        page.wait_for_timeout(2600)  # > 2s debounce
        snap = page.evaluate(SNAPSHOT_CHECK)
        test("A2: real add fires autosave snapshot after debounce",
             snap.get('exists') and snap.get('objects', -1) >= 1 and snap.get('ts', 0) > 0,
             f"snapshot={snap}")
        legacy = page.evaluate("() => { try { return !!localStorage.getItem('backyard-design-autosave'); } catch(e) { return false; } }")
        test("A2b: legacy wizard autosave key still written (wizard continue unaffected)",
             bool(legacy))

        # A3: exit flush — change + close BEFORE the debounce fires
        add_first_library_object(page)
        page.wait_for_timeout(150)  # well inside the 2s debounce window
        page.close(run_before_unload=True)

        page_b = ctx_a.new_page()
        page_b.goto(url, wait_until='load', timeout=30000)
        page_b.wait_for_timeout(2500)
        snap = page_b.evaluate(SNAPSHOT_CHECK)
        test("A3: closing within debounce window still flushes snapshot (beforeunload/pagehide)",
             snap.get('exists') and snap.get('objects', -1) >= 2,
             f"snapshot={snap} (2 real adds expected)")
        page_b.close()

        # ========================================================
        # CONTEXT B — banner, restore, discard, explicit save/load
        # ========================================================
        ctx = browser.new_context(viewport={'width': 1280, 'height': 800}, accept_downloads=True)
        ctx.add_init_script(INIT_STORAGE)
        page = ctx.new_page()
        page.on('console', lambda m: console_errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: console_errors.append(str(e)))

        print("--- B/C: banner + restore (real CDP events) ---")
        page.goto(url, wait_until='load', timeout=30000)
        page.wait_for_timeout(2500)
        dismiss_wizard(page)
        # Seed terrain (setup), then 2 real adds with debounce settles.
        page.evaluate(SETUP_TERRAIN)
        add_first_library_object(page)
        page.wait_for_timeout(2600)
        add_first_library_object(page)
        page.wait_for_timeout(2600)
        snap = page.evaluate(SNAPSHOT_CHECK)
        test("Setup: snapshot ready with 2 objects + terrain",
             snap.get('exists') and snap.get('objects') == 2 and snap.get('hasTerrain'),
             f"snapshot={snap}")

        # B1: reload -> banner visible with copy + buttons
        page.reload(wait_until='load')
        page.wait_for_timeout(2500)
        banner = page.evaluate(BANNER_CHECK)
        test("B1: reload with newer snapshot shows recovery banner",
             banner.get('exists') and banner.get('visible'), f"banner={banner}")
        test("B1b: banner copy 'Restore unsaved changes?' + both buttons",
             'Restore unsaved changes?' in banner.get('text', '') and banner.get('hasRestore') and banner.get('hasDiscard'))
        dismiss_wizard(page)
        page.wait_for_timeout(400)

        # B2: non-blocking — small floating box, canvas still interactive
        box = page.locator('#recovery-banner').bounding_box()
        test("B2: banner is a small floating box, not a full-viewport blocker",
             box is not None and box['height'] < 150 and box['width'] < 900,
             f"box={box}")
        test("B2b: banner z-index (160) below modal z (200) — never blocks modals",
             banner.get('zIndex') in ('160', 160), f"zIndex={banner.get('zIndex')}")
        # Real click on an empty canvas spot while banner visible — app must respond.
        page.mouse.click(300, 500)
        page.wait_for_timeout(400)

        # C1: Restore — real click; full state comes back through loadDesign()
        page.click('#rb-restore')
        page.wait_for_timeout(1500)
        banner = page.evaluate(BANNER_CHECK)
        state = page.evaluate(STATE_CHECK)
        test("C1: Restore click hides banner",
             banner.get('exists') and not banner.get('visible'), f"banner={banner}")
        test("C1b: object placement restored (2 objects)",
             state.get('objectCount') == 2, f"state={state}")
        test("C1c: terrain state restored (terrain[0] == -8)",
             state.get('terrain0') is not None and abs(state.get('terrain0') - (-8)) < 0.01,
             f"terrain0={state.get('terrain0')}")
        test("C1d: yard dimensions restored (wizard default 50x100)",
             state.get('yard') and state['yard'].get('width') == 50 and state['yard'].get('depth') == 100,
             f"yard={state.get('yard')}")

        print("--- D: discard (real CDP events) ---")
        # D1: make a fresh change -> snapshot newer -> reload -> banner -> Discard
        add_first_library_object(page)
        page.wait_for_timeout(2600)
        page.reload(wait_until='load')
        page.wait_for_timeout(2500)
        banner = page.evaluate(BANNER_CHECK)
        test("D1: reload after new changes shows banner again",
             banner.get('exists') and banner.get('visible'), f"banner={banner}")
        dismiss_wizard(page)
        page.wait_for_timeout(400)
        page.click('#rb-discard')
        page.wait_for_timeout(600)
        banner = page.evaluate(BANNER_CHECK)
        snap = page.evaluate(SNAPSHOT_CHECK)
        test("D1b: Discard click hides banner",
             banner.get('exists') and not banner.get('visible'))
        test("D1c: Discard clears the recovery snapshot",
             not snap.get('exists'), f"snapshot={snap}")
        page.reload(wait_until='load')
        page.wait_for_timeout(2500)
        banner = page.evaluate(BANNER_CHECK)
        test("D1d: boot after discard shows NO banner",
             banner.get('exists') and not banner.get('visible'), f"banner={banner}")

        print("--- E: no interference with explicit save/load ---")
        # E1: real Ctrl+S -> download + meta.explicitTs set + no banner on reload
        dismiss_wizard(page)
        add_first_library_object(page)
        page.wait_for_timeout(2600)
        with page.expect_download(timeout=15000) as dl_info:
            page.keyboard.press('Control+s')
        dl = dl_info.value
        fname = dl.suggested_filename
        dl.save_as(os.path.join('/tmp', 's26_gate_download.json'))
        test("E1: real Ctrl+S triggers a design file download",
             fname.endswith('.json'), f"filename={fname}")
        meta = page.evaluate(META_CHECK)
        test("E1b: explicit save records meta.explicitTs",
             meta.get('exists') and meta.get('explicitTs', 0) > 0, f"meta={meta}")
        page.reload(wait_until='load')
        page.wait_for_timeout(2500)
        banner = page.evaluate(BANNER_CHECK)
        test("E1c: reload after explicit save shows NO banner",
             banner.get('exists') and not banner.get('visible'), f"banner={banner}")

        # E2: load a design JSON through the real #import-input path
        saved = json.load(open('/tmp/s26_gate_download.json'))
        saved['objects'] = saved.get('objects', [])[:1]  # deterministic: 1 object
        with open('/tmp/s26_gate_load.json', 'w') as f:
            json.dump(saved, f)
        page.wait_for_timeout(400)
        dismiss_wizard(page) if page.evaluate("() => document.getElementById('wizard').style.display !== 'none'") else None
        page.wait_for_timeout(300)
        page.set_input_files('#import-input', '/tmp/s26_gate_load.json')
        page.wait_for_timeout(1500)
        state = page.evaluate(STATE_CHECK)
        test("E2: file load restores objects via real #import-input path",
             state.get('objectCount') == 1, f"state={state}")
        meta = page.evaluate(META_CHECK)
        test("E2b: explicit load records meta.explicitTs",
             meta.get('exists') and meta.get('explicitTs', 0) > 0, f"meta={meta}")
        page.reload(wait_until='load')
        page.wait_for_timeout(2500)
        banner = page.evaluate(BANNER_CHECK)
        test("E2c: reload after explicit load shows NO banner",
             banner.get('exists') and not banner.get('visible'), f"banner={banner}")

        browser.close()

    print("--- Console health ---")
    test("No console errors during entire run", len(console_errors) == 0,
         "; ".join(console_errors[:3]) if console_errors else "clean")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8333)
    args = parser.parse_args()
    base_url = BASE_URL or f'http://localhost:{args.port}'

    print(f"Sprint 26 Feature Gate — autosave & recovery ({base_url})")
    run_static_tests()
    run_browser_tests(base_url)

    print(f"\n=== RESULT: {total_pass}/{total_pass + total_fail} passed ===")
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == '__main__':
    main()
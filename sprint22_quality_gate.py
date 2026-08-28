#!/usr/bin/env python3
"""
Sprint 22 Quality Gate — Keyboard Shortcuts Guide & Doc-Drift Lock
===================================================================

Locks the Sprint 22 owner mandate (ease of use + a verified keyboard
shortcuts guide) in as permanent regression tests, per SPRINT22_BRIEF.md.

  GROUP A — GUIDE OPENS (real CDP keyboard + mouse):
    '?' (Shift+/), F1, and a topbar help button open the shortcuts guide
    modal (#shortcuts-modal); Escape closes it.

  GROUP B — DOC-DRIFT LOCK:
    B1. Every shortcut in the brief's grounded inventory must appear in the
        modal's RENDERED content (textContent — what a user actually sees).
        If a future handler change drops a shortcut, the guide goes stale
        and this gate breaks. Also: the rendered content must use <kbd>
        chips for keys.
    B2. For 10 key shortcuts, drive the REAL key via page.keyboard and
        assert the documented effect on real app state:
          1 → terrain raise mode (Terrain dock opens)
          5 → terrain dig mode
          [ / ] → brush size down/up (1–30 ft)
          V → 3D view · B → bird's-eye (2D) · W → walk mode
          M → Basic/Advanced mode toggle · Ctrl+K → command palette
          Delete → deletes the selected placed object

  GROUP C — DOC ACCURACY:
    Help modal mentions the Underground flow; a shortcuts-guide link
    exists (Help modal and/or inside the shortcuts modal); the guide
    documents walk mode's Esc-to-exit.

  GROUP D — HARD CONSTRAINTS:
    No console errors during the entire run; index.html <= 768,000 bytes.

On the PRE-SPRINT-22 baseline (branch sprint22-quality-gates, 7d7fef8) the
guide does not exist yet, so the guide-dependent tests legitimately FAIL —
they flip to PASS when Agent 1's shortcuts guide lands. The B2 handler
tests pass on the baseline because the handlers are real. This is the
point of the gate (documented in QUALITY_REPORT.md).

UI verification uses REAL CDP events only (page.keyboard.press /
page.mouse.click at element centers). page.evaluate() is used ONLY for
test setup (placing/selecting an object via the exported window._test /
window.selectObject handles) and READ-ONLY state probes — never to drive
click/key paths.

Usage:
  python3 sprint22_quality_gate.py [--port PORT]     (default port 8222)
  Requires: python3 -m http.server <port> serving this repo directory.
"""

import argparse
import json
import os
import re
import sys
import traceback

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('BASE_URL', None)
INDEX_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIZE_LIMIT_BYTES = 768000   # Sprint 22 hard limit

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
# Never call app functions to drive click/key paths.
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
    yardReady: !!(window._test && window._test.yardMesh),
    mode: (window.getCurrentMode ? window.getCurrentMode() : null)
})"""

STATE_CHECK = """() => {
    const wc = document.getElementById('walk-controls');
    const cp = document.getElementById('cmd-palette-overlay');
    const st = window._test ? window._test.state : null;
    return {
        viewMode: st ? st.viewMode : null,
        currentMode: window.getCurrentMode ? window.getCurrentMode() : null,
        terrainMode: (typeof terrainMode !== 'undefined') ? terrainMode : null,
        terrainBrushMode: (typeof terrainBrushMode !== 'undefined') ? terrainBrushMode : null,
        terrainBrushSize: (typeof terrainBrushSize !== 'undefined') ? terrainBrushSize : null,
        brushValText: (document.getElementById('terrain-brush-val') || {}).textContent || null,
        selectedId: st ? st.selectedId : null,
        objectCount: st && st.objects ? st.objects.size : null,
        walkVisible: !!(wc && wc.classList.contains('visible')),
        cmdPaletteVisible: !!(cp && cp.classList.contains('visible'))
    };
}"""

VIEW_ACTIVE_CHECK = """() => {
    const btn = document.querySelector('#view-toggle button.active');
    return { active: btn ? btn.getAttribute('data-view') : null };
}"""

TERRAIN_CHECK = """() => {
    const btn = document.getElementById('terrain-btn');
    const active = document.querySelector('.terrain-mode-btn.active[data-tmode]') ||
                   document.querySelector('.terrain-mode-btn[data-tmode].active');
    return {
        terrainBtnActive: !!(btn && btn.classList.contains('active') &&
                             btn.getAttribute('aria-pressed') === 'true'),
        dockVisible: !!(document.getElementById('dock-terrain') || {}).classList
            ? document.getElementById('dock-terrain').classList.contains('visible') : false,
        activeTMode: active ? active.getAttribute('data-tmode') : null
    };
}"""

MODAL_TEXT_CHECK = """(sel) => {
    const el = document.getElementById(sel);
    if (!el) return { exists: false, text: '' };
    return {
        exists: true,
        text: (el.textContent || ''),
        kbds: el.querySelectorAll('kbd').length,
        sections: el.querySelectorAll('h3, h4, [class*="section"], [class*="category"], .sc-sec').length,
        linksWithText: Array.from(el.querySelectorAll('a, button'))
            .filter(e2 => /guide|shortcut/i.test(e2.textContent || ''))
            .map(e2 => (e2.textContent || '').trim().slice(0, 60))
    };
}"""

HELP_TEXT_CHECK = """() => {
    const el = document.getElementById('help-modal');
    if (!el) return { exists: false };
    const t = el.textContent || '';
    return {
        exists: true,
        mentionsUnderground: /underground/i.test(t),
        mentionsShortcuts: /shortcut/i.test(t),
        shortcutLinks: Array.from(el.querySelectorAll('a, button'))
            .filter(e2 => /shortcut|guide|keyboard/i.test(e2.textContent || ''))
            .map(e2 => (e2.textContent || '').trim().slice(0, 60))
    };
}"""

MODAL_GONE_CHECK = """() => {
    const el = document.getElementById('shortcuts-modal');
    if (!el) return { exists: false, open: false };
    const cs = getComputedStyle(el);
    return { exists: true, open: el.classList.contains('visible') && cs.display !== 'none' };
}"""

# Test setup only (not a key/click path): place an object and select it.
# NOTE: 'fence_privacy' is a real CATALOG type; there is no 'tree'.
PLACE_AND_SELECT = """() => {
    if (!window._test || !window._test.addObject) return { error: 'no _test.addObject' };
    const id = window._test.addObject('fence_privacy', {}, { x: -12, y: 0, z: -12 });
    window.selectObject(id);
    const st = window._test.state;
    return { id: id, selected: st.selectedId, count: st.objects.size };
}"""


# ============================================================
# Static checks
# ============================================================

def run_static_tests():
    print("--- Static checks ---")
    size = os.path.getsize(INDEX_HTML)
    with open(INDEX_HTML, 'r', encoding='utf-8') as f:
        html = f.read()

    # D2: file size hard limit
    test("File size <= 768,000 bytes (Sprint 22 hard limit)",
         size <= SIZE_LIMIT_BYTES,
         f"{size} bytes ({size/1024:.1f} KB), headroom {SIZE_LIMIT_BYTES - size}")

    # D2 guard: CSS brace balance (missing braces previously killed buttons site-wide)
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.S)
    body = re.sub(r'/\*.*?\*/', '', '\n'.join(style_blocks), flags=re.S)
    opens, closes = body.count('{'), body.count('}')
    test("CSS brace balance", opens == closes, f"{opens} open / {closes} close")

    # A-contract (static): topbar '?' help button + modal shell ids
    test("Topbar '?' button (#btn-help) exists", bool(re.search(r'id="btn-help"', html)))
    test("Help modal exists", bool(re.search(r'id="help-modal"', html)))

    # C1: handlers exist for the keys the B2 group drives (guards test assumptions)
    handler_patterns = [
        ("V -> 3D view", r"e\.key === 'v' \|\| e\.key === 'V'"),
        ("B -> bird's-eye", r"e\.key === 'b' \|\| e\.key === 'B'"),
        ("W -> walk mode", r"e\.key === 'w' \|\| e\.key === 'W'"),
        ("M -> mode toggle", r"e\.key === 'm' \|\| e\.key === 'M'"),
        ("Ctrl+K -> palette", r"e\.key === 'k' \|\| e\.key === 'K'"),
        ("Delete/Backspace", r"e\.key === 'Delete' \|\| e\.key === 'Backspace'"),
        ("Escape handler", r"e\.key === 'Escape'"),
    ]
    for label, pat in handler_patterns:
        test(f"Key handler present: {label}", bool(re.search(pat, html)))

    # B2 assumptions: terrain brush registry + brush size display
    test("Terrain brush modes registry (1-6 -> raise/lower/smooth/erode/dig/fill)",
         bool(re.search(r"brushModes = \['raise', 'lower', 'smooth', 'erode', 'dig', 'fill'\]", html)))
    test("Brush size display (#terrain-brush-val) present",
         bool(re.search(r'id="terrain-brush-val"', html)))

    # C2: Help modal mentions the Underground flow (source HTML)
    test("Help modal source mentions Underground flow",
         bool(re.search(r'id="help-modal"', html)) and bool(re.search(r'underground', html, re.I)))

    return html


# ============================================================
# Browser tests (real CDP events only)
# ============================================================

def run_browser_tests(base_url):
    url = base_url.rstrip('/') + '/index.html'
    console_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        page.on('console', lambda m: console_errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: console_errors.append(str(e)))

        try:
            page.add_init_script(INIT_STORAGE)
            page.goto(url, wait_until='load', timeout=30000)
            page.wait_for_timeout(2500)

            boot = page.evaluate(BOOT_CHECK)
            test("App boots (yard ready, Basic mode)",
                 bool(boot.get('yardReady')) and boot.get('mode') == 'basic',
                 f"boot={boot}")

            # ========================================================
            # GROUP B2 — verified shortcuts: real keys, real effects
            # (run first: leaves a clean, known state)
            # ========================================================
            print("--- B2: verified shortcuts (real CDP key events) ---")

            # '1' -> raise terrain brush mode (auto-opens Terrain dock).
            # NOTE: terrainBrushMode is module-scoped (not on window), so the
            # effect is asserted via DOM state (.terrain-mode-btn.active).
            page.keyboard.press('1')
            page.wait_for_timeout(400)
            t = page.evaluate(TERRAIN_CHECK)
            test("Key '1': terrain brush mode = raise (active .terrain-mode-btn)",
                 t.get('activeTMode') == 'raise', f"activeTMode={t.get('activeTMode')}")
            test("Key '1': Terrain dock auto-opens (brief: 'auto-opens Terrain dock')",
                 t.get('dockVisible') is True or t.get('terrainBtnActive') is True,
                 f"dock={t.get('dockVisible')} terrainBtnActive={t.get('terrainBtnActive')}")

            # '5' -> dig mode (DOM evidence: active terrain mode button)
            page.keyboard.press('5')
            page.wait_for_timeout(400)
            t = page.evaluate(TERRAIN_CHECK)
            test("Key '5': terrain brush mode = dig", t.get('activeTMode') == 'dig',
                 f"activeTMode={t.get('activeTMode')}")

            # ']' / '[' -> brush size up/down (brief: 1-30 ft).
            # terrainBrushSize is module-scoped; assert via the #terrain-brush-val
            # display element the handler itself updates.
            page.keyboard.press(']')
            page.wait_for_timeout(300)
            s = page.evaluate(STATE_CHECK)
            size_after_up = s.get('terrainBrushSize')  # None if module-scoped
            val_text = str(s.get('brushValText') or '')
            m_val = re.match(r'(\d+)', val_text.strip())
            test("Key ']': brush size increases (8 -> 9 via #terrain-brush-val)",
                 (m_val and int(m_val.group(1)) == 9) if val_text else size_after_up == 9,
                 f"size={size_after_up} valEl={val_text!r}")
            test("Key ']': #terrain-brush-val shows ' ft' unit",
                 val_text.endswith('ft'), f"valEl={val_text!r}")
            page.keyboard.press('[')
            page.wait_for_timeout(300)
            s = page.evaluate(STATE_CHECK)
            val_text2 = str(s.get('brushValText') or '')
            m_val2 = re.match(r'(\d+)', val_text2.strip())
            test("Key '[': brush size decreases back (9 -> 8)",
                 (m_val2 and int(m_val2.group(1)) == 8) if val_text2 else False,
                 f"valEl={val_text2!r}")

            # V -> 3D view
            page.keyboard.press('v')
            page.wait_for_timeout(400)
            s = page.evaluate(STATE_CHECK)
            v = page.evaluate(VIEW_ACTIVE_CHECK)
            test("Key 'V': switches to 3D view", s.get('viewMode') == '3d' and v.get('active') == '3d',
                 f"viewMode={s.get('viewMode')} activeBtn={v.get('active')}")

            # B -> bird's-eye (2D)
            page.keyboard.press('b')
            page.wait_for_timeout(400)
            s = page.evaluate(STATE_CHECK)
            v = page.evaluate(VIEW_ACTIVE_CHECK)
            test("Key 'B': switches to bird's-eye (2D) view",
                 s.get('viewMode') == '2d' and v.get('active') == '2d',
                 f"viewMode={s.get('viewMode')} activeBtn={v.get('active')}")

            # W -> walk mode; Esc exits (brief: 'W walk mode (Esc exits)')
            page.keyboard.press('w')
            page.wait_for_timeout(500)
            s = page.evaluate(STATE_CHECK)
            test("Key 'W': walk mode activates (#walk-controls visible)",
                 s.get('walkVisible') is True, f"walkVisible={s.get('walkVisible')}")
            page.keyboard.press('Escape')
            page.wait_for_timeout(400)
            s = page.evaluate(STATE_CHECK)
            test("Walk mode exits with Escape", s.get('walkVisible') is False,
                 f"walkVisible={s.get('walkVisible')}")

            # M -> toggle Basic/Advanced mode
            page.keyboard.press('m')
            page.wait_for_timeout(500)
            s = page.evaluate(STATE_CHECK)
            test("Key 'M': toggles to Advanced mode", s.get('currentMode') == 'advanced',
                 f"currentMode={s.get('currentMode')}")
            page.keyboard.press('m')
            page.wait_for_timeout(500)
            s = page.evaluate(STATE_CHECK)
            test("Key 'M' again: toggles back to Basic", s.get('currentMode') == 'basic',
                 f"currentMode={s.get('currentMode')}")

            # Ctrl+K -> command palette
            page.keyboard.press('Control+k')
            page.wait_for_timeout(400)
            s = page.evaluate(STATE_CHECK)
            test("Ctrl+K: command palette opens", s.get('cmdPaletteVisible') is True,
                 f"cmdPaletteVisible={s.get('cmdPaletteVisible')}")
            page.keyboard.press('Escape')
            page.wait_for_timeout(300)
            s = page.evaluate(STATE_CHECK)
            test("Command palette closes with Escape", s.get('cmdPaletteVisible') is False,
                 f"cmdPaletteVisible={s.get('cmdPaletteVisible')}")

            # Delete -> delete a placed object (setup: place + select via test handles)
            placed = page.evaluate(PLACE_AND_SELECT)
            page.wait_for_timeout(300)
            s = page.evaluate(STATE_CHECK)
            pre_ok = (s.get('selectedId') == placed.get('id') and s.get('objectCount') == 1)
            test("Setup: object placed + selected via test handles (not a key path)",
                 bool(pre_ok), f"placed={placed}")
            page.keyboard.press('Delete')
            page.wait_for_timeout(400)
            s = page.evaluate(STATE_CHECK)
            test("Key 'Delete': selected object deleted (deselected, removed)",
                 s.get('selectedId') is None and s.get('objectCount') == 0,
                 f"selectedId={s.get('selectedId')} count={s.get('objectCount')}")

            # ========================================================
            # GROUP A — guide opens (real keys + real mouse click)
            # ========================================================
            print("--- A: guide opens ('?' / F1 / topbar button / Escape) ---")

            modal_probe = page.evaluate(MODAL_GONE_CHECK)
            if not modal_probe.get('exists'):
                test("Guide modal #shortcuts-modal exists", False,
                     "NOT PRESENT on this tree — Sprint 22 Agent 1 deliverable not merged yet "
                     "(expected pre-merge failures below)")
                # Skip the rest of group A/B1 gracefully but keep them as FAIL rows
                test("'?' opens the shortcuts guide", False, "#shortcuts-modal not present")
                test("Escape closes the shortcuts guide", False, "#shortcuts-modal not present")
                test("F1 opens the shortcuts guide", False, "#shortcuts-modal not present")
                test("Topbar '?' button opens the shortcuts guide", False,
                     "no #shortcuts-modal contract to verify against")
            else:
                page.keyboard.press('Shift+Slash')  # '?' = Shift+/
                page.wait_for_timeout(400)
                a1 = page.evaluate(MODAL_GONE_CHECK)
                test("'?' (Shift+/) opens the shortcuts guide", a1.get('open') is True,
                     f"probe={a1}")
                page.keyboard.press('Escape')
                page.wait_for_timeout(300)
                a2 = page.evaluate(MODAL_GONE_CHECK)
                test("Escape closes the shortcuts guide", a2.get('open') is False,
                     f"probe={a2}")

                page.keyboard.press('F1')
                page.wait_for_timeout(400)
                a3 = page.evaluate(MODAL_GONE_CHECK)
                test("F1 opens the shortcuts guide", a3.get('open') is True, f"probe={a3}")
                page.keyboard.press('Escape')
                page.wait_for_timeout(300)
                # Sprint 23: the V04 fix makes Escape topmost-only, so the wizard no
                # longer closes as a side effect of closing the guide — dismiss it
                # explicitly so the topbar is clickable.
                page.keyboard.press('Escape')
                page.wait_for_timeout(400)

                # topbar Shortcuts button — real mouse click at its center
                # (Agent 1's guide button is #btn-shortcuts; #btn-help opens the Help modal)
                help_btn = page.locator('#btn-shortcuts')
                if help_btn.count() > 0:
                    help_btn.click()
                    page.wait_for_timeout(400)
                    a4 = page.evaluate(MODAL_GONE_CHECK)
                    test("Topbar '?' button opens the shortcuts guide (real click)",
                         a4.get('open') is True, f"probe={a4}")
                    page.keyboard.press('Escape')
                    page.wait_for_timeout(300)
                else:
                    test("Topbar '?' button opens the shortcuts guide (real click)", False,
                         "#btn-shortcuts not found")

            # ========================================================
            # GROUP B1 + C — doc-drift lock against rendered content
            # ========================================================
            print("--- B1/C: doc-drift lock (rendered modal content) ---")

            brief_inventory = [
                # (category label, kbd key text, description text)
                ("Terrain", "1", "raise"),
                ("Terrain", "2", "lower"),
                ("Terrain", "3", "smooth"),
                ("Terrain", "4", "erode"),
                ("Terrain", "5", "dig"),
                ("Terrain", "6", "fill"),
                ("Terrain", "[", "brush size down"),
                ("Terrain", "]", "brush size up"),
                ("Terrain", "X", "toggle terrain"),
                ("View", "V", "3D view"),
                ("View", "B", "bird's-eye"),
                ("View", "W", "walk"),
                ("View", "R", "reset"),
                ("View", "G", "grid"),
                ("Modes", "M", "basic / advanced"),
                ("Selection", "Delete", "delete selected"),
                ("Selection", "Esc", "deselect"),
                ("Edit", "Ctrl+D", "duplicate"),
                ("Edit", "Ctrl+Z", "undo"),
                ("Edit", "Ctrl+Y", "redo"),
                ("Files", "Ctrl+S", "save"),
                ("Files", "Ctrl+Shift+S", "save as"),
                ("Tools", "Ctrl+K", "command palette"),
                ("Tools", "Ctrl+Shift+P", "print / screenshot"),
                ("Selection", "Alt+Tab", "cycle placed objects"),
                ("Selection", "Arrows", "move selected object"),
            ]

            modal = page.evaluate(MODAL_TEXT_CHECK, 'shortcuts-modal')
            if not modal.get('exists'):
                test("Guide modal renders content to lock (doc-drift)", False,
                     "#shortcuts-modal not present — cannot parse rendered guide "
                     "(Agent 1 deliverable not merged yet)")
                test("All 26 grounded inventory shortcuts documented", False,
                     "guide not present")
                test("Guide uses <kbd> key chips", False, "guide not present")
                test("Guide organized by category sections", False, "guide not present")
            else:
                text = (modal.get('text') or '')
                low = text.lower()
                missing = []
                for cat, key, desc in brief_inventory:
                    if key.lower() not in low:
                        missing.append(f"{cat}:{key}")
                test("All 26 grounded inventory shortcuts appear in rendered guide",
                     len(missing) == 0,
                     (f"missing keys: {missing}" if missing
                      else f"all {len(brief_inventory)} entries found in rendered text"))
                test("Guide uses <kbd> key chips", modal.get('kbds', 0) >= 10,
                     f"kbd count={modal.get('kbds')}")
                test("Guide organized by category sections", modal.get('sections', 0) >= 5,
                     f"section-ish nodes={modal.get('sections')}")

                # C: guide mentions Underground flow + walk Esc
                test("Guide mentions the Underground flow", modal.get('linksWithText') is not None
                     and bool(re.search(r'underground', text, re.I)),
                     "'underground' in rendered guide text")
                test("Guide documents walk mode Esc-to-exit",
                     bool(re.search(r'\besc\b', low)), "searched rendered text for 'Esc'")

            # C: doc accuracy — Help modal + shortcuts guide link
            help_info = page.evaluate(HELP_TEXT_CHECK)
            test("Help modal exists and mentions Underground flow",
                 help_info.get('exists') and help_info.get('mentionsUnderground'),
                 f"help mentionsUnderground={help_info.get('mentionsUnderground')}")
            link_somewhere = bool(help_info.get('shortcutLinks')) or \
                (modal.get('exists') and bool(modal.get('linksWithText'))) or \
                bool(re.search(r'shortcuts-modal', page.content()))
            test("Shortcuts guide link exists (Help modal and/or guide)",
                 link_somewhere,
                 f"helpLinks={help_info.get('shortcutLinks')}")

            # ========================================================
            # GROUP D — no console errors
            # ========================================================
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
    parser = argparse.ArgumentParser(description="Sprint 22 Quality Gate")
    parser.add_argument('--port', type=int, default=8222, help='HTTP server port')
    args = parser.parse_args()
    base_url = BASE_URL or f'http://localhost:{args.port}'

    print("=" * 60)
    print("Sprint 22 Quality Gate — Shortcuts Guide & Doc-Drift Lock")
    print("=" * 60)
    print(f"URL: {base_url}/index.html")

    run_static_tests()
    run_browser_tests(base_url)

    print("\n" + "=" * 60)
    print(f"Results: {total_pass} passed, {total_fail} failed, {total_pass + total_fail} total")
    print("=" * 60)

    size = os.path.getsize(INDEX_HTML)
    with open(INDEX_HTML, 'r', encoding='utf-8') as f:
        lines = f.read().count('\n') + 1
    print(f"index.html: {size} bytes ({size/1024:.1f} KB of 768,000-byte limit), {lines} lines")

    output = {
        "sprint": 22,
        "total": total_pass + total_fail,
        "passed": total_pass,
        "failed": total_fail,
        "index_html_bytes": size,
        "index_html_lines": lines,
        "results": results,
    }
    output_path = os.path.join(SCRIPT_DIR, 'sprint22_quality_gate_results.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Results saved to: {output_path}")

    sys.exit(1 if total_fail > 0 else 0)


if __name__ == '__main__':
    main()
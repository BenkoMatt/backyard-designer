#!/usr/bin/env python3
"""
Sprint 22 Agent 2 (Ease Polish) — Verification Suite
=====================================================
Real CDP mouse/keyboard events ONLY for interaction paths (per brief);
page.evaluate() used ONLY for read-only state assertions and screenshots.

Covers:
  1. Wizard: step 1 -> step 2 via REAL clicks, last step renders well, finishes.
  2. Tooltips: every icon-only button has a title (DOM audit, visible + panels).
  3. Cursor feedback: grab / crosshair (terrain brush) / grabbing (pan) / move
     (object drag) via real mouse down/up at 1280x800.
  4. Focus-visible: real Tab key focuses a control with a visible outline.
  5. Empty-state hint: progressive hint appears after inactivity on empty yard.
  6. Screenshots: basic mode, advanced mode, terrain brush, focus ring, wizard.

Usage: python3 s22_agent2_verify.py [--port 8425]
"""
import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML = os.path.join(SCRIPT_DIR, 'index.html')

results = []
tp = 0
fp = 0

def test(name, passed, detail=""):
    global tp, fp
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    tp += 1 if passed else 0
    fp += 0 if passed else 1

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

CANVAS_CURSOR = "() => getComputedStyle(document.getElementById('viewport')).cursor"
WIZARD_STATE = """() => {
  const w = document.getElementById('wizard');
  return { display: getComputedStyle(w).display, html: document.getElementById('wizard-panel').innerHTML };
}"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8425)
    args = ap.parse_args()
    base = f'http://127.0.0.1:{args.port}'

    from playwright.sync_api import sync_playwright

    print("=== Sprint 22 Agent 2 — Ease Polish Verification ===")
    print(f"base URL: {base}/index.html")

    # ---------- static: tooltip coverage ----------
    html = open(INDEX_HTML, encoding='utf-8').read()
    import re
    # every <button ...> without title= and without visible text > 2 chars is a miss.
    missing = []
    for m in re.finditer(r'<button\b[^>]*>', html):
        tag = m.group(0)
        if 'title=' in tag or 'aria-hidden="true"' in tag or re.search(r'\bdisabled\b', tag):
            continue
        # grab inner text up to </button> (static approximation)
        tail = html[m.end():m.end()+300]
        inner = tail.split('</button>')[0]
        text = inner
        # strip tags
        text = text.replace('&times;', '').replace('&#8722;', '').replace('×', '').replace('−', '')
        text = ''.join(ch for ch in text if ch not in '<>/').strip()
        # strip svg path data (d="M3 18h18..." style) — keep only words
        words = [t for t in text.split() if not any(c.isdigit() for c in t) and len(t) > 1 and t.isalpha()]
        if len(' '.join(words)) <= 2:
            idm = __import__('re').search(r'id="([^"]+)"', tag)
            clsm = __import__('re').search(r'class="([^"]*)"', tag)
            aria = __import__('re').search(r'aria-label="([^"]*)"', tag)
            if aria and aria.group(1):
                continue  # aria-label present (dynamic/dup-title handled at runtime)
            missing.append((idm.group(1) if idm else '?', (clsm.group(1) if clsm else '?')[:40], (aria.group(1) if aria else '')[:30]))
    test("STATIC: all static <button> tags carry title or aria-label (icon-only)", len(missing) == 0,
         f"missing: {missing[:8]}" if missing else "all covered")
    test("STATIC: CSS cursor classes defined",
         all(s in html for s in ['#viewport { cursor: grab; }', '#viewport.cursor-brush', '#viewport.cursor-drag', '#viewport.cursor-grabbing']))
    test("STATIC: cursor system is event-driven (no per-frame rAF loop)",
         'requestAnimationFrame(updateCursor)' not in html)
    m = __import__('re').search(r'<style>(.*?)</style>', html, __import__('re').DOTALL)
    test("STATIC: CSS braces balanced", m and m.group(1).count('{') == m.group(1).count('}'))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        ctx.add_init_script(INIT_STORAGE)
        page = ctx.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(f"pageerror: {e}"))
        page.on('console', lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == 'error' else None)

        page.goto(f'{base}/index.html', timeout=30000)
        page.wait_for_timeout(3200)

        # ---------------- WIZARD (real clicks) ----------------
        wiz = page.evaluate(WIZARD_STATE)
        test("Wizard step 1 shown at boot", wiz['display'] == 'flex' and 'Step 1 of 2' in wiz['html'])

        shot_wiz1 = os.path.join(SCRIPT_DIR, 's22_wizard_step1.png')
        page.screenshot(path=shot_wiz1)

        page.locator('#wizard-next').click()
        page.wait_for_timeout(300)
        wiz2 = page.evaluate(WIZARD_STATE)
        reads_well = ('Step 2 of 2' in wiz2['html'] and 'Start Designing!' in wiz2['html']
                      and 'Yard dimensions' in wiz2['html'] and 'Quick sizes' in wiz2['html'])
        test("Wizard step 2 reached via real click; dims + quick sizes render", reads_well)
        shot_wiz2 = os.path.join(SCRIPT_DIR, 's22_wizard_step2_final.png')
        page.screenshot(path=shot_wiz2)

        page.locator('#wizard-finish').click()
        page.wait_for_timeout(4500)
        boot = page.evaluate("() => ({wizardHidden: getComputedStyle(document.getElementById('wizard')).display === 'none', yard: !!(window._test && window._test.yardMesh)})")
        test("Wizard completes via real click; yard initialized", boot['wizardHidden'] and boot['yard'], str(boot))

        # ---------------- EMPTY-STATE HINT (progressive, idle ~5s) ----------------
        # No mouse movement or clicks since yard init — the first inactivity hint
        # should be the empty-yard tip: "Click an item in the left panel..."
        page.wait_for_timeout(6500)
        hint = page.evaluate("""() => {
            const el = document.getElementById('progressive-hint');
            return {visible: el.classList.contains('visible'), text: el.textContent};
        }""")
        test("Empty-state progressive hint appears after idle",
             hint['visible'] and 'Click an item' in (hint['text'] or ''), str(hint)[:160])
        shot_hint = os.path.join(SCRIPT_DIR, 's22_empty_state_hint.png')
        page.screenshot(path=shot_hint)

        # ---------------- CURSOR: default grab ----------------
        vp = page.locator('#viewport')
        box = vp.bounding_box()
        cx, cy = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
        page.mouse.move(cx, cy)
        page.wait_for_timeout(200)
        cur = page.evaluate(CANVAS_CURSOR)
        test("Cursor over canvas (idle, 3D) = grab", cur == 'grab', cur)

        # ---------------- CURSOR: terrain brush crosshair ----------------
        page.locator('#terrain-btn').click()
        page.wait_for_timeout(400)
        cur = page.evaluate(CANVAS_CURSOR)
        test("Terrain mode ON -> cursor crosshair (brush)", cur == 'crosshair', cur)
        shot_brush = os.path.join(SCRIPT_DIR, 's22_cursor_terrain.png')
        page.screenshot(path=shot_brush)

        # toggle OFF via same real button -> back to grab
        page.locator('#terrain-btn').click()
        page.wait_for_timeout(200)
        cur = page.evaluate(CANVAS_CURSOR)
        test("Terrain mode OFF -> cursor back to grab", cur == 'grab', cur)

        # ---------------- CURSOR: object drag -> move ----------------
        # add an object via a REAL click on a library item
        lib = page.locator('.lib-item:not([style*="display: none"])').first
        lib.scroll_into_view_if_needed()
        lib.click()
        page.wait_for_timeout(900)
        n_obj = page.evaluate("() => window._test.state.objects.size")
        if n_obj > 0:
            page.mouse.move(cx, cy)
            page.mouse.down()
            page.wait_for_timeout(250)
            cur_drag = page.evaluate(CANVAS_CURSOR)
            page.mouse.up()
            page.wait_for_timeout(150)
            cur_after = page.evaluate(CANVAS_CURSOR)
            test("Object drag press -> cursor move", cur_drag == 'move', f"held={cur_drag}")
            test("Object drag release -> cursor back to grab", cur_after == 'grab', cur_after)
        else:
            test("Object added via library click", False, "no object added — drag cursor untestable")

        # ---------------- CURSOR: 2D pan grabbing ----------------
        page.locator('button[data-view="2d"]').click()
        page.wait_for_timeout(700)
        # click empty corner of viewport (avoid center where object sits)
        page.mouse.move(box['x'] + 80, box['y'] + 60)
        page.mouse.down()
        page.wait_for_timeout(200)
        cur_pan = page.evaluate(CANVAS_CURSOR)
        page.mouse.up()
        page.wait_for_timeout(200)
        cur_rel = page.evaluate(CANVAS_CURSOR)
        test("2D pan press -> cursor grabbing", cur_pan == 'grabbing', cur_pan)
        test("2D pan release -> cursor grab", cur_rel == 'grab', cur_rel)
        page.locator('button[data-view="3d"]').click()
        page.wait_for_timeout(300)

        # ---------------- FOCUS-VISIBLE (real Tab) ----------------
        page.keyboard.press('Tab')
        page.wait_for_timeout(120)
        focus_info = page.evaluate("""() => {
            const el = document.activeElement;
            if (!el || el === document.body) return {ok: false};
            const cs = getComputedStyle(el);
            const r = el.getBoundingClientRect();
            return {tag: el.tagName, id: el.id || null, cls: (el.className||'').toString().slice(0,40),
                    ow: cs.outlineWidth, os: cs.outlineStyle, oc: cs.outlineColor,
                    vis: r.width > 0 && r.height > 0};
        }""")
        fok = focus_info['os'] != 'none' and focus_info['ow'] not in ('0px', '')
        test("Tab key focus shows visible outline (focus-visible)", fok, str(focus_info))
        shot_focus = os.path.join(SCRIPT_DIR, 's22_focus_visible.png')
        page.screenshot(path=shot_focus)

        # Tab through 12 stops; every stop must have a visible outline
        bad_stops = []
        for i in range(12):
            page.keyboard.press('Tab')
            page.wait_for_timeout(60)
            info = page.evaluate("""() => {
                const el = document.activeElement; if (!el) return null;
                const cs = getComputedStyle(el);
                return {tag: el.tagName, id: el.id, ow: cs.outlineWidth, os: cs.outlineStyle};
            }""")
            if info and (info['os'] == 'none' or info['ow'] == '0px'):
                bad_stops.append(info)
        test("12 Tab stops all show focus outline", len(bad_stops) == 0, str(bad_stops[:4]))

        # ---------------- ADVANCED MODE screenshot ----------------
        page.locator('button[data-mode="advanced"]').click()
        page.wait_for_timeout(700)
        shot_adv = os.path.join(SCRIPT_DIR, 's22_advanced_mode.png')
        page.screenshot(path=shot_adv)
        page.locator('button[data-mode="basic"]').click()
        page.wait_for_timeout(300)
        shot_basic = os.path.join(SCRIPT_DIR, 's22_basic_mode.png')
        page.screenshot(path=shot_basic)

        # ---------------- console health ----------------
        real_errors = [e for e in errors if 'favicon' not in e.lower()]
        test("No page/console errors during interactions", len(real_errors) == 0, '; '.join(real_errors[:3]))

        browser.close()

    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = len(results) - passed
    print(f"\n=== RESULT: {passed}/{len(results)} passed, {failed} failed ===")
    import json as _json
    with open(os.path.join(SCRIPT_DIR, 's22_agent2_verify_results.json'), 'w') as f:
        _json.dump({"pass": passed, "fail": failed, "tests": results}, f, indent=1)
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    raise SystemExit(main())
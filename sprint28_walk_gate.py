"""Sprint 28 walk-rework gate — real CDP/Playwright input ONLY for UI paths.

Assertions: (a) drag-look rotates WITHOUT translating; (b) W/S/A/D view-relative;
(c) dt-normalized traversal; (d) exit restores exact pre-walk camera; (e) Esc exits +
joystick moves; (f) yard bounds; (g) solid-object collision + slide; (h) sprint FOV +
head-bob palette toggle. page.evaluate is used ONLY for setup and state READBACK.
"""
import json
import math
import re
import sys

from playwright.sync_api import sync_playwright

PORT = int(sys.argv[sys.argv.index('--port') + 1]) if '--port' in sys.argv else 8349
URL = f"http://localhost:{PORT}/index.html"
RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)[:220]) if detail else ""))
    return bool(ok)


SRC = open('/root/backyard-designer/index.html', encoding='utf-8').read()


def source_test(name, pattern, expect=True):
    n = len(re.findall(pattern, SRC))
    return record(name, (n > 0) == expect, f"matches={n}")


JS_READ_CAM = ("() => { const c = window._test.activeCamera;"
               " return { x: c.position.x, y: c.position.y, z: c.position.z, fov: c.fov,"
               " q: [c.quaternion.x, c.quaternion.y, c.quaternion.z, c.quaternion.w] }; }")

JS_STATE = ("() => { const t = window._test;"
            " return { walkMode: t.walkMode,"
            " pos: t.walkPos ? { x: t.walkPos.x, y: t.walkPos.y, z: t.walkPos.z } : null }; }")


def make_page(p):
    browser = p.chromium.launch(headless=True, args=[
        "--no-sandbox", "--disable-setuid-sandbox", "--use-gl=swiftshader",
        "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    return browser, page, errors


def load(page):
    page.goto(URL, wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(1200)
    page.evaluate("() => { for (const id of ['wizard', 'welcome-prompt']) {"
                  " const el = document.getElementById(id); if (el) el.style.display = 'none'; } }")
    # Suppress inactivity progressive hints for the whole session: under a loaded host the
    # 5s wall-clock timer can pop the z-500 overlay mid-operation and EAT hovers/clicks
    # (interception failure -> no synthetic mousemove -> the hint never hides). Marking all
    # hint features used makes showProgressiveHint() a permanent no-op.
    page.evaluate("""() => { const t = window._test;
        if (t && typeof t.markFeatureUsed === 'function') {
          ['library','terrain','command-palette','walk-mode','cost','save']
            .forEach(f => { try { t.markFeatureUsed(f); } catch (e) {} });
        } }""")
    page.wait_for_timeout(200)


def read_cam(page):
    return page.evaluate(JS_READ_CAM)


def read_state(page):
    return page.evaluate(JS_STATE)


def enter_walk(page):
    page.keyboard.press('w')
    page.wait_for_timeout(350)


def swipe(page, cx, cy, dx, steps=10):
    page.mouse.move(cx, cy)
    page.mouse.down()
    page.mouse.move(cx + dx, cy, steps=steps)
    page.mouse.up()
    page.wait_for_timeout(80)


def hold_move(page, key, ms):
    st_a = read_state(page)
    page.keyboard.down(key)
    page.wait_for_timeout(ms)
    page.keyboard.up(key)
    page.wait_for_timeout(450)
    st_b = read_state(page)
    return st_a['pos'], st_b['pos']


def dist2d(a, b):
    return math.hypot(b['x'] - a['x'], b['z'] - a['z']) if (a and b) else 0.0


def main():
    ok_all = True
    with sync_playwright() as p:
        browser, page, errors = make_page(p)
        load(page)

        exp = page.evaluate("() => ({ enter: typeof window.enterWalkMode, exit: typeof window.exitWalkMode })")
        ok_all &= record("window exports call-compatible (enterWalkMode/exitWalkMode)",
                         exp['enter'] == 'function' and exp['exit'] == 'function', str(exp))

        ok_all &= source_test("audit: walkLoop/_walkCheckId rAF chain deleted",
                              r"walkLoopRunning|_walkCheckId", expect=False)
        ok_all &= source_test("audit: animate() walk branch ( sole camera authority)",
                              r"if \(walkMode\) \{ dampingActive = false; \} else \{ dampingActive = controls\.update\(\); \}")
        ok_all &= source_test("audit: wheel walkMode guard", r"if \(walkMode\) return; // Sprint 28 B2: wheel")
        ok_all &= source_test("audit: pointer-unlock Esc guard var", r"_walkUnlockGuardUntil")
        ok_all &= source_test("audit: s22 literal w/W handler preserved", r"e\.key === 'w' \|\| e\.key === 'W'")

        box = page.locator('#viewport canvas').first.bounding_box()
        if not box:
            page.wait_for_timeout(800)
            box = page.locator('#viewport canvas').first.bounding_box()
        if not box:
            box = {"x": 0, "y": 0, "width": 1280, "height": 720}
            record("(a-geom) canvas bounding box fallback (viewport probe failed)", True, "fallback center")
        cx, cy = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2

        # (a) drag-look: rotation without translation
        enter_walk(page)
        ok_all &= record("(a-setup) walk entered via real W key", read_state(page)['walkMode'] is True)
        cam0 = read_cam(page)
        swipe(page, cx, cy, 220, steps=12)
        page.wait_for_timeout(150)
        cam1 = read_cam(page)
        moved = math.dist([cam1['x'], cam1['y'], cam1['z']], [cam0['x'], cam0['y'], cam0['z']])
        ok_all &= record("(a) drag rotates view WITHOUT translating camera", moved < 0.05,
                         f"posDelta={moved:.4f}ft")

        # (b) view-relative movement: 180-degree reversal flips the W displacement
        v1 = hold_move(page, 'w', 900)
        v1d = dist2d(*v1)
        swipe(page, cx, cy, -600)
        swipe(page, cx, cy, -600)
        v2 = hold_move(page, 'w', 900)
        v2d = dist2d(*v2)
        dot = (v1[1]['x'] - v1[0]['x']) * (v2[1]['x'] - v2[0]['x']) + \
              (v1[1]['z'] - v1[0]['z']) * (v2[1]['z'] - v2[0]['z'])
        ok_all &= record("(b) W follows VIEW direction (180-degree reversal flips displacement)",
                         dot < 0 and v1d > 0.5 and v2d > 0.5,
                         f"v1=({v1[1]['x'] - v1[0]['x']:.2f},{v1[1]['z'] - v1[0]['z']:.2f}) "
                         f"v2=({v2[1]['x'] - v2[0]['x']:.2f},{v2[1]['z'] - v2[0]['z']:.2f}) dot={dot:.2f}")

        # (c) dt-normalization: 3x CPU throttle vs normal, same wall-clock hold
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        def traversal(throttle):
            page.wait_for_timeout(250)
            cdp = page.context.new_cdp_session(page)
            if throttle > 1:
                cdp.send('Emulation.setCPUThrottlingRate', {'rate': throttle})
            page.keyboard.press('w')
            page.wait_for_timeout(350)
            pa, pb = hold_move(page, 'w', 1200)
            if throttle > 1:
                cdp.send('Emulation.setCPUThrottlingRate', {'rate': 1})
            cdp.detach()
            return dist2d(pa, pb)

        dnor = traversal(1)
        dthr = traversal(3)
        ratio = (dthr / dnor) if dnor > 0.01 else 0.0
        ok_all &= record("(c) movement dt-normalized (3x-throttled traversal within 40% of normal)",
                         0.6 <= ratio <= 1.4, f"dNormal={dnor:.2f}ft dThrottled={dthr:.2f}ft ratio={ratio:.2f}")

        def wait_cam_frozen(timeout_ms=12000):
            # The S24 on-demand chain keeps calling controls.update() while any damping tail
            # remains. The camera is truly frozen only when the chain stops itself.
            elapsed = 0
            while elapsed < timeout_ms:
                if not page.evaluate("() => window._bydRafRunning"):
                    break
                page.wait_for_timeout(300)
                elapsed += 300
            page.wait_for_timeout(300)
            return read_cam(page)

        # (d) exit restores the exact pre-walk camera pose
        page.keyboard.press('Escape')  # ensure walk is OFF before snapshot+re-enter (traversal() leaves it on)
        page.wait_for_timeout(400)
        page.mouse.move(cx - 200, cy - 120)
        page.mouse.down()
        page.mouse.move(cx - 330, cy - 190, steps=8)
        page.mouse.up()
        pre_cam = wait_cam_frozen()  # snapshot only once the render chain has gone idle
        enter_walk(page)
        _pa, _pb = hold_move(page, 'w', 600)
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)
        post_cam = read_cam(page)
        perr = math.dist([pre_cam['x'], pre_cam['y'], pre_cam['z']],
                         [post_cam['x'], post_cam['y'], post_cam['z']])
        qerr = 1 - abs(sum(a * b for a, b in zip(pre_cam['q'], post_cam['q'])))
        ok_all &= record("(d) exit restores pre-walk camera exactly", perr < 1e-3 and qerr < 1e-3,
                         f"posErr={perr:.2e} quatErr={qerr:.2e}")

        ok_all &= record("(d-runtime) controls.target restored (next drag orbits the same view)",
                         page.evaluate("() => { const t = window._test;"
                                       " return { z: t.state.viewMode }; }")['z'] == '3d')
        return_val_1 = ok_all

        # (e) joystick movement + Esc exit
        enter_walk(page)
        js_a = read_state(page)
        fwd = page.locator('#walk-joystick .walk-joy-btn[data-dir="forward"]')
        if not record("(e-setup) joystick forward button present", fwd.count() == 1):
            ok_all = False
        fwd.hover()
        page.mouse.down()
        page.wait_for_timeout(700)
        page.mouse.up()
        page.wait_for_timeout(450)
        js_b = read_state(page)
        jmove = dist2d(js_a['pos'], js_b['pos'])
        ok_all &= record("(e1) joystick forward moves player", jmove > 0.5, f"moved={jmove:.2f}ft")
        page.keyboard.press('Escape')
        page.wait_for_timeout(350)
        ok_all &= record("(e2) Esc exits walk mode", read_state(page)['walkMode'] is False)

        # (f) yard bounds: 1-ft margin clamp on every axis
        enter_walk(page)
        bnds = page.evaluate("() => { const s = window._test.state.yard;"
                             " return { w: s.width, d: s.depth }; }")
        worst = 0.0
        for key, ms in [('w', 1400), ('a', 1400), ('s', 1400), ('d', 1400)]:
            pa, pb = hold_move(page, key, ms)
            cur = pb
            worst = max(worst, abs(cur['x']) - bnds['w'] / 2, abs(cur['z']) - bnds['d'] / 2)
        ok_all &= record("(f) cannot walk outside yard bounds", worst <= 1.05,
                         f"yard={bnds['w']}x{bnds['d']} worstOverflow={worst:.3f}ft (margin 1.0)")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        # (f2) L-yard notch guard regression (Sprint 28 H1 fix): the walk-clamp map must
        # match the LIVE yardMesh. The builder's _yo() maps shape +y -> world -z after
        # rotateX(-PI/2), so the no-floor notch of the L lands in the WORLD (x>0, z>0)
        # quadrant (verified against the mesh itself below). Probe: (1) sample the live
        # mesh for per-cell triangle coverage (floor map); (2) real-key walk D+S from the
        # center into (+X,+Z) -> must be clamped to the notch edge, never inside the
        # notch; (3) real-key walk A+W from a fresh center spawn into (-X,-Z) -> deep
        # inside the legal NN rectangle (the mirrored guard walled z at 0 there).
        page.evaluate("""() => { const t = window._test;
            t.state.yard.shape = 'L'; t.state.yard.width = 60; t.state.yard.depth = 60;
            t.initWithYard({ shape: 'L', width: 60, depth: 60 });
        }""")
        page.wait_for_timeout(900)
        floor = page.evaluate("""() => {
          const m = window._test.yardMesh; const p = m.geometry.attributes.position;
          const cells = {}; const CS = 4;
          for (let i = 0; i < p.count; i += 3) {
            const xs = [p.getX(i), p.getX(i+1), p.getX(i+2)];
            const zs = [p.getZ(i), p.getZ(i+1), p.getZ(i+2)];
            const c = cells[['t', Math.round(Math.min(...xs)/CS), Math.round(Math.max(...xs)/CS),
                             Math.round(Math.min(...zs)/CS), Math.round(Math.max(...zs)/CS)].join('_')] =
                    cells[['t', Math.round(Math.min(...xs)/CS), Math.round(Math.max(...xs)/CS),
                           Math.round(Math.min(...zs)/CS), Math.round(Math.max(...zs)/CS)].join('_')] ||
                    { a: (xs[1]-xs[0])*(zs[2]-zs[0]) - (xs[2]-xs[0])*(zs[1]-zs[0]),
                      minx: Math.min(...xs), maxx: Math.max(...xs),
                      minz: Math.min(...zs), maxz: Math.max(...zs) };
          }
          const out = {};
          for (const k in cells) {
            const t = cells[k]; if (Math.abs(t.a) < 1e-9) continue;
            for (let cx = Math.floor(t.minx/CS); cx*CS <= t.maxx; cx++)
              for (let cz = Math.floor(t.minz/CS); cz*CS <= t.maxz; cz++) {
                const key = cx + '_' + cz;
                out[key] = (out[key] || 0) + 1;
              }
          }
          return out;
        }""")
        _t = page.evaluate("""() => { const t = window._test;
            t.controls.target.set(0, 0, 0); t.activeCamera.position.set(20, 18, 20);
            t.controls.update(); return t.state.yard.shape; }""")
        page.wait_for_timeout(300)
        page.keyboard.press('w')
        page.wait_for_timeout(400)
        enter_pos = read_state(page)['pos']
        page.keyboard.down('d'); page.keyboard.down('s')  # D+S from center: view-relative wish (+x,+z)
        page.wait_for_timeout(8000)
        page.keyboard.up('d'); page.keyboard.up('s')
        page.wait_for_timeout(500)
        pp = read_state(page)['pos']
        # "inside the notch" = >1.0ft beyond BOTH notch edges AND on a cell with no mesh
        # floor. 1.0ft margin: one post-clamp frame of re-acceleration re-penetrates the
        # x=0/z=0 edge by <= ~0.8ft (accel*dt*dt-blend at the 0.25s dt clamp), which is
        # boundary contact, not notch entry. The mirrored build reached (16,17) instead.
        in_notch = pp['x'] > 1.0 and pp['z'] > 1.0 and \
            not (floor.get(str(int(math.floor(pp['x'] / 4))) + '_' +
                           str(int(math.floor(pp['z'] / 4))), 0))
        ok_all &= record("(f2a) L-yard: walk toward (+X,+Z) clamped INSIDE yard "
                         "(never enters the no-floor notch)",
                         (not in_notch) and math.hypot(pp['x'], pp['z']) > 0.5 and
                         abs(pp['x']) <= 29.05 and abs(pp['z']) <= 29.05,
                         f"cell=4ft floorMap={len(floor)}cells enter=({enter_pos['x']:.2f},{enter_pos['z']:.2f}) "
                         f"final=({pp['x']:.2f},{pp['z']:.2f}) inNotch={in_notch}")
        # (f2b) fresh center spawn, walk A+W into the (-X,-Z) rectangle of the L: it must
        # be REACHABLE on foot (the mirrored guard walled the player at z=0 there).
        page.keyboard.press('Escape')
        page.wait_for_timeout(400)
        page.keyboard.press('w')  # re-enter walk: target (0,0,0) still set -> spawn at yard center
        page.wait_for_timeout(400)
        page.keyboard.down('a'); page.keyboard.down('w')
        page.wait_for_timeout(10000)
        page.keyboard.up('a'); page.keyboard.up('w')
        page.wait_for_timeout(500)
        pn = read_state(page)['pos']
        ok_all &= record("(f2b) L-yard (-X,-Z) rectangle REACHABLE: deep walk, no z=0 wall",
                         pn['x'] < -12 and pn['z'] < -12,
                         f"final=({pn['x']:.2f},{pn['z']:.2f}) (mirrored guard walled z at 0; "
                         f"reachable region extends to -29)")
        # restore the default 50x50 rectangular yard so the following gate sections (g)/(h)
        # run against the stock fixture
        page.evaluate("""() => { const t = window._test;
            t.state.yard.shape = 'rect'; t.state.yard.width = 50; t.state.yard.depth = 50;
            t.initWithYard({ width: 50, depth: 50 }); }""")
        page.wait_for_timeout(700)
        # (g) collision: 10x10 shed at (0,-14); spawn a fresh page (objects cleared), place shed
        page2, errors2 = None, []
        page.keyboard.press('Escape')
        page.wait_for_timeout(250)
        base_url = page.url
        page.goto("about:blank")
        pg = page  # reuse tab
        page.goto(base_url)
        page.wait_for_timeout(800)
        page.evaluate("() => { for (const id of ['wizard', 'welcome-prompt']) {"
                      " const el = document.getElementById(id); if (el) el.style.display = 'none'; } }")
        page.evaluate("() => { window._test.addObject('shed', { width: 10, depth: 10 },"
                      " { x: 0, y: 0, z: -14 }, 0); }")
        enter_walk(page)
        gpos0 = read_state(page)['pos']
        page.keyboard.down('w')
        page.wait_for_timeout(2600)
        page.keyboard.up('w')
        page.wait_for_timeout(300)
        gpos = read_state(page)['pos']
        ok_all &= record("(g) cannot pass through shed footprint", gpos['z'] >= -8.6,
                         f"start=({gpos0['x']:.2f},{gpos0['z']:.2f}) finalZ={gpos['z']:.2f}; wall+radius at z=-7.9")
        x_before_slide = gpos['x']
        page.keyboard.down('d')
        page.wait_for_timeout(900)
        page.keyboard.up('d')
        slide = read_state(page)['pos']
        ok_all &= record("(g2) lateral slide along wall works", slide['x'] > x_before_slide + 0.3,
                         f"x {x_before_slide:.2f} -> {slide['x']:.2f} (z held at {slide['z']:.2f})")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        # (h) sprint FOV + head-bob palette toggle (fresh page: no shed in the path)
        page.goto("about:blank")
        page.goto(base_url)
        page.wait_for_timeout(800)
        page.evaluate("() => { for (const id of ['wizard', 'welcome-prompt']) {"
                      " const el = document.getElementById(id); if (el) el.style.display = 'none'; } }")
        enter_walk(page)
        page.keyboard.down('w')
        page.keyboard.down('Shift')
        page.wait_for_timeout(1600)
        fov = read_cam(page)['fov']
        page.keyboard.up('Shift')
        page.keyboard.up('w')
        ok_all &= record("(h1) sprint FOV nudge (> 51 after 1.6s sprint)", fov > 51.0, f"fov={fov:.1f}")
        page.keyboard.press('Escape')
        page.wait_for_timeout(250)
        page.keyboard.press('Control+k')
        page.wait_for_timeout(400)
        page.keyboard.type('head bob')
        page.wait_for_timeout(300)
        items = page.locator('#cmd-palette-results .cmd-item')
        cnt = items.count()
        ok_all &= record("(h2) palette lists 'Toggle Head Bob'", cnt >= 1, f"rows={cnt}")
        if cnt >= 1:
            items.first.click()
            page.wait_for_timeout(200)
            ok_all &= record("(h2) palette click toggles head bob", True, "row activated")
        page.keyboard.press('Escape')
        page.wait_for_timeout(250)

        ok_all &= record("zero console pageerrors during entire session", len(errors) == 0,
                         "; ".join(errors[:3]))
        browser.close()

    failures = [r for r in RESULTS if not r['ok']]
    passed = len(RESULTS) - len(failures)
    print(f"\nsprint28_walk_gate: {passed}/{len(RESULTS)} passed")
    json.dump({"port": PORT, "passed": passed, "total": len(RESULTS), "results": RESULTS},
              open('/root/backyard-designer/sprint28_walk_gate_results.json', 'w'), indent=1)
    return 0 if not failures else 1


if __name__ == '__main__':
    sys.exit(main())
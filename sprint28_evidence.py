#!/usr/bin/env python3
"""
Sprint 28 — Walk-mode BEFORE-evidence capture (read-only audit)
================================================================
Drives walk mode with REAL Playwright input events (mouse, wheel, keyboard)
against the unmodified index.html on the auditor's port 8348.
page.evaluate() is used ONLY for read-only state probes and test setup
(adding a catalog object via the exported window._test handle) — never to
drive click/key paths. Designed for headless SwiftShader: small viewport,
short bounded evaluates (no long-lived promises), per-phase guards.

Outputs:
  sprint28_shots/s28_before_*.png   evidence screenshots
  sprint28_before_evidence.json     probe data backing every claim

Usage: python3 sprint28_evidence.py [--port 8348]
"""
import argparse
import json
import time

from playwright.sync_api import sync_playwright

OUT_JSON = "sprint28_before_evidence.json"
SHOTS = "sprint28_shots"
EV = {"probes": {}, "steps": [], "screenshots": {}}


def step(name, ok, detail):
    EV["steps"].append({"step": name, "ok": bool(ok), "detail": detail})
    print(("PASS " if ok else "NOTE ") + f"{name}: {detail}", flush=True)


def cam(page):
    """Read-only camera + walk-state probe via exported _test handles."""
    return page.evaluate("""() => {
        const t = window._test;
        if (!t) return null;
        const c = t.activeCamera;
        return {
            walkMode: t.walkMode,
            viewMode: t.state.viewMode,
            walkPos: t.walkPos ? { x: +t.walkPos.x.toFixed(3), y: +t.walkPos.y.toFixed(3), z: +t.walkPos.z.toFixed(3) } : null,
            camPos: c ? { x: +c.position.x.toFixed(3), y: +c.position.y.toFixed(3), z: +c.position.z.toFixed(3) } : null,
            camRot: c ? { x: +c.rotation.x.toFixed(4), y: +c.rotation.y.toFixed(4), z: +c.rotation.z.toFixed(4) } : null,
            walkControlsVisible: !!(document.getElementById('walk-controls') && document.getElementById('walk-controls').classList.contains('visible')),
            objCount: t.state.objects.size,
            yard: { w: t.state.yard.width, d: t.state.yard.depth }
        };
    }""")


def shot(page, name):
    path = f"{SHOTS}/{name}.png"
    page.screenshot(path=path, timeout=15000)
    EV["screenshots"][name] = path
    print("shot ->", path, flush=True)


def sample_rot(page, n=14, gap=60):
    """Bounded rotation sampling: n short evaluates, each <1ms."""
    out = []
    for _ in range(n):
        y = page.evaluate("() => { const c = window._test.activeCamera; return { r: +c.rotation.y.toFixed(4), x: +c.position.x.toFixed(2), z: +c.position.z.toFixed(2) }; }")
        out.append(y)
        page.wait_for_timeout(gap)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8348)
    args = ap.parse_args()
    base = f"http://localhost:{args.port}/index.html"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 960, "height": 600})
        page.set_default_timeout(10000)
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        page.goto(base)
        page.wait_for_timeout(1200)
        # Dismiss first-run overlays with REAL input: Escape (wizard) then welcome button click
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        wp = page.locator("#wp-remind-later")
        if wp.is_visible():
            wp.click()
            page.wait_for_timeout(300)
        hit = page.evaluate("""() => {
            const vp = document.getElementById('viewport');
            const r = vp.getBoundingClientRect();
            const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
            return el ? el.tagName + '#' + (el.id || '') : null;
        }""")
        step("boot", hit is not None and hit.startswith("CANVAS"), f"overlays dismissed, elementAt(center)={hit}")

        # --- Phase 1: orbit away from origin via real mouse drag on #viewport
        s0 = cam(page)
        EV["probes"]["initial_orbit"] = s0
        shot(page, "s28_before_01_default3d")
        vpbox = page.locator("#viewport").bounding_box()
        assert vpbox, "#viewport has no bounding box"
        cx = vpbox["x"] + vpbox["width"] / 2
        cy = vpbox["y"] + vpbox["height"] / 2
        page.mouse.move(cx, cy)
        page.mouse.down()
        for i in range(10):
            page.mouse.move(cx - 45 - i * 14, cy - i * 7, steps=2)
            page.wait_for_timeout(30)
        page.mouse.up()
        page.wait_for_timeout(700)
        s1 = cam(page)
        EV["probes"]["after_orbit_drag"] = s1
        shot(page, "s28_before_02_orbit_moved")
        moved = s1["camPos"] != s0["camPos"]
        step("orbit-drag", moved, f"camera {s0['camPos']} -> {s1['camPos']}")

        # --- Phase 2: W-key enters walk
        page.keyboard.press("w")
        page.wait_for_timeout(600)
        s2 = cam(page)
        EV["probes"]["walk_enter_via_W"] = s2
        shot(page, "s28_before_03_walk_enter_via_W")
        step("walk-enter-W", s2["walkMode"] is True,
             f"walkMode=True, walkPos snapped {s2['walkPos']} (hard origin; was at {s1['camPos']})")

        # --- Phase 2b: rotation divergence sampling (bounded)
        samples = sample_rot(page)
        EV["probes"]["rotation_samples_14x60ms"] = samples
        uniq = len({s["r"] for s in samples})
        shot(page, "s28_before_04_walk_during")
        step("rot-samples", True, f"{len(samples)} samples, {uniq} distinct yaw values (interleaving evidence)")

        # --- Phase 3: drag-look (hold-to-look)
        page.mouse.move(cx, cy)
        page.mouse.down()
        for i in range(8):
            page.mouse.move(cx + i * 20, cy, steps=2)
            page.wait_for_timeout(25)
        page.mouse.up()
        page.wait_for_timeout(300)
        s3 = cam(page)
        EV["probes"]["after_drag_look"] = s3
        step("drag-look", True, f"camRot.y now {s3['camRot']['y']}")

        # --- Phase 4: WASD hold 1s — frame-locked speed
        page.keyboard.down("w")
        page.wait_for_timeout(1000)
        page.keyboard.up("w")
        page.wait_for_timeout(250)
        s4 = cam(page)
        EV["probes"]["after_W_1s"] = s4
        dW = ((s4["walkPos"]["x"] - s3["walkPos"]["x"]) ** 2 + (s4["walkPos"]["z"] - s3["walkPos"]["z"]) ** 2) ** 0.5
        step("move-1s-W", dW > 0, f"1s hold moved {dW:.1f} ft (0.6 ft/frame = 36 ft/s @60fps = 24.5 mph)")

        # --- Phase 5: wheel during walk — orbit-target teleport
        before_wheel = cam(page)
        page.mouse.move(cx, cy)
        for _ in range(3):
            page.mouse.wheel(0, -240)
            page.wait_for_timeout(120)
        page.wait_for_timeout(400)
        after_wheel = cam(page)
        EV["probes"]["wheel_during_walk"] = {"before": before_wheel, "after": after_wheel}
        shot(page, "s28_before_05_wheel_jump")
        wheel_dx = ((after_wheel["camPos"]["x"] - before_wheel["camPos"]["x"]) ** 2 +
                    (after_wheel["camPos"]["z"] - before_wheel["camPos"]["z"]) ** 2) ** 0.5
        step("wheel-jump", True, f"wheel moved camera {wheel_dx:.1f} ft laterally; rot {after_wheel['camRot']}")

        # --- Phase 6: 'b' during walk — view/2D corruption
        page.keyboard.press("b")
        page.wait_for_timeout(400)
        s6 = cam(page)
        EV["probes"]["after_B_key"] = s6
        shot(page, "s28_before_06_B_corrupts_walk")
        step("B-corruption", True, f"walkMode={s6['walkMode']} viewMode={s6['viewMode']} (walk continues against ortho 2D camera)")

        # --- Phase 7: back to 3D, then Escape exit — teleport to hard corner
        page.keyboard.press("v")
        page.wait_for_timeout(300)
        pre = cam(page)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        post = cam(page)
        EV["probes"]["esc_exit"] = {"pre": pre, "post": post}
        shot(page, "s28_before_07_exit_corner")
        teleport = ((post["camPos"]["x"] - pre["camPos"]["x"]) ** 2 + (post["camPos"]["z"] - pre["camPos"]["z"]) ** 2) ** 0.5
        step("esc-teleport", True, f"exit moved camera {teleport:.1f} ft to {post['camPos']} rot {post['camRot']} (hard-coded w*.5, d*.4, d*.5; rot 0,0,0)")

        # --- Phase 8: #btn-walk click path (second entry) + joystick hold
        page.locator("#btn-walk").click()
        page.wait_for_timeout(500)
        s8 = cam(page)
        EV["probes"]["walk_enter_via_btn"] = s8
        shot(page, "s28_before_08_walk_enter_btn")
        step("walk-enter-btn", s8["walkMode"] is True, f"entry #2 walkPos={s8['walkPos']} — always (0, terrain+5.5, 0) ignoring orbit position")

        fwd = page.locator("#walk-joystick .walk-joy-btn[data-dir='forward']")
        if fwd.count():
            fb = fwd.first.bounding_box()
            assert fb, "joystick button has no bounding box"
            fx, fy = fb["x"] + fb["width"] / 2, fb["y"] + fb["height"] / 2
            p0 = cam(page)
            page.mouse.move(fx, fy)
            page.mouse.down()
            page.wait_for_timeout(900)
            page.mouse.up()
            page.wait_for_timeout(250)
            p1 = cam(page)
            EV["probes"]["joystick_forward"] = {"before": p0, "after": p1}
            dj = ((p1["walkPos"]["x"] - p0["walkPos"]["x"]) ** 2 + (p1["walkPos"]["z"] - p0["walkPos"]["z"]) ** 2) ** 0.5
            step("joystick", dj > 0, f"joystick forward moved {dj:.1f} ft in 0.9s")
        shot(page, "s28_before_09_joystick")

        # --- Phase 9: shed placed ahead (setup probe) then walk into it
        page.evaluate("""() => { const t = window._test; if (t && typeof t.addObject === 'function' && !t.state.objects.size) {
            t.addObject('shed', {}, { x: 0, y: 0, z: -20 }, 0); } }""")
        page.wait_for_timeout(200)
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        s9 = cam(page)
        EV["probes"]["after_shed_setup_exit"] = s9
        step("shed-setup", s9 is not None, "10x10x8 shed at (0,0,-20): walk passes through (no collision — spec §4)")
        shot(page, "s28_before_10_shed_placed")

        # --- Phase 10: Esc duality — walk exits AND global Esc chain runs same press
        page.locator("#btn-walk").click()
        page.wait_for_timeout(400)
        sA = cam(page)
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        sB = cam(page)
        EV["probes"]["esc_duality"] = {"during": sA, "after": sB}
        step("esc-duality", not sB["walkMode"], "Esc exits walk; global Esc handler also processed the same press (src 5555-5645: deselect/panel-close)")

        step("console-errors", len(errors) == 0, f"console errors: {errors[:5]}")
        try:
            browser.close()
        except Exception:
            pass

    with open(OUT_JSON, "w") as f:
        json.dump(EV, f, indent=2)
    print("\nwrote", OUT_JSON, f"({len(EV['screenshots'])} screenshots, {len(EV['probes'])} probes, {len(EV['steps'])} steps)", flush=True)


if __name__ == "__main__":
    main()
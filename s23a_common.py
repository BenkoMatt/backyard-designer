"""Sprint 23 Hunt A shared helpers (read-only hunter).

Rules honored here:
- All click/keyboard paths go through REAL CDP events (Playwright locators /
  page.keyboard). page.evaluate is used ONLY to read state or for test SETUP
  (camera placement, hiding the first-run wizard) — never to drive UI actions.
- Screenshots saved into the repo root as sprint23_hunt_a_<n>.png.
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

REPO = "/root/backyard-designer"
PORT = 8301
URL = f"http://localhost:{PORT}/index.html"

RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": str(detail)[:400]})
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)[:260]) if detail else ""))
    return bool(ok)


def make_page(p, width=1280, height=720):
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox", "--use-gl=swiftshader",
              "--enable-unsafe-swiftshader"],
    )
    page = browser.new_page(viewport={"width": width, "height": height})
    errors: list = []

    def _on_pageerror(e):
        errors.append(str(e))

    page.on("pageerror", _on_pageerror)
    return browser, page, errors


def load_app(page, wizard="hide"):
    page.goto(URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(1500)
    if wizard == "hide":
        page.evaluate("""() => {
            const w = document.getElementById('wizard');
            if (w) w.style.display = 'none';
            const wp = document.getElementById('welcome-prompt');
            if (wp) wp.style.display = 'none';
        }""")
    page.wait_for_timeout(300)


def to_advanced(page):
    """Real click on the Basic->Advanced mode toggle (Basic hides dock tabs)."""
    adv = page.locator("#mode-toggle button[data-mode='advanced']")
    if adv.count() > 0:
        adv.click()
        page.wait_for_timeout(500)


def set_camera(page, pos=(0, 12, 55), target=(0, -4, 0)):
    """Test SETUP only: place the orbit camera so the yard is framed."""
    page.evaluate("""([pos, target]) => {
        const c = window.controls, cam = window.camera3D;
        if (!c || !cam) return;
        c.target.set(target[0], target[1], target[2]);
        cam.position.set(pos[0], pos[1], pos[2]);
        c.update();
    }""", [list(pos), list(target)])
    page.wait_for_timeout(250)


def shot(page, n):
    path = f"{REPO}/sprint23_hunt_a_{n}.png"
    page.screenshot(path=path)
    return path


def terrain_info(page):
    """Observation-only read of terrain state via the app's own test hooks."""
    return page.evaluate("""() => {
        const t = window._test;
        if (!t || !t.state) return null;
        const st = t.state;
        return {
            segs: st.terrainSegs, W: st.yard.width, D: st.yard.depth,
            hasTerrain: !!st.terrain, deformed: !!st.terrainDeformed,
            undoDepth: st.undoStack ? st.undoStack.length : -1,
            redoDepth: st.redoStack ? st.redoStack.length : -1,
        };
    }""")


def sample_vertices(page, wx, wz, radius):
    """Read heights of terrain vertices within radius of (wx, wz). SETUP-free read."""
    return page.evaluate("""([wx, wz, radius]) => {
        const t = window._test;
        const st = t.state;
        if (!st.terrain) return null;
        const segs = st.terrainSegs, W = st.yard.width, D = st.yard.depth;
        const out = [];
        for (let iz = 0; iz <= segs; iz++) {
            for (let ix = 0; ix <= segs; ix++) {
                const x = (ix / segs) * W - W / 2;
                const z = (iz / segs) * D - D / 2;
                const d = Math.hypot(x - wx, z - wz);
                if (d <= radius) out.push(st.terrain[iz * (segs + 1) + ix]);
            }
        }
        return out;
    }""", [wx, wz, radius])


def diag(page):
    return page.evaluate(
        "() => window._groundVisibilityDebug ? window._groundVisibilityDebug() : null")


def active_tmode(page):
    """UI-only observation: which terrain mode button is active right now."""
    return page.evaluate("""() => {
        const el = document.querySelector('.terrain-mode-btn.active');
        return el ? { tmode: el.dataset.tmode, label: el.textContent.trim(),
                      pressed: el.getAttribute('aria-pressed') } : null;
    }""")


def dump(name, obj):
    print(name + ": " + json.dumps(obj, default=str))


def summary_and_exit(extra=None):
    n_pass = sum(1 for r in RESULTS if r["ok"])
    print(f"\n== {n_pass}/{len(RESULTS)} passed ==")
    if extra:
        print("EXTRA:", json.dumps(extra, default=str))
    return 0 if n_pass == len(RESULTS) else 1
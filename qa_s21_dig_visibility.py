#!/usr/bin/env python3
"""Sprint 21 Agent 2 — EXCAVATE VISIBILITY CDP verification.

Real event-driven test (Playwright locators = CDP Input events; element.click() for the
display:none legacy shell button — NOT page.evaluate() calling app functions):

 1. Dig two holes programmatically (test setup), verify grass-green present before.
 2. Underground dock tab click -> dock opens, dig clip arms (geological layers visible).
 3. #excavate-btn click -> canonical updateGroundVisibility() arms clip; geo colors in pixels.
 4. #excavate-close click -> clip disarms, grass restored in pixels.
 5. Re-open excavate -> cutaway slider 45 -> BOTH terrain clip + dig clip active (compose).
 6. vc-underground on -> armed; close excavate -> STILL armed (composition); vc off -> disarmed.
 7. Terrain dock Dig brush -> armed; Raise -> disarmed (Sprint 20 behavior preserved).
 8. No page errors.

Pixel analysis via PIL hue-band classification:
- grass 0x5ba06d = (91,160,109); topsoil 0x4a301e; subsoil 0x9b7a4f;
  clay 0xa04224 -> x1.45 boost = (232,96,52); bedrock 0x606068 -> (139,139,151)
- underground vertices get 1.45x brightness boost, so bands are generous.
"""
import json
import os
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

URL = os.environ.get("BASE_URL", "http://localhost:8311") + "/index.html"
DIR = "/tmp/s21-digvis"
os.makedirs(DIR, exist_ok=True)

RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})
    print(("PASS  " if ok else "FAIL  ") + name + ("  -- " + str(detail)[:180] if detail else ""))


def classify_pixels(png_path, max_dim=420):
    img = Image.open(png_path).convert("RGB")
    img.thumbnail((max_dim, max_dim))
    px = img.load()
    w, h = img.size
    c = {"sky": 0, "grass": 0, "brown": 0, "clay": 0, "bedrock": 0, "other": 0, "total": 0}
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            c["total"] += 1
            if b > r + 20 and b > g - 10:
                c["sky"] += 1
            elif g > r + 12 and g > b + 18:
                c["grass"] += 1
            elif r > b + 18 and g > b + 6 and abs(r - g) < 75 and r < 236 and g < 226 and b < 191:
                c["brown"] += 1
            elif r > g + 40 and g > b + 10 and r > 120:
                c["clay"] += 1
            elif abs(r - g) < 16 and abs(g - b) < 20 and 70 < r < 210 and b >= g - 8:
                c["bedrock"] += 1
            else:
                c["other"] += 1
    return c


def frac(c, key):
    return c[key] / max(1, c["total"])


def geo_frac(c):
    return frac(c, "brown") + frac(c, "clay") + frac(c, "bedrock")


def diag(page):
    return page.evaluate("() => window._groundVisibilityDebug ? window._groundVisibilityDebug() : null")


def set_camera(page):
    # window.controls / window.camera3D are exported globally (line ~17311).
    page.evaluate("""() => {
        const c = window.controls, cam = window.camera3D;
        if (!c || !cam) return;
        c.target.set(0, -4, 0);
        cam.position.set(0, 12, 55);
        c.update();
    }""")
    page.wait_for_timeout(300)


def dig_two_holes(page):
    page.evaluate("""() => {
        const t = window._test;
        if (!t.state.terrain) t.ensureTerrainArray();
        const segs = t.state.terrainSegs;
        const W = t.state.yard.width, D = t.state.yard.depth;
        const holes = [
            {cx: -10, cz: -15, r: 9, depth: -9},
            {cx: 12, cz: 20, r: 8, depth: -7},
        ];
        for (const hole of holes) {
            for (let iz = 0; iz <= segs; iz++) {
                for (let ix = 0; ix <= segs; ix++) {
                    const wx = (ix / segs) * W - W / 2;
                    const wz = (iz / segs) * D - D / 2;
                    const dx = wx - hole.cx, dz = wz - hole.cz;
                    const d = Math.sqrt(dx * dx + dz * dz);
                    if (d < hole.r) {
                        const t2 = d / hole.r;
                        const fall = (1 - t2 * t2) * (1 - t2 * t2);
                        const idx = iz * (segs + 1) + ix;
                        t.state.terrain[idx] = Math.min(t.state.terrain[idx], hole.depth * fall);
                    }
                }
            }
        }
        t.applyTerrainFull();
    }""")
    page.wait_for_timeout(700)


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--use-gl=swiftshader",
                  "--enable-unsafe-swiftshader"],
        )
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.on("pageerror", lambda e: errors.append(str(e)))

        page.goto(URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1200)
        page.evaluate("""() => {
            const w = document.getElementById('wizard');
            if (w) w.style.display = 'none';
            const wp = document.getElementById('welcome-prompt');
            if (wp) wp.style.display = 'none';
        }""")
        page.wait_for_timeout(400)

        dig_two_holes(page)
        # Basic mode hides the Underground dock tab — switch to Advanced via the real toggle.
        adv = page.locator("#mode-toggle button[data-mode='advanced']")
        if adv.count() > 0:
            adv.click()
            page.wait_for_timeout(500)
        set_camera(page)
        page.screenshot(path=f"{DIR}/0_before.png")
        before = classify_pixels(f"{DIR}/0_before.png")
        print("BEFORE bands:", json.dumps(before))
        record("setup:grass_visible_before", frac(before, "grass") > 0.05,
               f"grass frac={frac(before, 'grass'):.3f}")

        # -- 1. Underground dock tab (real CDP click) --------------------------
        page.locator('.td-tab[data-dock="underground"]').click(timeout=5000)
        page.wait_for_timeout(600)
        dock_visible = page.evaluate(
            "() => document.getElementById('dock-underground').classList.contains('visible')")
        d = diag(page)
        print("after dock open diag:", json.dumps(d))
        record("dock:underground_opens", dock_visible)
        record("dock:clip_armed_on_open", bool(d and d.get("autoDigClipActive")), f"diag={d}")

        page.screenshot(path=f"{DIR}/1_dock_open.png")
        b1 = classify_pixels(f"{DIR}/1_dock_open.png")
        print("dock open bands:", json.dumps(b1))
        record("dock:geo_colors_in_pixels", geo_frac(b1) > geo_frac(before),
               f"geo {geo_frac(before):.4f} -> {geo_frac(b1):.4f} (brown={b1['brown']} clay={b1['clay']} bedrock={b1['bedrock']})")
        record("dock:grass_pixels_dropped", frac(b1, "grass") < frac(before, "grass"),
               f"grass {frac(before, 'grass'):.4f} -> {frac(b1, 'grass'):.4f}")

        # -- 2. Excavate button click (owner's route) --------------------------
        # The dock tab already set excavatePanelVisible=true (shared canonical state),
        # so first close it via excavate-close, then verify the excavate-btn route
        # arms the clip on its own (panel starts closed, like a fresh session).
        page.evaluate("() => document.getElementById('excavate-close').click()")
        page.wait_for_timeout(300)
        page.evaluate("() => document.getElementById('excavate-btn').click()")
        page.wait_for_timeout(600)
        d = diag(page)
        page.screenshot(path=f"{DIR}/2_excavate_open.png")
        b2 = classify_pixels(f"{DIR}/2_excavate_open.png")
        print("excavate open diag:", json.dumps(d), "bands:", json.dumps(b2))
        record("excavate:clip_armed", bool(d and d.get("autoDigClipActive")), f"diag={d}")
        record("excavate:geo_colors_in_pixels", geo_frac(b2) > geo_frac(before),
               f"geo {geo_frac(before):.4f} -> {geo_frac(b2):.4f}")

        # -- 3. Close -> grass restored ----------------------------------------
        # NOTE: vc-underground's off-branch restores opacity from the slider even while
        # the excavate panel is open, so to assert clean grass restoration we first
        # leave underground view (no-op here), then close the panel via excavate-close.
        page.evaluate("() => document.getElementById('excavate-close').click()")
        page.wait_for_timeout(600)
        d = diag(page)
        page.screenshot(path=f"{DIR}/3_after_close.png")
        b3 = classify_pixels(f"{DIR}/3_after_close.png")
        print("after close diag:", json.dumps(d), "bands:", json.dumps(b3))
        record("close:clip_disarmed", bool(d and not d.get("autoDigClipActive")), f"diag={d}")

        # -- 4. Reopen + cutaway slider composes with dig clip -----------------
        page.evaluate("() => document.getElementById('excavate-btn').click()")
        page.wait_for_timeout(400)
        cut = page.locator("#terrain-cutaway")
        cut.evaluate("el => { el.value = 45; el.dispatchEvent(new Event('input', {bubbles:true})); }")
        page.wait_for_timeout(500)
        d = diag(page)
        page.screenshot(path=f"{DIR}/4_cutaway_compose.png")
        print("cutaway+dig diag:", json.dumps(d))
        record("compose:cutaway_and_dig_both_active",
               bool(d and d.get("autoDigClipActive") and d.get("terrainClipActive")), f"diag={d}")
        cut.evaluate("el => { el.value = 0; el.dispatchEvent(new Event('input', {bubbles:true})); }")
        page.wait_for_timeout(300)

        # -- 5. vc-underground composition -------------------------------------
        page.evaluate("() => document.getElementById('vc-underground').click()")
        page.wait_for_timeout(700)
        ug = page.evaluate("() => window._test.undergroundViewActive")
        d = diag(page)
        record("vc-underground:arms_clip", ug is True and bool(d and d.get("autoDigClipActive")), f"diag={d}")
        # Close excavate while underground view active -> clip must STAY armed
        page.evaluate("() => document.getElementById('excavate-btn').click()")
        page.wait_for_timeout(400)
        d = diag(page)
        record("compose:excavate_close_keeps_clip_while_underground",
               bool(d and not d.get("excavatePanelVisible") and d.get("autoDigClipActive")), f"diag={d}")
        # vc off -> nothing else active -> disarm
        page.evaluate("() => document.getElementById('vc-underground').click()")
        page.wait_for_timeout(400)
        d = diag(page)
        record("vc-underground:off_disarms", bool(d and not d.get("autoDigClipActive")), f"diag={d}")

        # -- 5b. Clean-state grass restoration ---------------------------------
        # Everything is off again. Close the still-open Underground dock via its tab
        # (real user path; triggers closeDockPanel -> updateGroundVisibility), then
        # re-aim the camera (vc-underground's off path reset it) and verify the
        # normal grass surface is back in the pixels.
        page.locator('.td-tab[data-dock="underground"]').click()
        page.wait_for_timeout(500)
        set_camera(page)
        page.screenshot(path=f"{DIR}/5_restored.png")
        b5 = classify_pixels(f"{DIR}/5_restored.png")
        record("close:grass_restored", frac(b5, "grass") >= frac(before, "grass") - 0.02,
               f"grass {frac(b5, 'grass'):.4f} vs before {frac(before, 'grass'):.4f}")

        # -- 6. Terrain dock Dig brush regression ------------------------------
        page.locator('.td-tab[data-dock="terrain"]').click()
        page.wait_for_timeout(400)
        dig_btn = page.locator('.terrain-mode-btn[data-tmode="dig"]')
        if dig_btn.count() > 0:
            dig_btn.click()
            page.wait_for_timeout(500)
            d = diag(page)
            record("digbrush:arms_clip", bool(d and d.get("autoDigClipActive")), f"diag={d}")
            page.locator('.terrain-mode-btn[data-tmode="raise"]').click()
            page.wait_for_timeout(400)
            d = diag(page)
            record("digbrush:raise_disarms", bool(d and not d.get("autoDigClipActive")), f"diag={d}")
        else:
            record("digbrush:arms_clip", False, "dig mode button not found")

        if errors:
            record("console:no_page_errors", False, "; ".join(errors[:3]))
        else:
            record("console:no_page_errors", True)

        browser.close()

    n_pass = sum(1 for r in RESULTS if r["ok"])
    print(f"\n== {n_pass}/{len(RESULTS)} passed ==")
    Path(f"{DIR}/results.json").write_text(json.dumps(RESULTS, indent=2))
    return 0 if n_pass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
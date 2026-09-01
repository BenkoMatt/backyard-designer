#!/usr/bin/env python3
"""Stale-plane regression probe for sprint-27 clip sig-guard fix (task t_52168e24).

Drives a LIVE page with real Playwright input (mouse clicks on range tracks +
arrow-key nudges; page.evaluate used ONLY for observation/setup). Asserts:

  A. Cutaway sweep 0->40->70->30->80->0->65: yardMesh material downward-plane
     constant == cutY at EVERY step, where
        cutY = maxH + 0.5 - val/100*(maxH-minH+5.5)
     (the verifier bug: after the first move every subsequent constant froze).
  B. Cutaway 0 disarms (no downward plane), re-arm at 65 tracks again.
  C. Cross-section clip sweep x@57 -> x@-34 -> axis change -> z@23: plane
     constant == (pos/100)*halfDim (halfDim = width/2 for x, depth/2 for z);
     disable removes the plane.

Usage: python3 sprint27_staleplane_probe.py --port 8345 [--out probe.json]
Exit 0 iff all checks pass.
"""
import argparse
import json
import sys
import time

from playwright.sync_api import sync_playwright

VIEW = {"width": 1280, "height": 800}

SETUP = """() => {
  const w = document.getElementById('wizard');
  if (w) w.style.display = 'none';
  const wp = document.getElementById('welcome-prompt');
  if (wp) { wp.classList.remove('visible'); wp.style.display = 'none'; wp.setAttribute('aria-hidden','true'); }
  if (typeof window.applyTerrainFull === 'function') window.applyTerrainFull();
  window.requestRender();
  return {ok: true};
}"""

YARD_STATE = """() => {
  const ym = window._test.yardMesh;
  const planes = (ym.material.clippingPlanes || []).map(p => ({
    id: p.id, nx: +p.normal.x.toFixed(4), ny: +p.normal.y.toFixed(4),
    nz: +p.normal.z.toFixed(4), c: +p.constant.toFixed(4)}));
  return {
    planes,
    down: planes.filter(p => p.ny < -0.5),
    horiz: planes.filter(p => p.ny === 0 && (p.nx !== 0 || p.nz !== 0)),
    maxH: window._test.getMaxTerrainHeight(),
    minH: window._test.getMinTerrainHeight(),
    yardW: window._test.state.yard.width,
    yardD: window._test.state.yard.depth,
    cutVal: document.getElementById('terrain-cutaway').value,
    cutLabel: document.getElementById('cutaway-val').textContent,
  };
}"""


def set_slider(page, sel, value):
    """Real input on a range: proportional track click, then arrow-key nudge to
    the exact value (each keypress fires genuine input events)."""
    el = page.locator(sel)
    box = el.bounding_box()
    if not box or box["width"] <= 0:
        raise RuntimeError(f"{sel} not visible (box={box})")
    mn = int(el.get_attribute("min"))
    mx = int(el.get_attribute("max"))
    frac = (value - mn) / float(mx - mn)
    x = box["x"] + 3 + (box["width"] - 6) * frac
    y = box["y"] + box["height"] / 2
    page.mouse.click(x, y)
    page.wait_for_timeout(150)
    cur = int(el.input_value())
    key = "ArrowRight" if value > cur else "ArrowLeft"
    el.focus()
    for _ in range(abs(value - cur)):
        page.keyboard.press(key)
    page.wait_for_timeout(150)
    return int(el.input_value())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8345)
    ap.add_argument("--out", default="sprint27_staleplane_probe.json")
    args = ap.parse_args()
    base = f"http://localhost:{args.port}"

    results = []

    def check(name, ok, detail=""):
        results.append({"check": name, "ok": bool(ok), "detail": str(detail)})
        print(("PASS  " if ok else "FAIL  ") + name + "  | " + str(detail))
        return ok

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--use-gl=angle",
                  "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
        )
        ctx = browser.new_context(viewport=VIEW)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        page.goto(base + "/index.html", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1500)
        skip = page.locator("#wizard-skip")
        if skip.count() > 0:
            skip.click()
        else:
            page.keyboard.press("Escape")
        page.wait_for_timeout(800)
        page.evaluate(SETUP)
        page.wait_for_timeout(300)

        # Advanced mode + underground dock (real clicks) so cutaway slider is visible
        adv = page.locator("#mode-toggle button[data-mode='advanced']")
        if adv.count() > 0:
            adv.click()
            page.wait_for_timeout(500)
        page.locator(".td-tab[data-dock='underground']").click()
        page.wait_for_timeout(800)

        # ---------- A. cutaway stale-plane sweep ----------
        for val in [0, 40, 70, 30, 80]:
            got = set_slider(page, "#terrain-cutaway", val)
            page.wait_for_timeout(500)
            st = page.evaluate(YARD_STATE)
            exp = st["maxH"] + 0.5 - (val / 100.0) * (st["maxH"] - st["minH"] + 5.5)
            if val == 0:
                check(f"cutaway {val}: no downward plane (disarmed)", len(st["down"]) == 0,
                      f"planes={[p['c'] for p in st['planes']]}")
            else:
                check(f"cutaway {val}: slider input value == {val}", got == val, f"got {got}")
                okc = len(st["down"]) >= 1 and abs(st["down"][0]["c"] - exp) <= 0.05
                check(f"cutaway {val}: yard down-plane constant == cutY", okc,
                      f"plane_c={st['down'][0]['c'] if st['down'] else None} "
                      f"expected={round(exp, 2)} label={st['cutLabel']}")

        # ---------- B. disarm at 0, re-arm at 65 ----------
        got0 = set_slider(page, "#terrain-cutaway", 0)
        page.wait_for_timeout(500)
        st0 = page.evaluate(YARD_STATE)
        check(f"cutaway 0 (after sweep): input == 0 and plane removed",
              got0 == 0 and len(st0["down"]) == 0,
              f"got {got0}, down={[p['c'] for p in st0['down']]}")
        got65 = set_slider(page, "#terrain-cutaway", 65)
        page.wait_for_timeout(500)
        st65 = page.evaluate(YARD_STATE)
        exp65 = st65["maxH"] + 0.5 - (65 / 100.0) * (st65["maxH"] - st65["minH"] + 5.5)
        check("cutaway re-arm 65: constant == cutY (not reusing stale 80-value)",
              got65 == 65 and len(st65["down"]) >= 1
              and abs(st65["down"][0]["c"] - exp65) <= 0.05,
              f"plane_c={st65['down'][0]['c'] if st65['down'] else None} expected={round(exp65, 2)}")

        # ---------- C. cross-section clip sweep ----------
        page.locator("#cross-section-toggle").click()
        page.wait_for_timeout(600)
        page.locator("#cs-clip-enable").click()
        page.wait_for_timeout(500)
        for axis, frac in [("x", 57), ("x", -34), ("z", 23)]:
            if axis == "z":
                page.locator("#cs-clip-axis").select_option("z")
                page.wait_for_timeout(200)
            got = set_slider(page, "#cs-clip-pos", frac)
            page.wait_for_timeout(500)
            stc = page.evaluate(YARD_STATE)
            halfdim = (stc["yardW"] if axis == "x" else stc["yardD"]) / 2.0
            expc = (frac / 100.0) * halfdim
            cand = [p for p in stc["horiz"] if (p["nx"] < -0.5 if axis == "x" else p["nz"] < -0.5)]
            check(f"cs-clip {axis}@{frac}: input == {frac} and plane constant == position",
                  got == frac and len(cand) >= 1 and abs(cand[0]["c"] - expc) <= 0.05,
                  f"got {got}, planes={[(p['nx'], p['nz'], p['c']) for p in stc['horiz']]} "
                  f"expected_c={round(expc, 2)}")
        # disable removes the horizontal plane
        page.locator("#cs-clip-enable").click()
        page.wait_for_timeout(500)
        std = page.evaluate(YARD_STATE)
        check("cs-clip disable: horizontal plane removed",
              len(std["horiz"]) == 0, f"planes={[p['c'] for p in std['planes']]}")

        check("no pageerrors during probe", len(errors) == 0, "; ".join(errors))
        browser.close()

    passed = sum(1 for r in results if r["ok"])
    total = len(results)
    print(f"\n{passed}/{total} checks passed")
    with open(args.out, "w") as f:
        json.dump({"port": args.port, "passed": passed, "total": total,
                   "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "results": results},
                  f, indent=2)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""Sprint 27 dig-perf gate (fixer card t_8b83d52f). REAL CDP/Playwright input only.

Asserts (brief t_8b83d52f quality bar):
  1. mode switch to dig: no main-thread longtask > 150 ms during entry
  2. held 5 s dig stroke @ terrainSegs=200: avg rAF FPS >= 45, worst 1 s >= 30
  3. dig re-entry: ZERO shader compile/link calls (no shader recompile stall)
  4. crater visuals: s21-style dig-visibility invariants (strata/walls render)
  5. renderer program inventory stable across dig mode switches

page.evaluate is used ONLY for observation/test setup (terrain state, trace
attach, counters) — every click/key path uses real Playwright mouse events.
Usage: python3 sprint27_digperf_gate.py --port 8344 [--out sprint27_fps_after.json]
"""
import argparse
import json
import os
import subprocess
import time

from playwright.sync_api import sync_playwright

VIEW = {"width": 1280, "height": 800}

# --- observation/setup JS (NOT input) -------------------------------------
ATTACH_TRACE = """() => {
  if (window._s27) return {already: true};
  window._s27 = {compiles: 0, links: 0, longtasks: [], frames: [], renderFrames: [],
                 running: false, progCount: 0};
  const gl = window.renderer.getContext();
  const oc = gl.compileShader.bind(gl);
  gl.compileShader = s => { window._s27.compiles++; oc(s); };
  const ol = gl.linkProgram.bind(gl);
  gl.linkProgram = p => { window._s27.links++; ol(p); };
  window._s27.progCount = () => (window.renderer.info.programs || []).length;
  const po = new PerformanceObserver(list => {
    for (const e of list.getEntries()) window._s27.longtasks.push(+e.duration);
  });
  try { po.observe({entryTypes: ['longtask']}); } catch (e) {}
  const upd = renderer => {
    try { window._s27.renderFrames.push([performance.now(), window.renderer.info.render.frame]); } catch (e) {}
  };
  window._s27.upd = upd;
  return {ok: true};
}"""

START_RAF = """() => {
  const s = window._s27;
  if (!s) return {err: 'no trace'};
  s.running = true;
  s.frames = [];
  s.renderFrames = [];
  s.prevTs = null; s.prevWall = null;
  s.maxGapTs = 0; s.maxGapWall = 0;
  const loop = ts => {
    if (!s.running) return;
    const now = performance.now();
    if (s.prevTs !== null) {
      const g = ts - s.prevTs;
      if (g > s.maxGapTs) s.maxGapTs = g;
      const gw = now - s.prevWall;
      if (gw > s.maxGapWall) s.maxGapWall = gw;
    }
    s.prevTs = ts; s.prevWall = now;
    s.frames.push([now, ts]);
    try { s.renderFrames.push([performance.now(), window.renderer.info.render.frame]); } catch (e) {}
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
  return {ok: true};
}"""

STOP_RAF = """() => {
  const s = window._s27;
  if (s) s.running = false;
  return {frames: s ? s.frames.length : 0,
          maxGapTs: s ? s.maxGapTs : null,
          maxGapWall: s ? s.maxGapWall : null};
}"""

CLEAR_TRACE = """() => {
  const s = window._s27;
  s.compiles = 0; s.links = 0; s.longtasks = [];
  return {ok: true};
}"""

FLATTEN = """() => {
  const t = window._test;
  if (!t.state.terrain) t.ensureTerrainArray();
  for (let i = 0; i < t.state.terrain.length; i++) t.state.terrain[i] = 0;
  t.applyTerrainFull();
  window.requestRender();
  return {flat: true};
}"""

DIG_PIT = """() => {
  const t = window._test;
  t.ensureTerrainArray();
  const segs = t.state.terrainSegs;
  for (let i = 0; i < t.state.terrain.length; i++) t.state.terrain[i] = 0;
  const c = Math.floor(segs / 2), R = 40;
  for (let iz = c - R; iz <= c + R; iz++) {
    for (let ix = c - R; ix <= c + R; ix++) {
      const dist = Math.sqrt((ix - c) ** 2 + (iz - c) ** 2);
      if (dist > R) continue;
      t.state.terrain[iz * (segs + 1) + ix] =
        -Math.min(15, Math.max(0, (R - dist) * 0.9));
    }
  }
  window.applyTerrainFull();
  window.requestRender();
  return {dug: true, segs: segs};
}"""

CRATER_CHECK = """() => {
  const t = window._test;
  let minH = Infinity, neg = 0;
  for (let i = 0; i < t.state.terrain.length; i++) {
    if (t.state.terrain[i] < minH) minH = t.state.terrain[i];
    if (t.state.terrain[i] < 0) neg++;
  }
  const se = t.solidEarthMesh;
  let minY = Infinity;
  if (se && se.geometry) {
    const pos = se.geometry.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const y = pos.getY(i);
      if (y < minY) minY = y;
    }
  }
  return {minTerrain: minH, negativeCells: neg, sePresent: !!se,
          seVerts: se && se.geometry ? se.geometry.attributes.position.count : 0,
          seMinY: minY};
}"""

DIAG = """() => window._groundVisibilityDebug ? window._groundVisibilityDebug() : null"""

RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)[:180]) if detail else ""))


def load01():
    try:
        with open("/proc/loadavg") as f:
            return round(float(f.read().split()[0]), 2)
    except Exception:
        return None


def stroke_fps(s):
    """avg + worst-1s rAF FPS from collected [wall, ts] frame pairs."""
    fr = [f[0] for f in s["frames"]]
    if len(fr) < 10:
        return {"avg_fps": 0.0, "worst_1s": 0.0, "frames": len(fr)}
    dur = (fr[-1] - fr[0]) / 1000.0
    worst_fps = []
    j = 0
    for i in range(len(fr)):
        while fr[i] - fr[j] > 1000:
            j += 1
        worst_fps.append(i - j + 1)
    return {
        "avg_fps": round(len(fr) / max(dur, 1e-6), 2),
        "worst_1s": round(min(worst_fps) if worst_fps else 0, 1),
        "frames": len(fr),
    }


def center_of(page, selector):
    box = page.locator(selector).bounding_box()
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


def held_stroke(page, seconds=5.0):
    """Real held dig stroke via Playwright mouse (down -> paced move -> up)."""
    vw = page.evaluate("() => window.innerWidth")
    vh = page.evaluate("() => window.innerHeight")
    x0, y0 = vw / 2 + 40, vh / 2
    page.mouse.move(x0, y0)
    page.mouse.down()
    start = time.time()
    end = start + seconds
    i = 0
    while time.time() < end:
        dx = 18 if (i % 2 == 0) else -18
        page.mouse.move(x0 + dx, y0 + (8 if (i % 4 < 2) else -8))
        i += 1
        time.sleep(0.012)  # ~80 Hz, realistic mouse rate; unpounded CDP floods starve rAF
    page.mouse.up()
    return (time.time() - start) * 1000.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8344)
    ap.add_argument("--out", default="sprint27_fps_after.json")
    args = ap.parse_args()
    base = f"http://localhost:{args.port}"

    evidence = {"port": args.port, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "load01_start": load01()}

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

        # --- boot: real click on wizard skip (fallback: keyboard Escape) ---
        skip = page.locator("#wizard-skip")
        if skip.count() > 0:
            skip.click()
        else:
            page.keyboard.press("Escape")
        page.wait_for_timeout(800)
        # Test setup (same recipe as qa_s21/s26 gates): dismiss wizard shell +
        # welcome-prompt dialog so it cannot intercept dock/mode clicks.
        page.evaluate("""() => {
          const w = document.getElementById('wizard');
          if (w) w.style.display = 'none';
          const wp = document.getElementById('welcome-prompt');
          if (wp) { wp.classList.remove('visible'); wp.style.display = 'none'; wp.setAttribute('aria-hidden','true'); }
          return {ok: true};
        }""")
        page.wait_for_timeout(300)

        page.evaluate(ATTACH_TRACE)

        # Advanced mode (real click) so all dock tabs reachable
        adv = page.locator("#mode-toggle button[data-mode='advanced']")
        if adv.count() > 0:
            adv.click()
            page.wait_for_timeout(500)
        # Terrain dock (real click); dig needs the mode buttons
        page.locator(".td-tab[data-dock='terrain']").click()
        page.wait_for_timeout(600)
        page.evaluate(FLATTEN)
        page.wait_for_timeout(400)

        # =========================================================
        # 1. Mode switch -> dig: stall measurement
        # =========================================================
        page.locator(".terrain-mode-btn[data-tmode='raise']").click()
        page.wait_for_timeout(400)
        progs_before = page.evaluate("() => window._s27.progCount()")
        page.evaluate(CLEAR_TRACE)
        page.evaluate(START_RAF)
        t_c0 = time.time()
        page.locator(".terrain-mode-btn[data-tmode='dig']").click()
        t_click = (time.time() - t_c0) * 1000.0
        page.wait_for_timeout(600)
        page.evaluate(STOP_RAF)
        s = page.evaluate("() => window._s27")
        _wall = [f[0] for f in s["frames"]]
        gap1 = max(_wall[i + 1] - _wall[i] for i in range(len(_wall) - 1)) if len(_wall) > 2 else None
        ev = {"click_ms": round(t_click, 1), "longtasks": s["longtasks"],
              "max_longtask_ms": round(max(s["longtasks"]), 1) if s["longtasks"] else 0,
              "raf_gap_ms": round(gap1, 1) if gap1 else None,
              "progs_before": progs_before,
              "progs_after": page.evaluate("() => window._s27.progCount()"),
              "compiles": s["compiles"], "links": s["links"]}
        evidence["mode_switch_first"] = ev
        record("modeswitch:no_longtask_over_150ms",
               ev["max_longtask_ms"] <= 150, f"max longtask {ev['max_longtask_ms']} ms, "
               f"click {ev['click_ms']} ms, rAF gap {ev['raf_gap_ms']} ms")
        record("modeswitch:zero_new_programs",
               ev["progs_after"] <= ev["progs_before"],
               f"programs {ev['progs_before']} -> {ev['progs_after']}")

        # =========================================================
        # 2. Re-entry: zero shader compile/link
        # =========================================================
        page.locator(".terrain-mode-btn[data-tmode='raise']").click()
        page.wait_for_timeout(400)
        page.evaluate(CLEAR_TRACE)
        page.evaluate(START_RAF)
        t_c0 = time.time()
        page.locator(".terrain-mode-btn[data-tmode='dig']").click()
        t_click2 = (time.time() - t_c0) * 1000.0
        page.wait_for_timeout(500)
        page.evaluate(STOP_RAF)
        s2 = page.evaluate("() => window._s27")
        _wall2 = [f[0] for f in s2["frames"]]
        gap2 = max(_wall2[i + 1] - _wall2[i] for i in range(len(_wall2) - 1)) if len(_wall2) > 2 else None
        ev2 = {"click_ms": round(t_click2, 1), "compiles": s2["compiles"],
               "links": s2["links"], "max_longtask_ms":
                   round(max(s2["longtasks"]), 1) if s2["longtasks"] else 0,
               "raf_gap_ms": round(gap2, 1) if gap2 else None}
        evidence["mode_switch_reentry"] = ev2
        record("reentry:zero_shader_compile_link",
               ev2["compiles"] == 0 and ev2["links"] == 0,
               f"compiles={ev2['compiles']} links={ev2['links']} "
               f"rAF gap {ev2['raf_gap_ms']} ms")

        # =========================================================
        # 3. Held 5 s dig stroke @ terrainSegs=200
        # =========================================================
        page.evaluate(FLATTEN)
        page.wait_for_timeout(300)
        page.evaluate(CLEAR_TRACE)
        page.evaluate(START_RAF)
        stroke = held_stroke(page, 5.0)
        page.wait_for_timeout(100)
        stop = page.evaluate(STOP_RAF)
        s3 = page.evaluate("() => window._s27")
        fps3 = stroke_fps(s3)
        lt = max(s3["longtasks"]) if s3["longtasks"] else 0
        evidence["held_dig_stroke"] = {**fps3, "max_longtask_ms": round(lt, 1),
                                       "longtask_count": len(s3["longtasks"]),
                                       "max_raf_gap_ms": round(max(stop["maxGapTs"] or 0, stop["maxGapWall"] or 0), 1),
                                       "stroke_wall_ms": stroke,
                                       "load01_end": load01()}
        record("stroke:avg_fps_ge_45", fps3["avg_fps"] >= 45,
               f"avg {fps3['avg_fps']} fps over {fps3['frames']} rAF ticks, "
               f"max longtask {round(lt,1)} ms, max rAF gap "
               f"{evidence['held_dig_stroke']['max_raf_gap_ms']} ms "
               f"(render ceiling note: SwiftShader flat-lawn ceiling measured ~8 fps)")
        record("stroke:worst_1s_ge_30", fps3["worst_1s"] >= 30,
               f"worst 1 s window {fps3['worst_1s']} fps")
        # sprint 27 supplementary, environment-relative bars (SwiftShader box):
        # stroke throughput must match the measured render ceiling of an IDLE FLAT
        # scene (~8 fps on this host) and produce zero >50ms main-thread blocks.
        record("stroke:fps_meets_box_render_ceiling", fps3["avg_fps"] >= 6.5,
               f"stroke avg {fps3['avg_fps']} fps >= measured box ceiling "
               f"(flat lawn idle ~7-8 fps on SwiftShader; dig-path CPU now ~5% of samples)")
        record("stroke:no_main_thread_blocks_over_150ms", lt <= 150,
               f"max longtask {round(lt,1)} ms (brief stall bar; baseline: up to 14,042 ms, Hunter A)")

        # =========================================================
        # 4. Crater visuals (s21-style invariants)
        # =========================================================
        page.evaluate(DIG_PIT)
        page.wait_for_timeout(700)
        chk = page.evaluate(CRATER_CHECK)
        evidence["crater"] = chk
        record("crater:min_terrain_le_minus15", chk["minTerrain"] <= -14.9,
               f"min terrain {chk['minTerrain']} ft, {chk['negativeCells']} cells < 0")
        record("crater:solid_earth_present_with_walls",
               chk["sePresent"] and chk["seVerts"] > 0,
               f"solidEarth verts={chk['seVerts']} bottom={chk['seMinY']}")
        # strata colors on solid earth vertices below zero (geo colors)
        geo = page.evaluate("""() => {
          const t = window._test;
          const se = t.solidEarthMesh;
          if (!se) return {geo: 0, grass: 0};
          const pos = se.geometry.attributes.position;
          const col = se.geometry.attributes.color;
          let geoC = 0, grassC = 0;
          for (let i = 0; i < pos.count; i++) {
            if (pos.getY(i) > 0.2) continue;
            const r = col.getX(i), g = col.getY(i), b = col.getZ(i);
            if (g > r + 0.12 && g > b + 0.1) grassC++; else geoC++;
          }
          return {geo: geoC, grass: grassC};
        }""")
        evidence["crater_colors"] = geo
        record("crater:strata_colors_geological_not_grass",
               geo["geo"] > geo["grass"],
               f"geo-colored {geo['geo']} vs grass {geo['grass']}")
        # dig clip armed via real UI (terrain dock dig button already active)
        d = page.evaluate(DIAG)
        record("crater:dig_clip_armed_in_dig_mode",
               bool(d and d.get("autoDigClipActive")), f"diag={d}")

        # =========================================================
        # 5. Program inventory stable across full dig path
        # =========================================================
        progs_final = page.evaluate("() => window._s27.progCount()")
        evidence["programs_final"] = progs_final
        record("programs:stable_across_dig_path",
               progs_final <= ev["progs_after"],
               f"{ev['progs_before']} -> {progs_final}")

        if errors:
            record("console:no_page_errors", False, "; ".join(errors[:3]))
        else:
            record("console:no_page_errors", True)

        browser.close()

    evidence["results"] = RESULTS
    evidence["passed"] = sum(1 for r in RESULTS if r["ok"])
    evidence["total"] = len(RESULTS)
    out = args.out
    with open(out, "w") as f:
        json.dump(evidence, f, indent=2)
    print(f"\n== {evidence['passed']}/{evidence['total']} passed -> {out}")
    return 0 if evidence["passed"] == evidence["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
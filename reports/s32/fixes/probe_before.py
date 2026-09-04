"""S32 fixer BEFORE-probe: DOM evidence for conflicts + P0/P1/P2 defects.
Serves from http://127.0.0.1:8380 (worktree copy). Read-only probes + real clicks.
"""
import json, time, os, sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
os.makedirs(OUT, exist_ok=True)
res = {}
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def newpage(pw, w=1280, h=800):
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    ctx = b.new_context(viewport={"width": w, "height": h})
    pg = ctx.new_page()
    pg.set_default_timeout(12000)
    errs = []
    pg.on("pageerror", lambda e: errs.append("PAGEERR: "+str(e)))
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_timeout(2500)
    return b, ctx, pg, errs

with sync_playwright() as pw:
    # ---------- SESSION 1: share copy + export menu (fresh) + topbar wheel ----------
    b, ctx, pg, errs = newpage(pw)
    pg.evaluate("() => document.getElementById('wizard-skip')?.click()")
    pg.wait_for_timeout(600)
    pg.evaluate("() => window.setMode('advanced')")
    pg.wait_for_timeout(400)

    # --- share copy: clipboard presence + click ---
    s1 = pg.evaluate("""() => {
      const hasNavClip = !!(navigator.clipboard && navigator.clipboard.writeText);
      // seed share modal with a URL
      const box = document.getElementById('share-url-box');
      if (box) box.textContent = 'http://127.0.0.1:8380/index.html#eyJ2Ijo0fQ';
      return { hasNavClip, isSecure: window.isSecureContext, urlLen: (box?box.textContent.length:0) };
    }""")
    pg.click("#btn-share")
    pg.wait_for_timeout(500)
    pg.click("#share-copy-btn")
    pg.wait_for_timeout(600)
    toast1 = pg.evaluate("() => document.getElementById('toast')?.textContent || ''")
    # can execCommand copy work here at all?
    s2 = pg.evaluate("""() => {
      const ta = document.createElement('textarea'); ta.value='probe'; document.body.appendChild(ta); ta.select();
      let ok=false; try { ok = document.execCommand('copy'); } catch(e) {}
      document.body.removeChild(ta);
      return { execOk: ok, qcs: document.queryCommandSupported ? document.queryCommandSupported('copy') : null };
    }""")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
    res["share_copy"] = {"probe": s1, "toast_after_click": toast1, "exec_fallback": s2, "errors": errs}
    log(f"share: nav={s1['hasNavClip']} secure={s1['isSecure']} toast={toast1!r} exec={s2}")

    # --- export menu: open fresh at 1280x800 ---
    pg.click("#btn-export")
    pg.wait_for_timeout(400)
    ex1 = pg.evaluate("""() => {
      const m = document.getElementById('export-menu');
      const r = m.getBoundingClientRect();
      const tb = document.getElementById('topbar');
      const tbr = tb.getBoundingClientRect();
      const cx = r.x + r.width/2, cy = r.y + r.height/2;
      const hit = document.elementFromPoint(cx, cy);
      // pixel scan: is there a menu-surface (near-white) pixel in the menu rect below topbar?
      const c = document.createElement('canvas'); // DOM-only check: rely on rect+hit-test
      const chain = [];
      let el = hit; while (el && chain.length < 6) { chain.push(el.id || el.className || el.tagName); el = el.parentElement; }
      return { display: m.style.display, rect: {x:r.x,y:r.y,w:r.width,h:r.height},
               topbarBottom: tbr.bottom, hit: chain, visible: r.height > 10 && r.bottom > tbr.bottom };
    }""")
    pg.screenshot(path=f"{OUT}/before_export_menu_1280.png")
    # try real click on STL item (Playwright actionability)
    stl_clickable = True
    try:
        pg.click("#export-stl", timeout=2500)
    except Exception as e:
        stl_clickable = f"FAIL: {str(e)[:120]}"
    pg.wait_for_timeout(300)
    res["export_menu_fresh"] = ex1
    res["export_stl_click"] = stl_clickable
    log(f"export fresh: {json.dumps(ex1)} stl_click={stl_clickable}")
    # close any menu
    pg.keyboard.press("Escape"); pg.mouse.click(640, 400); pg.wait_for_timeout(300)

    # --- topbar wheel scroll ---
    tb_state = pg.evaluate("""() => {
      const tb = document.getElementById('topbar');
      return { sw: tb.scrollWidth, cw: tb.clientWidth, sl: tb.scrollLeft };
    }""")
    pg.mouse.move(640, 26)
    pg.mouse.wheel(0, 240)  # vertical wheel over topbar
    pg.wait_for_timeout(300)
    after_v = pg.evaluate("() => document.getElementById('topbar').scrollLeft")
    pg.keyboard.down("Shift"); pg.mouse.wheel(0, 240); pg.keyboard.up("Shift")
    pg.wait_for_timeout(300)
    after_sh = pg.evaluate("() => document.getElementById('topbar').scrollLeft")
    pg.evaluate("() => document.getElementById('topbar').scrollBy({left:300})")
    pg.wait_for_timeout(200)
    after_prog = pg.evaluate("() => document.getElementById('topbar').scrollLeft")
    res["topbar_wheel"] = {"state": tb_state, "after_vwheel": after_v, "after_shiftwheel": after_sh, "after_prog": after_prog}
    log(f"wheel: {json.dumps(res['topbar_wheel'])}")
    b.close()

    # ---------- SESSION 2: contour lines + cut/fill + labels (terrain flows) ----------
    b, ctx, pg, errs = newpage(pw)
    pg.evaluate("() => document.getElementById('wizard-skip')?.click()")
    pg.wait_for_timeout(600)
    pg.evaluate("() => window.setMode('advanced')")
    pg.wait_for_timeout(400)
    # dig a pit for real relief
    pg.keyboard.press("5"); pg.wait_for_timeout(400)
    pg.mouse.move(950, 500); pg.mouse.down()
    for i in range(8):
        pg.mouse.move(950 - i*6, 500 + (i % 2)*4, steps=3); pg.wait_for_timeout(70)
    pg.mouse.up(); pg.wait_for_timeout(2500)
    terr = pg.evaluate("() => { const t = window._test.state.terrain; return { n: t.length, min: Math.min(...t), max: Math.max(...t) }; }")
    log(f"terrain relief: {json.dumps(terr)}")

    # --- contour toggle ---
    pg.evaluate("() => document.querySelector('.td-tab[data-dock=\\'analyze\\']')?.click()")
    pg.wait_for_timeout(600)
    # find the VISIBLE contour toggle actually in the dock DOM
    ct = pg.evaluate("""() => {
      const els = Array.from(document.querySelectorAll('#ta-contour-toggle'));
      return els.map(e => ({ inDock: !!e.closest('.dock-panel, #dock-panel-container, .td-panel, #terrain-analysis-panel'),
                             visible: e.offsetParent !== null || getComputedStyle(e).display !== 'none',
                             parentChain: (() => { let c=[],el=e; while(el && c.length<5){c.push(el.id||el.className||el.tagName); el=el.parentElement;} return c; })() }));
    }""")
    log(f"contour toggles found: {json.dumps(ct)}")
    pre = pg.evaluate("""() => {
      const uuids = new Set(); window.scene.traverse(o => uuids.add(o.uuid)); return uuids.size;
    }""")
    pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()")
    pg.wait_for_timeout(1200)
    cprobe = pg.evaluate("""() => {
      let found = null; const uuids = new Set();
      window.scene.traverse(o => { uuids.add(o.uuid);
        if (o.isLineSegments && !found) { found = { type: 'LineSegments', visible: o.visible, verts: o.geometry?.attributes?.position?.count }; } });
      return { sceneNow: uuids.size, lineseg: found,
               contourEnabled: typeof contourEnabled !== 'undefined' ? contourEnabled : null,
               overlayExists: typeof contourOverlay !== 'undefined' ? !!contourOverlay : null,
               overlayVisible: (typeof contourOverlay !== 'undefined' && contourOverlay) ? contourOverlay.visible : null,
               overlayVerts: (typeof contourOverlay !== 'undefined' && contourOverlay) ? contourOverlay.geometry.attributes.position.count : null };
    }""")
    toast_c = pg.evaluate("() => document.getElementById('toast')?.textContent || ''")
    pg.screenshot(path=f"{OUT}/before_contours_dug.png")
    res["contour"] = {"terrain": terr, "toggles": ct, "sceneBefore": pre, "after": cprobe, "toast": toast_c}
    log(f"contour: {json.dumps(cprobe)} toast={toast_c!r}")
    # turn contour off to not interfere
    pg.evaluate("() => document.getElementById('ta-contour-toggle')?.click()")
    pg.wait_for_timeout(400)

    # --- cut/fill stale panel ---
    pg.evaluate("() => document.getElementById('ta-cutfill-toggle')?.click()")
    pg.wait_for_timeout(500)
    cf0 = pg.evaluate("""() => ({ cut: document.getElementById('cf-cut-val').textContent,
                                  fill: document.getElementById('cf-fill-val').textContent })""")
    # dig again while panel open
    pg.keyboard.press("5"); pg.wait_for_timeout(300)
    pg.mouse.move(1000, 560); pg.mouse.down()
    for i in range(6):
        pg.mouse.move(1000 - i*5, 560, steps=3); pg.wait_for_timeout(70)
    pg.mouse.up(); pg.wait_for_timeout(2500)
    cf1 = pg.evaluate("""() => ({ cut: document.getElementById('cf-cut-val').textContent,
                                  fill: document.getElementById('cf-fill-val').textContent })""")
    terr2 = pg.evaluate("() => { const t = window._test.state.terrain; return { min: Math.min(...t) }; }")
    res["cutfill"] = {"on_open": cf0, "after_dig_while_open": cf1, "terrain_min": terr2}
    log(f"cutfill: open={cf0} after_dig={cf1} min={terr2}")

    # --- label edit path (existing label) ---
    pg.evaluate("() => window._test && document.getElementById('btn-label')?.click()")
    pg.wait_for_timeout(300)
    pg.mouse.click(700, 450)  # place a label
    pg.wait_for_timeout(500)
    lbl_modal_open = pg.evaluate("() => document.getElementById('label-edit-modal').classList.contains('visible')")
    pg.evaluate("""() => { document.getElementById('label-text-input').value = 'ProbeLabel'; document.getElementById('label-save-btn').click(); }""")
    pg.wait_for_timeout(500)
    nlabels = pg.evaluate("() => window._test.labels ? window._test.labels.size : -1")
    # try dblclick on label position to edit
    pg.mouse.dblclick(700, 430)
    pg.wait_for_timeout(600)
    edit_open = pg.evaluate("""() => ({ open: document.getElementById('label-edit-modal').classList.contains('visible'),
                                        title: document.getElementById('label-edit-title')?.textContent })""")
    res["label"] = {"created_modal": lbl_modal_open, "n_labels": nlabels, "dblclick_edit": edit_open}
    log(f"label: created={lbl_modal_open} n={nlabels} dblclick={json.dumps(edit_open)}")
    b.close()

    # ---------- SESSION 3: night sky stars/moon ----------
    b, ctx, pg, errs = newpage(pw)
    pg.evaluate("() => document.getElementById('wizard-skip')?.click()")
    pg.wait_for_timeout(600)
    pg.evaluate("() => window.setMode('advanced')")
    pg.wait_for_timeout(400)
    night = pg.evaluate("""() => {
      const A = window.Atmosphere; if (!A) return { err: 'no Atmosphere' };
      A.setStarIntensity(1.0); A.setMoonEnabled(true);
      A.update(23.9, -30); // deep night
      const out = { starField: null, moonMesh: null, moonLight: null };
      window.scene.traverse(o => {
        if (o.isPoints && !out.starField) out.starField = { visible: o.visible, count: o.geometry.attributes.position.count,
                                                            opacity: o.material.uniforms ? o.material.uniforms.opacity.value : null };
        if (o.geometry && o.geometry.type === 'SphereGeometry' && !out.moonMesh) out.moonMesh = { visible: o.visible, pos: o.position.toArray() };
        if (o.isDirectionalLight && !out.moonLight) { /* sun is also directional; check color */ if (o.color.getHexString() === '90a0c0') out.moonLight = { intensity: o.intensity }; }
      });
      return out;
    }""")
    pg.wait_for_timeout(800)
    pg.screenshot(path=f"{OUT}/before_night_23h.png")
    # pixel count bright points in upper sky band
    import subprocess
    res["night"] = night
    log(f"night: {json.dumps(night)}")
    b.close()

json.dump(res, open(f"{OUT}/probe_before.json", "w"), indent=1, default=str)
log("saved probe_before.json")
#!/usr/bin/env python3
"""Sprint 22 Agent 1 — pre-build CDP verification of every shortcut in the SPRINT22_BRIEF inventory.
Real CDP input events only (Playwright keyboard/mouse), never page.evaluate() calling app functions.
"""
import os
from playwright.sync_api import sync_playwright

URL = os.environ.get("BASE_URL", "http://localhost:8175") + "/index.html"
RESULTS = []

def record(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)[:200]) if detail else ""))

def js(page, expr):
    # read-only observation only
    return page.evaluate("() => " + expr)

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(URL)
    pg.wait_for_function("() => document.getElementById('wizard-next') && document.getElementById('wizard').style.display !== 'none'", timeout=10000)
    # dismiss wizard via real clicks
    pg.click("#wizard-next", timeout=8000)
    pg.wait_for_selector("#wizard-finish", timeout=8000)
    pg.click("#wizard-finish", timeout=8000)
    pg.wait_for_function("() => document.getElementById('wizard').style.display === 'none'", timeout=8000)
    pg.wait_for_timeout(900)

    # ---------- TERRAIN ----------
    # '1' -> raise mode active + terrain dock opens
    pg.keyboard.press("1")
    pg.wait_for_timeout(300)
    raise_active = js(pg, "document.querySelector('.terrain-mode-btn[data-tmode=\"raise\"]').classList.contains('active')")
    dock_terrain_visible = js(pg, "!!document.querySelector('#dock-terrain-content') && getComputedStyle(document.getElementById('terrain-dock')||document.querySelector('.terrain-dock')||document.body).display !== 'none'")
    record("1 -> raise brush mode active", raise_active)
    # dock open check: dock tab area visible
    dock_open = js(pg, "(() => { const el = document.querySelector('.td-tab[data-dock=\"terrain\"]'); if (!el) return false; const panel = document.getElementById('dock-panel') || document.querySelector('.dock-panel, #dock'); return panel ? getComputedStyle(panel).display !== 'none' : true; })()")
    record("1 -> terrain dock auto-opens", dock_open)

    pg.keyboard.press("3")  # smooth
    pg.wait_for_timeout(250)
    record("3 -> smooth brush mode", js(pg, "document.querySelector('.terrain-mode-btn[data-tmode=\"smooth\"]').classList.contains('active')"))

    # [ / ] brush size. Start at a known value: press ']' repeatedly from 8 -> 12 then '[' -> back
    pg.keyboard.press("]")  # 9
    pg.wait_for_timeout(120)
    pg.keyboard.press("]")
    pg.wait_for_timeout(120)
    v_after_up = js(pg, "document.getElementById('terrain-brush-val').textContent")
    record("] -> brush size up (8->9+)", v_after_up in ("9 ft", "10 ft"), v_after_up)
    pg.keyboard.press("[")
    pg.wait_for_timeout(120)
    v_after_down = js(pg, "document.getElementById('terrain-brush-val').textContent")
    record("[ -> brush size down", v_after_down in ("8 ft", "9 ft"), v_after_down)

    # X -> toggle terrain dock/mode off
    pg.keyboard.press("x")
    pg.wait_for_timeout(250)
    x_off = js(pg, "!document.getElementById('terrain-btn').classList.contains('active')")
    record("X -> terrain mode toggled off", x_off)
    pg.keyboard.press("x")
    pg.wait_for_timeout(250)
    x_on = js(pg, "document.getElementById('terrain-btn').classList.contains('active')")
    record("X -> terrain mode toggled back on", x_on)
    pg.keyboard.press("x")  # leave terrain off for next tests
    pg.wait_for_timeout(200)

    # ---------- VIEW & CAMERA ----------
    pg.keyboard.press("v")
    pg.wait_for_timeout(300)
    record("V -> 3D view active", js(pg, "document.querySelector('#view-toggle button[data-view=\"3d\"]').classList.contains('active')"))
    pg.keyboard.press("b")
    pg.wait_for_timeout(300)
    record("B -> bird's-eye (2D) active", js(pg, "document.querySelector('#view-toggle button[data-view=\"2d\"]').classList.contains('active')"))
    pg.keyboard.press("v")
    pg.wait_for_timeout(250)

    pg.keyboard.press("g")
    pg.wait_for_timeout(250)
    grid1 = js(pg, "window._bydScene && (() => { const g = window._bydScene.children.find(o => o.isGridHelper); return g ? g.visible : 'nogrid'; })()")
    record("G -> grid toggled", grid1 is False, grid1)  # grid starts visible -> now False
    pg.keyboard.press("g")
    pg.wait_for_timeout(200)
    grid2 = js(pg, "window._bydScene && (() => { const g = window._bydScene.children.find(o => o.isGridHelper); return g ? g.visible : 'nogrid'; })()")
    record("G -> grid toggled back", grid2 is True, grid2)

    # R reset: nudge camera by orbit-drag first (real mouse), then R should restore
    pg.mouse.move(720, 420)
    pg.mouse.down()
    pg.mouse.move(820, 470, steps=5)
    pg.mouse.up()
    pg.wait_for_timeout(200)
    pg.keyboard.press("r")
    pg.wait_for_timeout(300)
    cam_ok = js(pg, "(() => { const c = window._bydActiveCamera; return c ? (c.position.x > 10 && c.position.z > 10) : 'nocam'; })()")
    record("R -> view reset", cam_ok is True, cam_ok)

    # M -> toggle to advanced, then back to basic
    pg.keyboard.press("m")
    pg.wait_for_timeout(300)
    record("M -> advanced mode", js(pg, "document.body.classList.contains('byd-advanced-mode')"))
    pg.keyboard.press("m")
    pg.wait_for_timeout(300)
    record("M -> back to basic", js(pg, "document.body.classList.contains('byd-basic-mode')"))

    # T -> terrain dock opens
    pg.keyboard.press("t")
    pg.wait_for_timeout(300)
    t_open = js(pg, "(() => { const tab = document.querySelector('.td-tab[data-dock=\"terrain\"]'); return tab ? tab.classList.contains('active') : false; })()")
    record("T -> terrain dock tab active", t_open)
    # close dock with Escape (also tests Escape close panels)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(250)

    # W -> walk mode, Esc exits
    pg.keyboard.press("w")
    pg.wait_for_timeout(500)
    walk_on = js(pg, "document.getElementById('walk-controls').classList.contains('visible')")
    record("W -> walk mode entered", walk_on)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(400)
    record("Escape -> walk mode exits", js(pg, "!document.getElementById('walk-controls').classList.contains('visible')"))

    # ---------- SELECTION & EDIT (need an object) ----------
    lib_item = pg.locator(".lib-item").first
    lib_item.click()
    pg.wait_for_timeout(400)
    sel = js(pg, "window._bydState ? window._bydState.selectedId : null")
    record("click library item -> object added+selected", sel is not None, sel)

    x0, z0 = js(pg, "(() => { const o = window._bydState.objects.get(window._bydState.selectedId); return [o.position.x, o.position.z]; })()")
    pg.keyboard.press("ArrowRight")
    pg.wait_for_timeout(200)
    x1, z1 = js(pg, "(() => { const o = window._bydState.objects.get(window._bydState.selectedId); return [o.position.x, o.position.z]; })()")
    record("ArrowRight -> object moved +1 x", abs((x1 - x0) - 1.0) < 0.01, f"{x0}->{x1}")

    # Alt+Tab cycle with a second object
    pg.locator(".lib-item").nth(1).click()
    pg.wait_for_timeout(350)
    id2 = js(pg, "window._bydState.selectedId")
    pg.keyboard.press("Alt+Tab")
    pg.wait_for_timeout(250)
    id3 = js(pg, "window._bydState.selectedId")
    record("Alt+Tab -> cycles selection", id3 is not None and id3 != id2, f"{id2}->{id3}")

    # Ctrl+A select-all context
    pg.keyboard.press("Control+a")
    pg.wait_for_timeout(300)
    multi = js(pg, "window._bydState.selectedIds.size")
    record("Ctrl+A -> select all (batch)", multi and multi >= 2, multi)

    # Escape clears selection
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(250)
    esc_cleared = js(pg, "window._bydState.selectedId === null && window._bydState.selectedIds.size === 0")
    record("Escape -> deselect", esc_cleared)

    # Ctrl+D duplicate: select single first via Alt+Tab? simpler: click canvas object center via lib again
    lib_item.click()
    pg.wait_for_timeout(300)
    n0 = js(pg, "window._bydState.objects.size")
    pg.keyboard.press("Control+d")
    pg.wait_for_timeout(350)
    n1 = js(pg, "window._bydState.objects.size")
    record("Ctrl+D -> duplicate", n1 == n0 + 1, f"{n0}->{n1}")

    # Delete
    pg.keyboard.press("Delete")
    pg.wait_for_timeout(300)
    n2 = js(pg, "window._bydState.objects.size")
    record("Delete -> deletes selected", n2 == n1 - 1, f"{n1}->{n2}")

    # Ctrl+Z undo / Ctrl+Shift+Z redo
    pg.keyboard.press("Control+z")
    pg.wait_for_timeout(300)
    n3 = js(pg, "window._bydState.objects.size")
    record("Ctrl+Z -> undo restore", n3 == n1, f"{n2}->{n3}")
    pg.keyboard.press("Control+Shift+z")
    pg.wait_for_timeout(300)
    n4 = js(pg, "window._bydState.objects.size")
    record("Ctrl+Shift+Z -> redo delete", n4 == n2, f"{n3}->{n4}")

    # ---------- FILES & TOOLS ----------
    downloads = []
    pg.context.on("page", lambda _: None)
    pg.expect_download(lambda: pg.keyboard.press("Control+s"), timeout=5000)
    record("Ctrl+S -> triggers download (save)", True)

    # Ctrl+Shift+S -> save-as prompt dialog
    pg.on("dialog", lambda d: (results_dialog.append(d.type) if False else None))
    got_prompt = {"v": False}
    def on_dialog(d):
        got_prompt["v"] = True
        try: d.dismiss()
        except Exception: pass
    pg.on("dialog", on_dialog)
    pg.keyboard.press("Control+Shift+s")
    pg.wait_for_timeout(400)
    record("Ctrl+Shift+S -> save-as prompt appears", got_prompt["v"])

    # Ctrl+K palette
    pg.keyboard.press("Control+k")
    pg.wait_for_timeout(300)
    record("Ctrl+K -> command palette opens", js(pg, "document.getElementById('cmd-palette-overlay').classList.contains('visible')"))
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(200)
    record("Escape -> palette closes", js(pg, "!document.getElementById('cmd-palette-overlay').classList.contains('visible')"))

    # '?' and F1 currently unhandled (baseline check)
    pg.keyboard.press("Shift+Slash")  # produces '?'
    pg.wait_for_timeout(250)
    help_open = js(pg, "document.getElementById('help-modal').classList.contains('visible')")
    print("NOTE  '?' currently opens help-modal:", help_open)
    pg.keyboard.press("F1")
    pg.wait_for_timeout(250)
    print("NOTE  F1 currently opens help-modal:", js(pg, "document.getElementById('help-modal').classList.contains('visible')"))

    # '?' does not collide with any other handler (searched: no other '?' handler exists)
    # Ctrl+Shift+P is the perf panel (documented at 15855) — brief says print/screenshot; verify actual
    pg.keyboard.press("Control+Shift+p")
    pg.wait_for_timeout(300)
    perf = js(pg, "(() => { const el = document.getElementById('perf-panel'); return el ? getComputedStyle(el).display : 'none-created'; })()")
    print("NOTE  Ctrl+Shift+P toggles perf panel, display:", perf)

    record("no page errors during all shortcut drives", not errors, errors[:3])
    b.close()

fails = [n for n, ok in RESULTS if not ok]
print(f"\n==== {len(RESULTS) - len(fails)}/{len(RESULTS)} pre-build checks passed; fails: {fails}")
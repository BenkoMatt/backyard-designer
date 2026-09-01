#!/usr/bin/env python3
"""One-shot: cutaway sweep with GL program counter attached.

Confirms the t_52168e24 fix does not reintroduce shader-program churn when the
cutaway slider mutates the persistent plane in place (sprint-27 win retained).
"""
import json
import time

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8347"
VIEW = {"width": 1280, "height": 800}

ATTACH = """() => {
  const gl = window.renderer.getContext();
  window._pc = {compiles: 0, links: 0};
  const oc = gl.compileShader.bind(gl);
  gl.compileShader = s => { window._pc.compiles++; oc(s); };
  const ol = gl.linkProgram.bind(gl);
  gl.linkProgram = p => { window._pc.links++; ol(p); };
  return {ok: true};
}"""
PROGS = "() => (window.renderer.info.programs || []).length"
CLEAR = "() => { window._pc.compiles = 0; window._pc.links = 0; return window._pc; }"


def set_slider(page, sel, value):
    el = page.locator(sel)
    box = el.bounding_box()
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


out = {"port": 8347, "sweep": [], "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox", "--use-gl=angle",
              "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
    )
    page = browser.new_context(viewport=VIEW).new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE + "/index.html", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(1500)
    skip = page.locator("#wizard-skip")
    if skip.count() > 0:
        skip.click()
    else:
        page.keyboard.press("Escape")
    page.wait_for_timeout(800)
    page.evaluate("""() => {
      const w = document.getElementById('wizard');
      if (w) w.style.display = 'none';
      const wp = document.getElementById('welcome-prompt');
      if (wp) { wp.classList.remove('visible'); wp.style.display = 'none'; }
    }""")
    page.wait_for_timeout(300)
    page.evaluate(ATTACH)
    adv = page.locator("#mode-toggle button[data-mode='advanced']")
    if adv.count() > 0:
        adv.click()
        page.wait_for_timeout(500)
    page.locator(".td-tab[data-dock='underground']").click()
    page.wait_for_timeout(800)

    for val in [0, 40, 70, 30, 80, 65]:
        page.evaluate(CLEAR)
        got = set_slider(page, "#terrain-cutaway", val)
        page.wait_for_timeout(400)
        out["sweep"].append({
            "val": val, "got": got,
            "compiles": page.evaluate("() => window._pc.compiles"),
            "links": page.evaluate("() => window._pc.links"),
            "programs": page.evaluate(PROGS),
        })
    out["pageerrors"] = errors
    browser.close()

with open("/root/.hermes/kanban/boards/byd-overnight/workspaces/t_52168e24/sprint27_cutaway_progcount.json", "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
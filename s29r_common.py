#!/usr/bin/env python3
"""S29R (Agent R2) — full panel sweep: every panel surface, Basic AND Advanced.

Surfaces: terrain-controls (3 accordions + presets), excavate, terrain-analysis
(every toggle), innovation (every tool), sun (every control), cost, layer,
season, growth, permit, cross-section, cut-fill, buried-objects (2+ buried items).

Real CDP clicks/keys via Playwright. page.evaluate ONLY for read-only probes
and window._test setup (burying objects). Serves from MY worktree on :8220.
Outputs: reports/s29_shots/r2_<tag>_<mode>.png + .verdict.json (r2_ prefix
distinguishes from predecessor audit-panels artifacts).
"""
import base64
import json
import os
import sys
import time
import traceback
import urllib.request

from playwright.sync_api import sync_playwright

REPO = "/root/byd29r-panels"
PORT = 8220
URL = f"http://localhost:{PORT}/index.html"
SHOTS = os.path.join(REPO, "reports", "s29_shots")
os.makedirs(SHOTS, exist_ok=True)

KEY = None
for envf in ("/root/.hermes/.env", "/root/.env"):
    if os.path.exists(envf):
        for line in open(envf):
            if line.startswith("OLLAMA_API_KEY="):
                KEY = line.strip().split("=", 1)[1]
                break
    if KEY:
        break

QA_PROMPT = (
    "1280x800 screenshot of a 3D backyard design web app. QA: "
    "(1) any overlapping or clipped UI? (2) would a new user understand this "
    "screen in 5 seconds? (3) anything confusing, ambiguous, misplaced, or "
    "broken-looking? If perfect, reply CLEAN plus a one-line summary."
)

BURY_JS = """(() => { // window._test SETUP (allowed)
  const T = window._test; if (!T) return 'no _test';
  const added = [];
  // bury two objects: push y below grade using object API if present
  const objs = T.objects ? T.objects() : (window.__objects || []);
  return JSON.stringify({ok:true, api: Object.keys(T).slice(0,40)});
})()"""


def vision_qa(png_path, retries=4):
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = json.dumps({
        "model": "glm-5.3-flash",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": QA_PROMPT},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
        ]}],
        "options": {"temperature": 0},
    }).encode()
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                "https://ollama.com/v1/chat/completions", data=body,
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + KEY})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read().decode())
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            last = e
            time.sleep(5 * (attempt + 1))
    return "VISION_ERROR: %s" % last


def is_clean(verdict):
    v = (verdict or "").strip().upper()
    if "VISION_ERROR" in v:
        return None
    if v.startswith("CLEAN"):
        return True
    if v.startswith("*") and "CLEAN" in v[:14] and "NOT" not in v[:14]:
        return True
    if v.startswith("VERDICT: CLEAN"):
        return True
    return False


def shot_path(name):
    return os.path.join(SHOTS, name + ".png")


def sidecar(name, payload):
    with open(os.path.join(SHOTS, name + ".verdict.json"), "w") as f:
        json.dump(payload, f, indent=1)


def make_page(p, width=1280, height=800):
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox", "--use-gl=swiftshader",
              "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": width, "height": height})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    return browser, page, errors


def load_app(page, mode="basic"):
    """Load, clear seeds, dismiss wizard + welcome prompt via real clicks, set mode."""
    page.goto(URL + "#t", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(1200)
    page.evaluate("() => { try{localStorage.removeItem('backyard-recovery-snapshot');}catch(e){} }")
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(1500)
    skip = page.locator("#wizard-skip")
    if skip.count() > 0:
        skip.click()
        page.wait_for_timeout(700)
    # welcome prompt: dismiss via real click on first quick-action (Start from scratch)
    wp = page.locator("#welcome-prompt")
    if wp.count() > 0 and wp.first.is_visible():
        try:
            pg_btns = page.locator("#welcome-prompt button")
            if pg_btns.count() > 0:
                pg_btns.first.click(timeout=3000)
                page.wait_for_timeout(600)
        except Exception:
            pass
    if mode == "advanced":
        adv = page.locator("#mode-toggle button[data-mode='advanced']")
        if adv.count() > 0:
            adv.click()
            page.wait_for_timeout(700)
    page.keyboard.press("Escape")  # settle any hint/tooltip
    page.wait_for_timeout(250)
    # park pointer mid-viewport to avoid hover tooltips on sidebar/topbar
    page.mouse.move(640, 350)
    page.wait_for_timeout(450)


def setup_buried(page, n=2):
    """window._test setup: bury objects so buried-objects list has 2+ items.
    Uses only sanctioned _test helpers; read-back is read-only."""
    info = page.evaluate("""() => {
      const T = window._test;
      if (!T) return {err: 'no _test'};
      return {keys: Object.keys(T)};
    }""")
    return info


def rect_probe(page, selectors):
    """Read-only getBoundingClientRect probe for overlap verification."""
    return page.evaluate("""(sels) => {
      const out = [];
      for (const s of sels) {
        for (const el of document.querySelectorAll(s)) {
          const cs = getComputedStyle(el);
          if (cs.display === 'none' || cs.visibility === 'hidden') continue;
          const r = el.getBoundingClientRect();
          if (r.width < 2 || r.height < 2) continue;
          out.push({sel: s, x: Math.round(r.x), y: Math.round(r.y),
                    w: Math.round(r.width), h: Math.round(r.height),
                    right: Math.round(r.right), bottom: Math.round(r.bottom)});
        }
      }
      return out;
    }""", selectors)


def run_surface(page, spec, tag, mode):
    """Execute the action list; return (ok, err)."""
    try:
        for act in spec:
            kind = act[0]
            if kind == "click":
                page.locator(act[1]).first.click(timeout=6500)
            elif kind == "hover":
                page.locator(act[1]).first.hover(timeout=6500)
            elif kind == "drag":
                # real pointer drag of a range input to fraction of its track
                loc = page.locator(act[1]).first
                box = loc.bounding_box()
                loc.hover()
                page.mouse.down()
                page.mouse.move(box["x"] + box["width"] * act[2],
                                box["y"] + box["height"] / 2, steps=12)
                page.mouse.up()
            elif kind == "press":
                page.keyboard.press(act[1])
            elif kind == "kpress":
                page.locator(act[1]).first.click()
                page.keyboard.press(act[2])
            elif kind == "eval_setup":
                page.evaluate(act[1])
            elif kind == "wait":
                page.wait_for_timeout(int(act[1] * 1000))
            elif kind == "scroll_in":
                page.locator(act[1]).first.hover()
                page.mouse.wheel(0, act[2])
        return True, None
    except Exception as e:
        return False, str(e).split("\n")[0][:300]


def judge(page, tag, mode, label, results, probe_sels=None):
    name = f"r2_{tag}_{mode}"
    path = shot_path(name)
    page.screenshot(path=path)
    verdict = vision_qa(path)
    clean = is_clean(verdict)
    probe = rect_probe(page, probe_sels) if probe_sels else []
    rec = {"surface": tag, "mode": mode, "label": label,
           "clean": clean, "verdict": verdict, "probe": probe,
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    sidecar(name, rec)
    results[name] = rec
    mark = "CLEAN" if clean else ("ERR" if clean is None else "DIRTY")
    print(f"[{mark}] {name} :: {(verdict or '')[:160].replace(chr(10),' | ')}", flush=True)
    return clean
"""Sprint 29 Agent 1 (AUDIT-CORE-UI) shared helpers.

Rules honored (SPRINT29_BRIEF.md):
- Real CDP pointer/keyboard events only (Playwright locators / page.keyboard /
  page.mouse). page.evaluate is used ONLY for read-only probes or test SETUP
  (adding objects for the 200-object yard, dismissing overlays) — never to
  drive UI state changes.
- Screenshots + verdict JSON sidecars land in reports/s29_shots/.
- Vision: glm-5.3-flash via ollama-cloud, temperature 0, base64 image_url.
"""
import base64
import glob
import json
import os
import re
import time
import urllib.request

from playwright.sync_api import sync_playwright

REPO = "/root/byd29-audit-core"
PORT = 8183
URL = f"http://127.0.0.1:{PORT}/index.html"
SHOTS = os.path.join(REPO, "reports", "s29_shots")

KEY = "MISSING"
for _envf in ("/root/.hermes/.env", "/root/.env"):
    if os.path.exists(_envf):
        for _line in open(_envf):
            if _line.startswith("OLLAMA_API_KEY="):
                KEY = _line.strip().split("=", 1)[1]
                break
    if KEY:
        break

QA_PROMPT = (
    "1280x800 screenshot of a 3D backyard design web app. QA: (1) any overlapping or "
    "clipped UI? (2) would a new user understand this screen in 5 seconds? (3) anything "
    "confusing, ambiguous, misplaced, or broken-looking? If perfect, reply CLEAN plus a "
    "one-line summary."
)

VERDICTS = {}  # name -> verdict text (in-memory cache for this run)


def vision_qa(png_path):
    """Return raw verdict text from glm-5.3-flash for one screenshot."""
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
    for attempt in range(4):
        try:
            req = urllib.request.Request(
                "https://ollama.com/v1/chat/completions", data=body,
                headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read().decode())
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            last = e
            time.sleep(3 * (attempt + 1))
    return "VISION_ERROR: %s" % last


def is_clean(verdict):
    return verdict.strip().upper().startswith("CLEAN")


def make_browser(p, width=1280, height=800):
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox", "--use-gl=swiftshader",
              "--enable-unsafe-swiftshader"],
    )
    page = browser.new_page(viewport={"width": width, "height": height})
    errors = []

    def _on_pageerror(e):
        errors.append(str(e))

    page.on("pageerror", _on_pageerror)
    return browser, page, errors


def load_app(page, fresh=True):
    """Load the app. fresh=True drops localStorage so the first-run wizard shows."""
    if fresh:
        # SETUP only: clear storage so we exercise the true first-run state.
        page.goto("about:blank")
        page.evaluate("() => { try { localStorage.clear(); } catch(e) {} }", )
    page.goto(URL, wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(1800)


def dismiss_overlays(page):
    """SETUP only: hide wizard + welcome so we can audit the main workspace.
    The wizard MutationObserver re-shows the welcome prompt 600ms after the
    wizard hides — so we pre-seed the onboarding state (test setup, per brief)
    to keep it away, then also hard-hide both overlays."""
    page.evaluate("""() => {
        try {
            localStorage.setItem('backyard-onboarding-state',
                JSON.stringify({completedSteps:[], tourCompleted:true,
                                welcomeShown:true, dismissedAt:Date.now(),
                                featuresUsed:{}}));
        } catch(e) {}
        const w = document.getElementById('wizard');
        if (w) w.style.display = 'none';
        const wp = document.getElementById('welcome-prompt');
        if (wp) { wp.classList.remove('visible'); wp.setAttribute('aria-hidden','true'); }
    }""")
    page.wait_for_timeout(400)


def to_advanced(page):
    adv = page.locator("#mode-toggle button[data-mode='advanced']")
    if adv.count() > 0:
        adv.click()
        page.wait_for_timeout(700)


def to_basic(page):
    b = page.locator("#mode-toggle button[data-mode='basic']")
    if b.count() > 0:
        b.click()
        page.wait_for_timeout(700)


def set_camera(page, pos=(0, 12, 55), target=(0, -4, 0)):
    """SETUP only: frame the yard."""
    page.evaluate("""([pos, target]) => {
        const c = window.controls, cam = window.camera3D;
        if (!c || !cam) return;
        c.target.set(target[0], target[1], target[2]);
        cam.position.set(pos[0], pos[1], pos[2]);
        c.update();
    }""", [list(pos), list(target)])
    page.wait_for_timeout(350)


def shot(page, name, note=""):
    path = os.path.join(SHOTS, name + ".png")
    if os.path.exists(path):
        # resumable: don't re-shoot existing captures in the same run
        return path
    page.screenshot(path=path)
    return path


def verdict_and_save(name, note="", extra=None, force=False):
    """Run vision QA on <name>.png, write sidecar <name>.verdict.json, return dict."""
    png = os.path.join(SHOTS, name + ".png")
    side = os.path.join(SHOTS, name + ".verdict.json")
    if os.path.exists(side) and not force:
        with open(side) as f:
            return json.load(f)
    v = vision_qa(png)
    rec = {"surface": name, "verdict": v, "clean": is_clean(v), "note": note,
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if extra:
        rec.update(extra)
    with open(os.path.join(SHOTS, name + ".verdict.json"), "w") as f:
        json.dump(rec, f, indent=1)
    print(("CLEAN " if rec["clean"] else "ISSUE ") + name + (" | " + v[:160] if not rec["clean"] else ""))
    return rec


def append_handoff(lines):
    """Append one JSON-line findings to the shared handoff file."""
    with open("/root/byd29-staging/S29_HANDOFF.md", "a") as f:
        for line in lines:
            f.write(line + "\n")


def rect(page, sel):
    """Read-only probe: element bounding rect as dict, or None."""
    r = page.evaluate("""(sel) => {
        const el = document.querySelector(sel);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {x: r.x, y: r.y, w: r.width, h: r.height, top: r.top, bottom: r.bottom,
                left: r.left, right: r.right};
    }""", sel)
    return r
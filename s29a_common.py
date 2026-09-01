"""Sprint 29 Agent 4 (AUDIT-TRANSIENTS) shared CDP helpers.

Rules honored (SPRINT29_BRIEF hard rule 2): all click/keyboard paths go through
REAL CDP events (Playwright locators / page.keyboard / page.mouse). page.evaluate
is used ONLY for read-only probes and test SETUP (seeding localStorage, window._test
state, hiding the first-run wizard) — never to drive UI actions.

Server: port 8180+ only (rule 3). This agent owns 8191; torn down at the end.
"""
import json
import os
import socket
import subprocess
import time

from playwright.sync_api import sync_playwright

REPO = "/root/byd29-audit-transients"
PORT = 8191
URL = f"http://localhost:{PORT}/index.html"
SHOTS = os.path.join(REPO, "reports", "s29_shots")
os.makedirs(SHOTS, exist_ok=True)

_server = None


def start_server():
    global _server
    if _server:
        return
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("127.0.0.1", PORT))  # already running?
        return
    # (ConnectionRefused falls through to spawn)
    _spawn()


def _spawn():
    global _server
    _server = subprocess.Popen(
        ["python3", "-m", "http.server", str(PORT)],
        cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                s.connect(("127.0.0.1", PORT))
                return
        except OSError:
            time.sleep(0.2)


def stop_server():
    global _server
    if _server:
        _server.terminate()
        _server = None


def make_page(p, width=1280, height=800):
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox", "--use-gl=swiftshader",
              "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": width, "height": height})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append("console-error: " + m.text) if m.type == "error" else None)
    return browser, page, errors


def load_app(page, wizard="hide", goto=None):
    page.goto(goto or URL, wait_until="networkidle", timeout=45000)
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
    adv = page.locator("#mode-toggle button[data-mode='advanced']")
    if adv.count() > 0:
        adv.click()
        page.wait_for_timeout(500)


def shot(page, name):
    path = os.path.join(SHOTS, name + ".png")
    page.screenshot(path=path)
    return path


def sidecar(name, obj):
    path = os.path.join(SHOTS, name + ".verdict.json")
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)
    return path


RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": str(detail)[:400]})
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)[:300]) if detail else ""))
    return bool(ok)


def save_results(path):
    with open(path, "w") as f:
        json.dump(RESULTS, f, indent=1)
    n_pass = sum(1 for r in RESULTS if r["ok"])
    print(f"\n== {n_pass}/{len(RESULTS)} passed ==")
    return n_pass == len(RESULTS)


def rect(page, sel):
    """Read-only geometry probe."""
    return page.evaluate("""(sel) => {
        const el = typeof sel === 'string' ? document.querySelector(sel) : sel;
        if (!el) return null;
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return {left: Math.round(r.left), top: Math.round(r.top), right: Math.round(r.right),
                bottom: Math.round(r.bottom), w: Math.round(r.width), h: Math.round(r.height),
                display: cs.display, visible: cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0};
    }""", sel)


def intersect(a, b):
    if not a or not b:
        return False
    return not (a["right"] <= b["left"] or a["left"] >= b["right"]
                or a["bottom"] <= b["top"] or a["top"] >= b["bottom"])


def rects_intersect(page, sel_a, sel_b):
    return intersect(rect(page, sel_a), rect(page, sel_b))


def toolbar_buttons(page):
    """Read-only probe of every bottom-left toolbar button rect."""
    return page.evaluate("""() => {
        const tb = document.getElementById('bottom-left-toolbar');
        if (!tb) return {exists: false, buttons: []};
        const btns = Array.from(tb.querySelectorAll('button')).map(b => {
            const r = b.getBoundingClientRect();
            return {id: b.id, left: Math.round(r.left), top: Math.round(r.top),
                    right: Math.round(r.right), bottom: Math.round(r.bottom),
                    visible: r.width > 0 && r.height > 0};
        });
        return {exists: true, buttons: btns};
    }""")
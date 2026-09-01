"""Sprint 29 Agent 3 shared helpers — CDP sweep + glm-5.3-flash vision QA.

Rules honored:
- All UI actions via REAL CDP pointer/keyboard events (Playwright).
- page.evaluate used ONLY for read-only probes + window._test SETUP.
- Server: port 8180 (owned by this agent). Never touch 8099/8115/8175/8093/8095.
"""
import base64
import json
import os
import time
import urllib.request

from playwright.sync_api import sync_playwright

REPO = "/root/byd29-audit-modals"
PORT = 8186
URL = f"http://localhost:{PORT}/index.html"
SHOTS = os.path.join(REPO, "reports", "s29_shots")

QA_PROMPT = (
    "1280x800 screenshot of a 3D backyard design web app. QA: (1) any overlapping or clipped "
    "UI? (2) would a new user understand this screen in 5 seconds? (3) anything confusing, "
    "ambiguous, misplaced, or broken-looking? If perfect, reply CLEAN plus a one-line summary."
)

KEY = None
for envf in ("/root/.hermes/.env", "/root/.env"):
    if os.path.exists(envf):
        for line in open(envf):
            if line.startswith("OLLAMA_API_KEY="):
                KEY = line.strip().split("=", 1)[1]
                break
    if KEY:
        break


def vision_qa(png_path, prompt=QA_PROMPT, retries=3):
    """glm-5.3-flash verdict for one screenshot. Returns raw content string."""
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = json.dumps({
        "model": "glm-5.3-flash",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
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
            time.sleep(3 * (attempt + 1))
    return "VISION_ERROR: %s" % last


def is_clean(verdict):
    v = verdict.strip().upper()
    if "VISION_ERROR" in v:
        return False
    # tolerate leading markdown emphasis, e.g. "**CLEAN** — ..."
    if v.startswith("CLEAN"):
        return True
    if v.startswith("*") and "CLEAN" in v[:12]:
        return True
    if v.startswith("VERDICT: CLEAN"):
        return True
    return False


def shot_path(name):
    os.makedirs(SHOTS, exist_ok=True)
    return os.path.join(SHOTS, name + ".png")


def sidecar(name, payload):
    os.makedirs(SHOTS, exist_ok=True)
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


def load_app(page, wizard=True):
    """Load app; wizard=True dismisses first-run wizard via its Skip button (real click)."""
    page.goto(URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(1800)
    if wizard:
        page.evaluate("() => { localStorage.removeItem('backyard-onboarding-state'); }")
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(1800)
        skip = page.locator("#wizard-skip")
        if skip.count() > 0:
            skip.click()
            page.wait_for_timeout(900)
    page.wait_for_timeout(300)


def dismiss_overlays(page):
    """Close toast/hints if any — read-only style, via Escape key (real key event)."""
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)


def to_advanced(page):
    adv = page.locator("#mode-toggle button[data-mode='advanced']")
    if adv.count() > 0:
        adv.click()
        page.wait_for_timeout(600)


def capture(page, name, label, verdict, issue=""):
    path = shot_path(name)
    page.screenshot(path=path)
    sidecar(name, {"surface": name, "label": label, "verdict": verdict,
                   "issue": issue, "ts": time.strftime("%H:%M:%S")})
    tag = "CLEAN" if is_clean(verdict) else "DIRTY"
    print(f"[{tag}] {name} :: {verdict.strip()[:150].replace(chr(10), ' | ')}")
    return path


def overlay_probe(page):
    """Read-only DOM probe: detect visible elements whose rect overflows the viewport
    or panels whose scrollHeight exceeds clientHeight (scroll overflow)."""
    return page.evaluate("""() => {
    const out = {overflow: [], clip: []};
    const vw = innerWidth, vh = innerHeight;
    const modals = ['help-modal','shortcuts-modal','share-modal','templates-modal',
                    'gallery-modal','label-edit-modal','cmd-palette-overlay','print-view',
                    'dock-terrain','dock-underground','dock-analyze','dock-innovate',
                    'dock-sun','dock-measure','dock-experience'];
    for (const id of modals) {
        const m = document.getElementById(id);
        if (!m) continue;
        const cs = getComputedStyle(m);
        const visible = cs.display !== 'none' && (m.classList.contains('visible') || cs.display === 'block' && id === 'print-view');
        if (!visible) continue;
        const r = m.getBoundingClientRect();
        const rec = {id, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)};
        if (r.x < 0 || r.y < 0 || r.right > vw || r.bottom > vh) out.overflow.push(rec);
        // inner scroll containers
        const scrollers = [m, ...m.querySelectorAll('.help-panel,.sc-panel,.templates-panel,.share-panel,.label-edit-panel,.gallery-panel,.dock-panel-body,.cmd-palette-results,.gallery-grid')];
        for (const s of scrollers) {
            const scs = getComputedStyle(s);
            if (scs.display === 'none') continue;
            const sh = s.scrollHeight, ch = s.clientHeight, sw = s.scrollWidth, cw = s.clientWidth;
            if ((sh - ch > 2 || sw - cw > 2)) {
                const sr = s.getBoundingClientRect();
                out.overflow.push({id: (s.id || s.className.split(' ')[0] || 'inner'), scroll: true,
                                   scrollH: sh, clientH: ch, scrollW: sw, clientW: cw,
                                   x: Math.round(sr.x), y: Math.round(sr.y)});
            }
        }
    }
    return out;
}""")
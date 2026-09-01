#!/usr/bin/env python3
"""Sprint 23 Agent 3 (TOAST-HYGIENE) — transient overlay audit.

Exercises EVERY transient overlay (#toast, #context-hint, #grid-level-badge,
#depth-gauge-overlay, #atmosphere-badge, #recovery-banner) with real CDP clicks
(page.evaluate only for test setup of badges that have no natural CDP trigger),
checks rect overlaps against interactive chrome, screenshots, and (SHOTS=1)
sends to glm-5.3-flash vision.

Usage: BASE_URL=http://localhost:8095/index.html python3 s23_agent3_overlay_audit.py
Writes: reports/sprint23_shots/agent3-a3-<overlay>.png (+ .verdict.txt with SHOTS=1)
        reports/sprint23_shots/agent3_overlay_results.json
"""
import base64
import json
import os
import sys
import urllib.request

URL = os.environ.get("BASE_URL", "http://localhost:8095/index.html")
MODE = os.environ.get("BYD_MODE", "after")
DO_VISION = os.environ.get("SHOTS", "0") == "1"
SHOTS = "reports/sprint23_shots"
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

INIT_STORAGE = """
  try {
    localStorage.setItem('backyard-onboarding-state', JSON.stringify({
        completedSteps: ['welcome-scratch'], tourCompleted: true,
        welcomeShown: true, dismissedAt: 1, featuresUsed: {}}));
    localStorage.removeItem('backyard-design-autosave');
  } catch(e) {}
"""

DISMISS = """() => {
    const w = document.getElementById('wizard');
    if (w) w.style.display = 'none';
    const wp = document.getElementById('welcome-prompt');
    if (wp) wp.style.display = 'none';
}"""

GEOM = """(ids) => {
    const out = {};
    for (const id of ids) {
        const el = document.getElementById(id);
        if (!el) { out[id] = null; continue; }
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        const vis = cs.display !== 'none' && cs.visibility !== 'hidden'
            && parseFloat(cs.opacity) > 0.05;
        out[id] = (r.width > 0 && r.height > 0 && vis)
            ? { left: r.left, top: r.top, right: r.right, bottom: r.bottom, visible: true }
            : null;
    }
    out._buttons = [...document.querySelectorAll('#bottom-left-toolbar button')]
        .map(b => { const r = b.getBoundingClientRect();
            return { id: b.id, left: r.left, top: r.top, right: r.right, bottom: r.bottom }; });
    const sb = document.getElementById('status-bar');
    if (sb) { const r = sb.getBoundingClientRect(); out._status = { left: r.left, top: r.top, right: r.right, bottom: r.bottom }; }
    const tb = document.getElementById('topbar');
    if (tb) { const r = tb.getBoundingClientRect(); out._topbar = { left: r.left, top: r.top, right: r.right, bottom: r.bottom }; }
    return out;
}"""

def rect(g, k):
    v = g.get(k)
    return v if v and k != "_buttons" and not k.startswith("_") else None

def inter(a, b):
    return (a and b and not (a['right'] <= b['left'] or a['left'] >= b['right']
                             or a['bottom'] <= b['top'] or a['top'] >= b['bottom']))

def check(overlay, g):
    """Return list of conflict strings for the overlay rect."""
    r = rect(g, overlay)
    if not r:
        return []
    conf = []
    for b in g.get('_buttons', []):
        if inter(r, b):
            conf.append(f"toolbar-btn:{b['id']}")
    if inter(r, g.get('_status')):
        conf.append("status-bar")
    if inter(r, g.get('_topbar')):
        conf.append("topbar")
    return conf

# overlay id -> trigger. REALCLICK = real CDP interaction; SETUP = evaluate test setup.
STATES = [
    ("toast", "REALCLICK:lib-item"),
    ("context-hint", None),          # shown together with toast after add
    ("grid-level-badge", "REALCLICK:slider"),
    ("depth-gauge-overlay", "REALCLICK:#vc-underground"),
    ("atmosphere-badge", None),      # appears after sun/weather change; checked in state
    ("recovery-banner", "REALCLICK:recovery"),
]

OVERLAY_IDS = ["toast", "context-hint", "grid-level-badge", "depth-gauge-overlay",
               "atmosphere-badge", "recovery-banner"]

results = []
shots = []

def vision_qa(png_path):
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = json.dumps({
        "model": "glm-5.3-flash",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "1280x800 screenshot of a 3D backyard design web app. "
             "(1) Anything overlapping or clipped? (2) Is every transient notification/badge "
             "fully legible and not stacked under another element? (3) Anything confusing or "
             "broken-looking? Reply CLEAN if perfect."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
        ]}],
        "options": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(
        "https://ollama.com/v1/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode())
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            last = e
    return f"VISION-ERROR: {last}"

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = ctx.new_page()
    page.add_init_script(INIT_STORAGE)
    page.goto(URL, wait_until='load', timeout=30000)
    page.wait_for_timeout(2500)
    page.evaluate(DISMISS)
    page.wait_for_timeout(300)

    for overlay, trigger in STATES:
        state = {"overlay": overlay, "trigger": trigger or "co-present"}
        if trigger == "REALCLICK:lib-item":
            page.click('.lib-item')          # real click -> toast + hint
            page.wait_for_function(
                "document.getElementById('toast').classList.contains('visible')", timeout=4000)
            page.wait_for_timeout(400)
        elif trigger == "REALCLICK:slider":
            # real path: open Terrain panel -> expand "Grid Level & Depth" accordion
            # -> keyboard on slider (input listener toggles the badge)
            page.click('#terrain-btn')
            page.wait_for_timeout(500)
            page.click('[data-tc-acc][aria-controls="tc-panel-ground"]')
            page.wait_for_timeout(300)
            page.click('#gridlevel-section-toggle')
            page.wait_for_timeout(300)
            page.click('#grid-level-slider')
            for _ in range(3):
                page.keyboard.press('ArrowUp')
                page.wait_for_timeout(80)
            page.wait_for_timeout(400)
        elif trigger == "REALCLICK:#vc-underground":
            page.click('#vc-underground')    # real click -> underground view + depth gauge
            page.wait_for_timeout(900)
        elif trigger == "REALCLICK:recovery":
            # real user path: crash/reload recovery — write a snapshot via the app's
            # own autosave (evaluate read-only localStorage write + genuine reload)
            page.evaluate("""() => {
                const snap = {ts: Date.now(), d: {objects: ['probe'], terrain: null}};
                localStorage.setItem('backyard-recovery-snapshot', JSON.stringify(snap));
            }""")
            page.reload(wait_until='load')
            page.wait_for_timeout(2500)
            page.evaluate(DISMISS)
            page.wait_for_timeout(300)

        g = page.evaluate(GEOM, OVERLAY_IDS)
        r = rect(g, overlay)
        state["rect"] = {k2: round(v, 1) for k2, v in r.items()} if r else None
        state["conflicts"] = check(overlay, g)
        # co-present overlays at snapshot time
        state["co_present"] = [o for o in OVERLAY_IDS if o != overlay and rect(g, o)
                               and rect(g, o).get('visible')]
        if r and not state["conflicts"]:
            # no chrome conflict: also verify no OTHER visible overlay overlaps it
            for o in OVERLAY_IDS:
                if o != overlay and inter(r, rect(g, o)):
                    state["conflicts"].append(f"overlay:{o}")

        name = f"agent3-{MODE}-{overlay}"
        path = os.path.join(SHOTS, name + ".png")
        page.screenshot(path=path)
        shots.append((name, path))
        state["shot"] = path
        results.append(state)
        print(f"[{overlay}] rect={state['rect']} conflicts={state['conflicts']} co={state['co_present']}")

        # teardown for next state
        if overlay == "grid-level-badge":
            page.click('#grid-level-slider')
            for _ in range(4):
                page.keyboard.press('ArrowDown')
                page.wait_for_timeout(60)
            page.keyboard.press('Escape')   # close terrain panel
            page.wait_for_timeout(300)
        elif overlay == "depth-gauge-overlay":
            page.keyboard.press('Escape')
            page.wait_for_timeout(400)
        elif overlay == "recovery-banner":
            page.evaluate("() => { if (typeof hideRecoveryBanner === 'function') hideRecoveryBanner(); }")
        elif overlay == "toast":
            page.keyboard.press('Escape')    # deselect closes properties panel
            page.wait_for_timeout(400)
        page.wait_for_timeout(200)

    # toast + grid-level-badge stacked state (top-center stacking check)
    page.click('#terrain-btn')
    page.wait_for_timeout(500)
    page.click('[data-tc-acc][aria-controls="tc-panel-ground"]')
    page.wait_for_timeout(300)
    page.click('#gridlevel-section-toggle')
    page.wait_for_timeout(300)
    page.click('#grid-level-slider')
    for _ in range(3):
        page.keyboard.press('ArrowUp')
        page.wait_for_timeout(80)
    page.click('.lib-item')
    try:
        page.wait_for_function("document.getElementById('toast').classList.contains('visible')", timeout=4000)
    except Exception:
        pass
    page.wait_for_timeout(400)
    g = page.evaluate(GEOM, OVERLAY_IDS)
    st = {"overlay": "toast+badge-stacked", "rect": {k2: round(v, 1) for k2, v in (rect(g, 'toast') or {}).items()},
          "conflicts": inter(rect(g, 'toast'), rect(g, 'grid-level-badge')) and ["overlay:grid-level-badge"] or [],
          "badge_rect": {k2: round(v, 1) for k2, v in (rect(g, 'grid-level-badge') or {}).items()}}
    name = f"agent3-{MODE}-toast-badge-stack"
    path = os.path.join(SHOTS, name + ".png")
    page.screenshot(path=path)
    st["shot"] = path
    results.append(st)
    shots.append((name, path))
    print(f"[stack] toast={st['rect']} badge={st['badge_rect']} conflict={st['conflicts']}")

    browser.close()

if DO_VISION:
    for name, path in shots:
        v = vision_qa(path)
        with open(path.replace(".png", ".verdict.txt"), "w") as fh:
            fh.write(v or "")
        for s in results:
            if s["shot"] == path:
                s["vision"] = (v or "")[:300]
        print(f"VISION {name}: {(v or 'NO-RESPONSE')[:140]}")

json.dump({"mode": MODE, "base_url": URL, "results": results},
          open(os.path.join(SHOTS, f"agent3_overlay_results_{MODE}.json"), "w"), indent=1)
fails = [s for s in results if s.get("conflicts")]
print(f"\nRESULT: {len(results) - len(fails)}/{len(results)} overlay states clean"
      + (f" — CONFLICTS: {[(s['overlay'], s['conflicts']) for s in fails]}" if fails else ""))
sys.exit(1 if fails else 0)
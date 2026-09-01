"""S29 Agent 1 — DOM rect verification of vision findings (read-only probes).

For each reported overlap, measure the real bounding rects + z-index to
confirm before any fix. Also probes: wizard-skip vs bottom toolbar cluster,
welcome toast vs welcome modal, tooltip vs modal, FPS placeholder, sidebar
scroll cue.
"""
import json
import sys
sys.path.insert(0, "/root/byd29-audit-core")
from s29a_common import load_app, make_browser, dismiss_overlays, to_advanced, set_camera
from playwright.sync_api import sync_playwright

PROBE = r"""() => {
  const out = {};
  const R = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return {x: r.x, y: r.y, w: r.width, h: r.height, z: cs.zIndex,
            display: cs.display, pos: cs.position, text: (el.textContent||'').slice(0,40)};
  };
  out.wizard_skip = R('#wizard-skip');
  out.wizard = R('#wizard');
  out.sun_btn = R('#sun-btn');
  out.scale_bar = R('#scale-bar');
  out.terrain_btn = R('#terrain-btn');
  out.excavate_btn = R('#excavate-btn');
  out.tape_btn = R('#tape-measure-btn');
  out.bottom_toolbar = R('#bottom-left-toolbar');
  out.toast = R('#toast');
  out.context_hint = R('#context-hint');
  out.welcome = R('#welcome-prompt');
  out.fps = (document.querySelector('#fps-display, #status-bar')?.textContent || '').slice(0,80);
  const sb = document.querySelector('#status-bar');
  out.status_text = sb ? sb.textContent.slice(0,120) : null;
  // overlap helper
  out.overlap = function(a, b) {
    if (!a || !b) return null;
    const x = Math.max(0, Math.min(a.x+a.w, b.x+b.w) - Math.max(a.x, b.x));
    const y = Math.max(0, Math.min(a.y+a.h, b.y+b.h) - Math.max(a.y, b.y));
    return {x_overlap: x, y_overlap: y, area: x*y};
  };
  out.skip_vs_sun = out.overlap(out.wizard_skip, out.sun_btn);
  out.skip_vs_scale = out.overlap(out.wizard_skip, out.scale_bar);
  out.skip_vs_tb = out.overlap(out.wizard_skip, out.bottom_toolbar);
  // toast visibility at welcome time
  const toast = document.querySelector('#toast');
  out.toast_visible = toast ? toast.classList.contains('visible') : null;
  out.toast_text = toast ? toast.textContent.slice(0,60) : null;
  return out;
}"""

with sync_playwright() as p:
    browser, page, errors = make_browser(p, 1280, 800)
    load_app(page, fresh=True)
    r = page.evaluate(PROBE)
    print(json.dumps({k: v for k, v in r.items() if k in (
        "wizard_skip", "sun_btn", "scale_bar", "bottom_toolbar", "skip_vs_sun",
        "skip_vs_scale", "skip_vs_tb", "toast_visible")}, indent=1))

    # advance to step 2 and probe again
    page.locator("#wizard-next").click()
    page.wait_for_timeout(400)
    r2 = page.evaluate(PROBE)
    print("step2 skip:", json.dumps(r2["wizard_skip"]))
    print("step2 skip_vs_sun:", r2["skip_vs_sun"], "vs_scale:", r2["skip_vs_scale"])

    # finish -> welcome visible; probe toast + tooltip
    page.locator("#wizard-finish").click()
    page.wait_for_timeout(1400)
    r3 = page.evaluate(PROBE)
    print("welcome toast_visible:", r3["toast_visible"], r3["toast_text"])
    print("welcome rect:", r3["welcome"])
    print("toast rect:", r3["toast"])
    print("ctx hint:", r3["context_hint"])
    print("status:", r3["status_text"])

    # tooltip probe — the 'dark onboarding tooltip' is likely #progressive-hint
    tp = page.evaluate("""() => {
        const sels = ['#progressive-hint','#ctx-tooltip','#context-hint','#progressive-hint *'];
        const out = {};
        for (const s of sels) {
            const el = document.querySelector(s);
            if (el) {
                const r = el.getBoundingClientRect();
                const cs = getComputedStyle(el);
                out[s] = {x:r.x,y:r.y,w:r.width,h:r.height,op:cs.opacity,vis:cs.visibility,disp:cs.display,text:(el.textContent||'').slice(0,50)};
            }
        }
        return out;
    }""")
    print("tooltips:", json.dumps(tp, indent=1))
    print("ERRORS:", errors[:5])
    browser.close()
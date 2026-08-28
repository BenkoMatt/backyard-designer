#!/usr/bin/env python3
"""Probe launcher toolbar geometry: chip rects, parent chain, container width."""
import sys
sys.path.insert(0, '/root/backyard-designer')
from sprint25_pw import launch

p, browser, ctx, page = launch(1280, 800)
try:
    page.keyboard.press('Escape')
    page.wait_for_timeout(400)
    data = page.evaluate("""() => {
      const tb = document.querySelector('#bottom-left-toolbar');
      const out = {chips: [], chain: []};
      if (!tb) return out;
      const cs = getComputedStyle(tb);
      out.tb = {w: tb.offsetWidth, h: tb.offsetHeight, left: cs.left, bottom: cs.bottom,
                maxw: cs.maxWidth, rect: tb.getBoundingClientRect().width};
      let el = tb.parentElement;
      while (el && el !== document.documentElement) {
        const r = el.getBoundingClientRect();
        const c = getComputedStyle(el);
        if (c.position !== 'static' || el.id)
          out.chain.push({tag: el.tagName, id: el.id || null, cls: String(el.className).slice(0,40),
                          pos: c.position, w: Math.round(r.width), x: Math.round(r.left),
                          overflow: c.overflow});
        el = el.parentElement;
      }
      tb.querySelectorAll(':scope > button, :scope > [id]').forEach(b => {
        const r = b.getBoundingClientRect();
        out.chips.push({id: b.id || b.textContent.trim().slice(0,12),
                        x: Math.round(r.left), y: Math.round(r.top),
                        w: Math.round(r.width), h: Math.round(r.height)});
      });
      const hint = document.querySelector('#context-hint');
      if (hint) { const r = hint.getBoundingClientRect(); const c = getComputedStyle(hint);
                  out.hint = {x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width),
                              h: Math.round(r.height), bottom: c.bottom}; }
      const sb = document.querySelector('#status-bar');
      if (sb) { const r = sb.getBoundingClientRect(); out.statusbar = {top: Math.round(r.top), h: Math.round(r.height)}; }
      return out;
    }""")
    import json
    print(json.dumps(data, indent=1))
finally:
    browser.close()
    p.stop()
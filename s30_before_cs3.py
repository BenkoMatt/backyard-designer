#!/usr/bin/env python3
import json, sys
sys.path.insert(0, "/root/byd30-fix")
from s30_probe_common import page_ctx, dismiss_overlays
pw, browser, ctx, page = page_ctx(mode="advanced")
dismiss_overlays(page)
page.click('.td-tab[data-dock="underground"]')
page.wait_for_timeout(700)
page.evaluate("() => { const b = document.getElementById('cross-section-toggle'); if (b) b.click(); }")
page.wait_for_timeout(700)
res = page.evaluate("""() => {
  const cvs = document.getElementById('cross-section-canvas');
  const cs = getComputedStyle(cvs);
  return { position: cs.position, margin: cs.margin, width: cs.width, height: cs.height,
    transform: cs.transform, top: cs.top, left: cs.left, attrW: cvs.getAttribute('width'),
    panelW: document.getElementById('cross-section-panel').offsetWidth,
    stack: cvs.closest('#right-panel-stack') ? 'in-stack' : 'not-in-stack' };
}""")
print(json.dumps(res, indent=1))
pw.stop()


import json, sys
sys.path.insert(0, "/root/byd30-fix")
from s30_probe_common import page_ctx, dismiss_overlays, shot
OUT = "/root/byd30-fix/reports/s30/fixes/"
pw, browser, ctx, page = page_ctx()
dismiss_overlays(page)
res = page.evaluate("""() => {
  const tb = document.getElementById('topbar');
  const cs = getComputedStyle(tb, '::after');
  const csb = getComputedStyle(tb, '::before');
  return { cls: tb.className, afterW: cs.width, afterBg: cs.backgroundImage.slice(0,60),
    chev: csb.content, sw: tb.scrollWidth, cw: tb.clientWidth };
}""")
print(json.dumps(res, indent=1))
json.dump(res, open(OUT + "after_topbar_cue.json", "w"), indent=1)
shot(page, "after_topbar_cue")
pw.stop()

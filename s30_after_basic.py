
import json, sys
sys.path.insert(0, "/root/byd30-fix")
from s30_probe_common import page_ctx, dismiss_overlays, shot
OUT = "/root/byd30-fix/reports/s30/fixes/"
pw, browser, ctx, page = page_ctx()  # basic default
dismiss_overlays(page)
res = page.evaluate("""() => {
  const tab = document.querySelector('.td-tab[data-dock="underground"]');
  const cs = getComputedStyle(tab);
  const r = tab.getBoundingClientRect();
  return { display: cs.display, rect: [r.x, r.y, r.width, r.height], label: tab.querySelector('.td-label').textContent };
}""")
# click it for real and see dock open
page.click('.td-tab[data-dock="underground"]')
page.wait_for_timeout(700)
res["after_click"] = page.evaluate("""() => {
  const dock = document.getElementById('dock-underground');
  return { visible: dock.classList.contains('visible') };
}""")
print(json.dumps(res, indent=1))
json.dump(res, open(OUT + "after_basic_underground.json", "w"), indent=1)
shot(page, "after_basic_underground")
pw.stop()

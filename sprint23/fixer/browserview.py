"""Load app in browser; dump document.scripts metadata + error location as the BROWSER sees it.
Also try parsing line 5587 col 2: print chars 1..40 of that line raw (repr) to spot invisible chars."""
from playwright.sync_api import sync_playwright
import re

html = open('/root/backyard-designer/index.html').read()
lines = html.split('\n')
l = lines[5586]  # 0-indexed for line 5587
print('line 5587 repr first 60:', repr(l[:60]))
print('line 5586 repr last 60:', repr(lines[5585][-60:]))
print('line 5588 repr first 60:', repr(lines[5587][:60]))

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.add_init_script("""
window.__errs = [];
window.addEventListener('error', function(e){
  window.__errs.push({msg: e.message, line: e.lineno, col: e.colno});
}, true);
""")
    page.goto("http://localhost:8304/index.html", timeout=30000)
    page.wait_for_timeout(2000)
    errs = page.evaluate("() => window.__errs")
    scripts = page.evaluate("() => Array.from(document.scripts).map(s => ({src: s.src || '(inline)', type: s.type, lines: s.textContent.split('\\n').length}))")
    print('browser errors:', errs)
    for s in scripts if (scripts := None) else []:
        pass
    print('browser sees scripts:')
    for s in scripts_result if (scripts_result := None) else []:
        pass
    print(scripts)
    browser.close()
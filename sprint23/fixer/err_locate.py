"""Get exact error location via window error event + check for embedded </script> in strings."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.add_init_script("""
window.__errs = [];
window.addEventListener('error', function(e){
  window.__errs.push({msg: e.message, file: e.filename, line: e.lineno, col: e.colno, stack: (e.error && e.error.stack || '').slice(0, 500)});
}, true);
""")
    page.goto("http://localhost:8304/index.html", timeout=30000)
    page.wait_for_timeout(2500)
    errs = page.evaluate("() => window.__errs")
    print("errors:", len(errs))
    for e in errs[:6]:
        print(e)
    browser.close()

html = open('/root/backyard-designer/index.html').read()
count = html.count('</script>')
print('literal </script> occurrences:', count)
import re
# find any that are NOT closing a real script tag: look for </script> inside block 2's body region
blocks = re.findall(r'<script([^>]*)>(.*?)</script>', html, re.S)
total_span_end = 0
for i, (attrs, body) in enumerate(blocks):
    if '</script' in body:
        print(f'block {i} body contains embedded </script>!')
# If real count of blocks*2 + 0 == count, no embedded closers
print('expected closers if clean:', len(blocks), '-> mismatch indicates embedded closers or unclosed tags')
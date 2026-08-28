"""Bisect with the pageerror event (data-URL dynamic import parse errors do not reject
the promise on some stacks). Use a <script type=module> injection per probe + pageerror."""
import base64
from playwright.sync_api import sync_playwright

body = open('/tmp/s23d.js').read()
lines = body.split('\n')
N = len(lines)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    page.goto('about:blank')

    def parses(text):
        errs.clear()
        b64 = base64.b64encode(text.encode()).decode()
        page.evaluate(f"""async () => {{
          const s = document.createElement('script');
          s.type = 'module';
          s.textContent = atob('{b64}');
          document.body.appendChild(s);
          await new Promise(r => setTimeout(r, 150));
          s.remove();
        }}""")
        page.wait_for_timeout(100)
        return errs[0] if errs else 'ok'

    print('whole:', str(parses(body))[:100])
    lo, hi = 1, N
    while lo < hi:
        mid = (lo + hi) // 2
        r = parses('\n'.join(lines[:mid]))
        if r == 'ok':
            lo = mid + 1
        else:
            hi = mid
    print('smallest failing prefix (lines):', lo, '/', N)
    print('line', lo - 1, repr(lines[lo - 2][:150]))
    print('line', lo, repr(lines[lo - 1][:150]))
    print('line', lo + 1, repr(lines[lo][:150]))
    browser.close()
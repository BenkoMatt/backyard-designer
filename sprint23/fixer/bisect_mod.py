"""Bisect block2 with chromium: find the largest line-prefix that parses as a module.
Loads data-URL modules (no server needed)."""
import base64
from playwright.sync_api import sync_playwright

body = open('/tmp/s23d.js').read()
lines = body.split('\n')
N = len(lines)
print('total lines:', N)

def parses(page, text):
    b64 = base64.b64encode(text.encode()).decode()
    url = f'data:text/javascript;base64,{b64}'
    try:
        return page.evaluate(f"() => import('{url}').then(() => 'ok').catch(e => 'runtime:' + e.message)")
    except Exception as e:
        return 'evalfail:' + str(e)[:200]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('about:blank')
    # First: whole body
    whole = parses(page, body)
    print('whole body parse:', whole)
    if whole == 'ok' or whole.startswith('runtime:'):
        print('parses fine as module?! aborting bisect')
    else:
        lo, hi = 1, N  # find smallest failing prefix length
        # quick check: prefix(3962) i.e. through line '});'
        for probe in (3963, 3000, 2000, 1000):
            txt = '\n'.join(lines[:probe])
            r = parses(page, txt)
            print(f'prefix {probe}: {str(r)[:120]}')
        # binary search smallest failing prefix in [1, 3963]
        lo, hi = 1, 3963
        while lo < hi:
            mid = (lo + hi) // 2
            r = parses(page, '\n'.join(lines[:mid]))
            if r == 'ok' or r.startswith('runtime:'):
                lo = mid + 1
            else:
                hi = mid
        print('smallest failing prefix (lines):', lo)
        print('line', lo, 'repr:', repr(lines[lo - 1][:120]) if lo - 1 < len(lines) else 'EOF')
        print('line', lo - 1, 'repr:', repr(lines[lo - 2][:120]))
        print('line', lo - 2, 'repr:', repr(lines[lo - 3][:120]))
    browser.close()
"""Verify module parses in-browser now + boot succeeds."""
import re, subprocess, urllib.request
from playwright.sync_api import sync_playwright

# node module parse via acorn
html = open('/root/backyard-designer/index.html').read()
m = re.search(r'<script type="module">', html)
start = m.end()
end = html.find('</script>', start)
open('/tmp/s23f.js', 'w').write(html[start:end])
r = subprocess.run(['node', '-e', '''
const acorn = require("/tmp/node_modules/acorn");
const fs = require("fs");
try {
  acorn.parse(fs.readFileSync("/tmp/s23f.js","utf8"), {ecmaVersion:2022, sourceType:"module"});
  console.log("acorn module parse: OK");
} catch (e) {
  console.log("acorn FAIL:", e.message, JSON.stringify(e.loc));
}
'''], capture_output=True, text=True, cwd='/tmp')
print(r.stdout.strip(), r.stderr[:200])

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto("http://localhost:8304/index.html", timeout=30000)
    page.wait_for_timeout(3000)
    boot = page.evaluate("() => ({hasState: !!window._bydState, yardReady: window._bydState ? window._bydState.yardReady : null, mode: window.getCurrentMode ? window.getCurrentMode() : null})")
    print('page errors:', errs[:3])
    print('boot:', boot)
    browser.close()
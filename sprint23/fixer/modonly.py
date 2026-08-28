"""Serve block2 body alone as /tmpmod.mjs on port 8307, load it as <script type=module>
in chromium, and read the precise parse error + line."""
import subprocess, time, threading, http.server, functools, os
from playwright.sync_api import sync_playwright

body = open('/tmp/s23d.js').read()
os.makedirs('/tmp/modsrv', exist_ok=True)
open('/tmp/modsrv/mod.mjs', 'w').write(body)

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory='/tmp/modsrv')
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8307), handler)
t = threading.Thread(target=srv.serve_forever, daemon=True)
t.start()

html = '<html><body><script type="module" src="http://127.0.0.1:8307/mod.mjs"></script></body></html>'
open('/tmp/modsrv/host.html', 'w').write(html)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto("http://127.0.0.1:8307/host.html", timeout=30000)
    page.wait_for_timeout(2000)
    print('errors:', len(errs))
    for e in errs[:5]:
        print(e[:600])
    browser.close()
srv.shutdown()
"""Fetch the served module body and node --check it — rules out disk-vs-served skew."""
import urllib.request, subprocess

req = urllib.request.Request('http://127.0.0.1:8304/index.html', headers={'Connection': 'close'})
html = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'replace')
disk = open('/root/backyard-designer/index.html').read()
print('served == disk:', html == disk, '| served bytes:', len(html))

m = re_module = None
import re
m = re.search(r'<script type="module">', html)
start = m.end()
end = html.find('</script>', start)
body = html[start:end]
open('/tmp/s23e.js', 'w').write(body)
r = subprocess.run(['node', '--check', '/tmp/s23e.js'], capture_output=True, text=True)
print('served block2 node --check rc:', r.returncode, r.stderr[:300])
print('served block2 line 3963:', body.split('\n')[3962][:120])
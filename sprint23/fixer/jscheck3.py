"""Extract inline JS blocks exactly like the browser does (no type filtering),
write each to /tmp, node --check each. The importmap has type=importmap so the
browser treats it as JSON - we check it separately with json.loads."""
import re, subprocess, json

html = open('/root/backyard-designer/index.html').read()
# Capture WITH attributes so we can filter by type
blocks = re.findall(r'<script([^>]*)>(.*?)</script>', html, re.S)
print(f'{len(blocks)} script blocks')
for i, (attrs, body) in enumerate(blocks):
    if 'src=' in attrs:
        print(f'block {i}: external src, skip')
        continue
    t = re.search(r'type="([^"]*)"', attrs)
    ttype = t.group(1) if t else '(classic/module)'
    if ttype == 'importmap':
        try:
            json.loads(body)
            print(f'block {i}: importmap JSON OK')
        except Exception as e:
            print(f'block {i}: importmap JSON FAIL: {e}')
        continue
    p = f'/tmp/s23c_{i}.js'
    open(p, 'w').write(body)
    r = subprocess.run(['node', '--check', p], capture_output=True, text=True)
    if r.returncode == 0:
        print(f'block {i} ({ttype}, {len(body)}b): OK')
    else:
        print(f'block {i} ({ttype}, {len(body)}b): FAIL')
        err = r.stderr
        # pull line number
        m = re.search(r's23c_' + str(i) + r'\.js:(\d+)', err)
        print(err[:800])
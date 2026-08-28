"""Precise JS syntax check: skip importmap JSON block; verify real script blocks only."""
import re, subprocess, os

path = '/root/backyard-designer/index.html'
html = open(path).read()

# All script blocks with their attrs
for m in re.finditer(r'<script([^>]*)>', html):
    attrs = m.group(1)
    if 'src=' in attrs:
        print("external:", attrs.strip()[:60])
    elif 'type=' in attrs:
        print("typed block:", attrs.strip()[:60])

# Check only untyped (classic JS) blocks
blocks = re.findall(r'<script>(.*?)(?:</script>)', html, re.S)
print(f"untyped blocks: {len(blocks)}")
fails = 0
for i, b in enumerate(blocks):
    if not b.strip():
        continue
    p = f'/tmp/s23fix_js_{i}.js'
    open(p, 'w').write(b)
    r = subprocess.run(['node', '--check', p], capture_output=True, text=True)
    status = 'OK' if r.returncode == 0 else 'FAIL'
    if r.returncode != 0:
        fails += 1
        print(f"BLOCK {i} {status}:")
        print(r.stderr[:800])
    else:
        print(f"BLOCK {i} {status} ({len(b)} chars)")
print("RESULT:", "ALL OK" if fails == 0 else f"{fails} FAILED")

# Where is #properties relative to #main close?
p_main = html.find('<div id="main">')
p_props = html.find('<div id="properties"')
p_close = html.find('</div>', html.find('id="sun-panel"'))
print(f"main@{p_main} props@{p_props} (props after main open: {p_props > p_main})")
"""Syntax-check the real JS blocks (skip importmap) + locate #properties + V02 marker."""
import re, subprocess
html = open('/root/backyard-designer/index.html').read()
blocks = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S)
for i, b in enumerate(blocks):
    if i == 0:
        continue  # importmap JSON
    p = f'/tmp/s23b_{i}.js'
    open(p, 'w').write(b)
    r = subprocess.run(['node', '--check', p], capture_output=True, text=True)
    print(f"block {i}: {'OK' if r.returncode == 0 else 'FAIL ' + r.stderr[:400]}")

# properties location
m = re.search(r'<div id="properties"[^>]*>', html)
print('properties tag:', m.group(0) if m else 'NOT FOUND')
idx = html.find(m.group(0)) if m else -1
# what's the parent? look backwards 400 chars
print('context before:', html[max(0,idx-400):idx][-300:] if idx >= 0 else '')
print('V02 marker count:', html.count('S23-V02'))
print('props-related fix markers:', [mm for mm in re.findall(r'S23-V\d\d', html)])
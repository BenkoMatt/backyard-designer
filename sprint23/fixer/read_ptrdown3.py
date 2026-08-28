"""Read onPointerDown 3D branch robustly (find function start, then print N lines)."""
import re
html = open('/root/backyard-designer/index.html').read()
i = html.find('function onPointerDown(')
assert i > 0
chunk = html[i:i + 6000]
lines = chunk.split('\n')
for n, ln in enumerate(lines[30:95], start=31):
    print(n, ln)
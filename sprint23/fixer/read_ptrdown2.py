"""Read the 3D branch of onPointerDown + find what consumes pointerdown."""
import re
html = open('/root/backyard-designer/index.html').read()
m = re.search(r'function onPointerDown\(e\) \{(.*?)\n\}', html, re.S)
body = m.group(1)
lines = body.split('\n')
# print lines 30-75 (after the 2D branch)
print("=== onPointerDown lines 30-80 ===")
for ln in lines[30:80]:
    print(ln)
"""V01: instrument onPointerDown raycast by shadowing the code path.

Read index.html's onPointerDown to see which element it's bound to and what gates it.
"""
import re
html = open('/root/backyard-designer/index.html').read()
# find onPointerDown definition
m = re.search(r'function onPointerDown\([^)]*\) \{(.*?)\n\}', html, re.S)
if m:
    body = m.group(1)
    print("=== onPointerDown first 60 lines ===")
    for ln in body.split('\n')[:60]:
        print(ln)
else:
    print("not found via regex; searching addEventListener")
    for mm in re.finditer(r"viewport\.addEventListener\('pointer\w+'", html):
        print(mm.group(0), "at", html[:mm.start()].count('\n') + 1)
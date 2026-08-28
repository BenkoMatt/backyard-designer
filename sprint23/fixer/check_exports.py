"""Check window export names + V13/V14 probe (why count=1?), V07 redo detail."""
import re
html = open('/root/backyard-designer/index.html').read()
for name in ['selectObjectMulti', 'selectObject', 'addObject', 'loadDesign', 'sanitizeObjectParams']:
    exp = f"window.{name} ="
    found = [m.start() for m in re.finditer(re.escape(exp), html)]
    print(f"window.{name}: {len(found)} exports at", [html[:f].count(chr(10)) + 1 for f in found])
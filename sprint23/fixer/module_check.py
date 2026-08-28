"""Check the type=module script block with node --input-type=module."""
import re, subprocess

html = open('/root/backyard-designer/index.html').read()
m = re.search(r'<script type="module">(.*?)</script>', html, re.S)
assert m, "module block not found"
code = m.group(1)
print("module block chars:", len(code))
p = '/tmp/s23fix_module.mjs'
open(p, 'w').write(code)
r = subprocess.run(['node', '--check', '--input-type=module', p], capture_output=True, text=True)
print("syntax:", "OK" if r.returncode == 0 else "FAIL")
if r.returncode != 0:
    print(r.stderr[:1000])
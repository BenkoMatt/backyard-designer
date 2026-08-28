#!/usr/bin/env python3
"""Diff the showProperties function between HEAD and current, line-aligned."""
import subprocess, difflib

orig = subprocess.run(['git', 'show', 'HEAD:index.html'], capture_output=True, text=True).stdout
cur = open('/root/backyard-designer/index.html').read()
o = orig.split('\n')
c = cur.split('\n')

def grab(lines, count=110):
    for i, l in enumerate(lines):
        if 'function showProperties' in l:
            return lines[i - 1:i - 1 + count], i
    return [], -1

ob, oi = grab(o)
cb, ci = grab(c)
print('orig showProperties at line', oi, '| current at', ci)
diff = list(difflib.unified_diff(ob, cb, lineterm='', n=3))
for d in diff:
    print(d[:140])
#!/usr/bin/env python3
"""Check runtime var() consumers (getComputedStyle reads) for tokens I plan to delete."""
import re
src = open('index.html', encoding='utf-8').read()
hits = re.findall(r"getPropertyValue\(\s*['\"]([^'\"]+)['\"]", src)
print("getPropertyValue reads:", hits)
# also CSS.supports or inline style="...var(--x)" in HTML body
inline = re.findall(r'style="[^"]*"', src)
import collections
c = collections.Counter()
for s in inline:
    for v in re.findall(r'var\((--[a-z0-9-]+)\)', s):
        c[v] += 1
print("inline-style var() uses:", dict(c))
# JS string-built styles containing var(
js = re.findall(r'\.style\.[a-zA-Z]+\s*=\s*[^;]*var\(--[a-z0-9-]+\)', src)
print("JS style assignments with var():", len(js))
for j in js[:10]:
    print("  ", j[:100])
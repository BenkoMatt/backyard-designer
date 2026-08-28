#!/usr/bin/env python3
"""Sprint 25 visual drift audit: find off-token colors/radii/shadows/typography in index.html CSS."""
import re, sys, collections

src = open('index.html', encoding='utf-8').read()
m = re.search(r'<style>(.*?)</style>', src, re.S)
css = m.group(1)
print(f"CSS block: {len(css)} chars, lines {src[:m.start()].count(chr(10))+1}-{src[:m.end()].count(chr(10))+1}")

# brace balance
opens, closes = css.count('{'), css.count('}')
print(f"BRACE BALANCE: {opens} open / {closes} close -> {'BALANCED' if opens==closes else 'UNBALANCED!!!'}")

# rules: split into selectors{body}
rules = re.findall(r'([^{}]+)\{([^{}]*)\}', css)
print(f"rules parsed: {len(rules)}")

# Count hex colors used directly (not inside a var definition)
hex_uses = collections.Counter()
rgba_uses = collections.Counter()
radius_vals = collections.Counter()
font_sizes = collections.Counter()
shadows = collections.Counter()
for sel, body in rules:
    sel = sel.strip()[:60]
    for hx in re.findall(r'#[0-9a-fA-F]{3,8}\b', body):
        hex_uses[hx.lower()] += 1
    for rg in re.findall(r'rgba?\([^)]+\)', body):
        rgba_uses[rg] += 1
    for r in re.findall(r'border-radius:([^;]+)', body):
        radius_vals[r.strip()] += 1
    for f in re.findall(r'font-size:([^;]+)', body):
        font_sizes[f.strip()] += 1
    for s in re.findall(r'box-shadow:([^;]+)', body):
        shadows[s.strip()] += 1

print("\n== TOP raw hex colors (non-var) ==")
for hx, n in hex_uses.most_common(25):
    print(f"  {n:4d}  {hx}")
print("\n== TOP rgba() colors ==")
for rg, n in rgba_uses.most_common(20):
    print(f"  {n:4d}  {rg}")
print("\n== border-radius values ==")
for r, n in radius_vals.most_common(25):
    print(f"  {n:4d}  {r}")
print("\n== font-size values ==")
for f, n in font_sizes.most_common(25):
    print(f"  {n:4d}  {f}")
print("\n== box-shadow values ==")
for s, n in shadows.most_common(20):
    print(f"  {n:4d}  {s[:80]}")

# focus-visible coverage
fv = len(re.findall(r':focus-visible', css))
focus = len(re.findall(r':focus(?![-:])', css))
print(f"\n:focus-visible rules: {fv}, :focus rules: {focus}")

# cursor rules
cursors = re.findall(r'cursor:([^;]+)', css)
print(f"\ncursor decls: {collections.Counter(c.strip() for c in cursors).most_common(15)}")
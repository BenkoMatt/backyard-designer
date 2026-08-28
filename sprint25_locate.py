#!/usr/bin/env python3
"""Sprint 25: locate off-token drift sites precisely."""
import re

src = open('index.html', encoding='utf-8').read()
css = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
rules = re.findall(r'([^{}]+)\{([^{}]*)\}', css)

def show(title, pred):
    print(f"\n== {title} ==")
    for sel, body in rules:
        hits = [d.strip() for d in body.split(';') if d.strip() and pred(d.strip())]
        if hits:
            s = ' '.join(sel.strip().split())[:90]
            for h in hits:
                print(f"  {s}  ||  {h[:110]}")

show("stray blue #1565c0/#e3f2fd", lambda d: '1565c0' in d or 'e3f2fd' in d)
show("radius 3px", lambda d: re.search(r'border-radius:\s*3px', d))
show("radius 2px", lambda d: re.search(r'border-radius:\s*2px', d))
show("radius 8px/10px", lambda d: re.search(r'border-radius:\s*(8|10)px', d))
show("radius 16/20/24px", lambda d: re.search(r'border-radius:\s*(16|20|24)px', d))
show("radius 6px raw", lambda d: re.search(r'border-radius:\s*6px', d))
show("radius 4px raw", lambda d: re.search(r'border-radius:\s*4px', d))
show("one-off shadows", lambda d: re.search(r'box-shadow:(?!var|none)', d))
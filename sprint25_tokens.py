#!/usr/bin/env python3
"""Audit every :root token: definition present + var() usage count. List dead tokens."""
import re

src = open('index.html', encoding='utf-8').read()
css = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
root = re.search(r':root\{([^}]*)\}', css).group(1)
tokens = [t.split(':')[0].strip() for t in root.split(';') if ':' in t]
dead = []
for t in tokens:
    uses = len(re.findall(r'var\(' + re.escape(t) + r'\)', src))
    if uses == 0:
        dead.append(t)
    print(f"{t}: {uses} uses")
print("\nDEAD TOKENS:", dead)
# byte size of removing each dead token decl (incl trailing ;)
for t in dead:
    m = re.search(re.escape(t) + r':[^;]+;', root)
    if m:
        print(f"  -{t}: {len(m.group(0))} bytes")
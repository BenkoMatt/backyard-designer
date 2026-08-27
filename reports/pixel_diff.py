#!/usr/bin/env python3
"""Pixel-diff before/after sprint22 screenshots per surface."""
import os
from PIL import Image, ImageChops

BEFORE = "/root/byd22-visual-consistency/reports/sprint22_shots/before"
AFTER = "/root/byd22-visual-consistency/reports/sprint22_shots/after"

rows = []
for name in sorted(os.listdir(BEFORE)):
    if not name.endswith(".png"):
        continue
    b_path, a_path = os.path.join(BEFORE, name), os.path.join(AFTER, name)
    if not os.path.exists(a_path):
        rows.append((name, "MISSING AFTER"))
        continue
    b, a = Image.open(b_path).convert("RGB"), Image.open(a_path).convert("RGB")
    if b.size != a.size:
        rows.append((name, f"size differs {b.size} vs {a.size}"))
        continue
    diff = ImageChops.difference(b, a)
    bbox = diff.getbbox()
    hist = diff.convert("L").histogram()
    total = sum(hist)
    changed = sum(hist[12:])  # pixels with meaningful delta
    pct = 100.0 * changed / total
    rows.append((name, f"{pct:5.2f}% pixels changed, diff-bbox={bbox}"))

print(f"{'surface':40s} delta")
for name, info in rows:
    print(f"{name:40s} {info}")
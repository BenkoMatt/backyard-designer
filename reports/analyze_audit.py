#!/usr/bin/env python3
"""Summarize computed-style drift from sprint22 audit.json."""
import json
import sys
from collections import Counter, defaultdict

mode = sys.argv[1] if len(sys.argv) > 1 else "before"
path = f"/root/byd22-visual-consistency/reports/sprint22_shots/{mode}/audit.json"
with open(path) as f:
    data = json.load(f)

heights = Counter()
radii = Counter()
fonts = Counter()
trans = Counter()
pads = Counter()
per_surface = {}

for surf, entry in sorted(data.items()):
    a = entry.get("audit") if isinstance(entry, dict) else None
    if not a or "buttons" not in (a or {}):
        continue
    s = {"buttons": [], "inputs": [], "headers": [], "gaps": a.get("gaps", [])}
    for b in a["buttons"]:
        heights[b["h"]] += 1
        radii[b["radius"]] += 1
        fonts[b["font"]] += 1
        trans[b["transition"]] += 1
        pads[b["pad"]] += 1
        s["buttons"].append((b["cls"], b["h"], b["radius"], b["font"], b["transition"]))
    for i in a.get("inputs", []):
        s["inputs"].append((i["cls"], i["h"], i["radius"], i["font"], i["pad"]))
    for hd in a.get("headers", []):
        s["headers"].append((hd["cls"], hd["font"], hd["color"]))
    per_surface[surf] = s

print("== BUTTON HEIGHTS ==")
for h, c in sorted(heights.items()):
    print(f"  {h}px x{c}")
print("== BUTTON RADII ==")
for r, c in radii.most_common():
    print(f"  {r!r} x{c}")
print("== BUTTON FONTS (size/weight/family) ==")
for ft, c in fonts.most_common():
    print(f"  {ft} x{c}")
print("== BUTTON TRANSITIONS ==")
for t, c in trans.most_common():
    print(f"  {t} x{c}")
print("== BUTTON PADDINGS ==")
for p, c in pads.most_common(15):
    print(f"  {p!r} x{c}")

print("\n== PER-SURFACE HEADERS ==")
for surf, s in per_surface.items():
    if s["headers"]:
        print(f" {surf}:")
        for hd in s["headers"][:6]:
            print(f"    {hd}")

print("\n== INPUT STYLES (drift candidates) ==")
ins = Counter()
for surf, s in per_surface.items():
    for i in s["inputs"]:
        ins[(i[2], i[4])] += 1
for k, c in ins.most_common(20):
    print(f"  radius={k[0]!r} pad={k[1]!r} x{c}")

print("\n== FLEX GAPS in use ==")
gaps = Counter()
for surf, s in per_surface.items():
    for g in s["gaps"]:
        gaps[g["gap"]] += 1
for g, c in gaps.most_common(15):
    print(f"  {g} x{c}")
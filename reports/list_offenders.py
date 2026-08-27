#!/usr/bin/env python3
"""List specific offender controls from audit.json."""
import json
import sys
from collections import defaultdict

mode = sys.argv[1] if len(sys.argv) > 1 else "before"
path = f"/root/byd22-visual-consistency/reports/sprint22_shots/{mode}/audit.json"
with open(path) as f:
    data = json.load(f)

no_trans = defaultdict(set)
arial = defaultdict(set)
odd_font = defaultdict(set)
radii_odd = defaultdict(set)

for surf, entry in sorted(data.items()):
    a = entry.get("audit") if isinstance(entry, dict) else None
    if not a or "buttons" not in (a or {}):
        continue
    for b in a["buttons"]:
        cls = b["cls"] or "(none)"
        if b["transition"] == "none":
            no_trans[cls].add(surf.split("-", 1)[-1])
        if "Arial" in b["font"]:
            arial[f"{cls} :: {b['font']}"].add(surf.split("-", 1)[-1])
        if b["radius"] in ("10px", "0px") and b["h"] >= 20 and "td-tab" not in cls and "chip" not in cls:
            radii_odd[f"{cls} r={b['radius']}"].add(surf.split("-", 1)[-1])

print("== BUTTON CLASSES MISSING TRANSITION ==")
for cls, surfs in sorted(no_trans.items()):
    print(f"  {cls}  -> {sorted(surfs)[:4]}")
print("\n== ARIAL (missing font-family:inherit) ==")
for cls, surfs in sorted(arial.items()):
    print(f"  {cls}  -> {sorted(surfs)[:4]}")
print("\n== ODD RADII on normal buttons ==")
for cls, surfs in sorted(radii_odd.items()):
    print(f"  {cls}  -> {sorted(surfs)[:4]}")
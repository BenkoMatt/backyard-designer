#!/usr/bin/env python3
"""Inspect unclassed buttons w/o transitions in after-audit."""
import json

path = "/root/byd22-visual-consistency/reports/sprint22_shots/after/audit.json"
with open(path) as f:
    data = json.load(f)
for surf, entry in sorted(data.items()):
    a = entry.get("audit") if isinstance(entry, dict) else None
    if not a or "buttons" not in (a or {}):
        continue
    for b in a["buttons"]:
        if b["transition"] == "none" and not b["cls"]:
            print(f"{surf}: id={b['id']} h={b['h']} font={b['font']} pad={b['pad']!r} bg={b['bg']} text-ish")
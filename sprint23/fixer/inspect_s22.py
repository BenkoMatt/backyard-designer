"""Inspect s22 gate test code for the 3 failing tests to understand what they check."""
import re
src = open('/root/backyard-designer/sprint22_quality_gate.py').read()
for name in ("Command palette closes with Escape", "Key 'Delete': selected object deleted", "opens the shortcuts guide"):
    idx = src.find(name)
    if idx == -1:
        print('NOT FOUND:', name)
        continue
    start = src.rfind('\n', 0, idx - 400)
    print('=' * 70)
    print(src[max(0, idx - 700):idx + 400])
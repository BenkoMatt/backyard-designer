#!/usr/bin/env python3
"""Diff the global Escape branch: HEAD vs current, lines around 'Escape' in the keydown handler."""
import subprocess, difflib

orig = subprocess.run(['git', 'show', 'HEAD:index.html'], capture_output=True, text=True).stdout

def region(src, tag):
    lines = src.split('\n')
    start = end = None
    for i, l in enumerate(lines, 1):
        if "} else if (e.key === 'Escape') {" in l and start is None and i > 5000:
            start = i
        if start and 'deselectObject(); clearMultiSelect(); hideContextMenu(); }' in l:
            end = i
            break
    print(f'===== {tag}: lines {start}-{end} =====')
    for i in range(start, end + 1):
        print(i, lines[i - 1][:120])

region(orig, 'ORIGINAL')
print()
region(open('/root/backyard-designer/index.html').read(), 'CURRENT')
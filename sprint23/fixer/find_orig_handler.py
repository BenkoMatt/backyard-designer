#!/usr/bin/env python3
"""Find the MAIN global keydown handler in ORIGINAL (the one with INPUT guard + Ctrl branches).
Search for 'INPUT' in a document.addEventListener('keydown' context."""
import subprocess

orig_src = subprocess.run(['git', 'show', 'HEAD:index.html'], capture_output=True, text=True).stdout
lines = orig_src.split('\n')
for i, l in enumerate(lines, 1):
    if "document.addEventListener('keydown'" in l:
        # check next 30 lines for INPUT guard
        window = '\n'.join(lines[i - 1:i + 29])
        if 'INPUT' in window or 'e.ctrlKey' in window:
            print('candidate handler at line', i, ':', l[:90])
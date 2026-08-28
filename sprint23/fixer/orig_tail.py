#!/usr/bin/env python3
"""Print ORIGINAL lines 5455-5475 (after the main Escape branch, where the handler closes)."""
import subprocess
orig_src = subprocess.run(['git', 'show', 'HEAD:index.html'], capture_output=True, text=True).stdout
lines = orig_src.split('\n')
for i in range(5452, 5478):
    print(i, lines[i - 1][:110])
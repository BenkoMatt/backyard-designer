#!/usr/bin/env python3
"""Print ORIGINAL lines 5478-5500 - the handler close + what follows."""
import subprocess
orig_src = subprocess.run(['git', 'show', 'HEAD:index.html'], capture_output=True, text=True).stdout
lines = orig_src.split('\n')
for i in range(5478, 5505):
    print(i, lines[i - 1][:110])
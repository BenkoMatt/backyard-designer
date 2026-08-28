#!/usr/bin/env python3
"""Show the original showProperties tail (git HEAD) vs current tail."""
import subprocess
orig = subprocess.run(['git', 'show', 'HEAD:index.html'], capture_output=True, text=True).stdout
olines = orig.split('\n')
# find the btn-duplicate listener in original
for i, l in enumerate(olines, 1):
    if 'btn-duplicate' in l and 'addEventListener' in l:
        print('orig line', i)
        for j in range(i - 2, i + 14):
            print(j, olines[j - 1][:110])
        break
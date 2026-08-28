#!/usr/bin/env python3
"""Show original (HEAD) lines around the keydown handler near 3836 region: the block the
fixer deleted. Original line 3945 'checkSafetyWarnings(obj);' closes showProperties.
Search original for 'checkSafetyWarnings(obj);' occurrences and their context."""
import subprocess
orig = subprocess.run(['git', 'show', 'HEAD:index.html'], capture_output=True, text=True).stdout
olines = orig.split('\n')
for i, l in enumerate(olines, 1):
    if l.strip() == 'checkSafetyWarnings(obj);':
        print('--- orig around line', i)
        for j in range(max(1, i - 18), i + 3):
            print(j, olines[j - 1][:120])
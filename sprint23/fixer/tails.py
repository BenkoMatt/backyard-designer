#!/usr/bin/env python3
"""Grab showProperties tail: from 'btn-duplicate' to 'function hideProperties' in both versions."""
import subprocess

orig = subprocess.run(['git', 'show', 'HEAD:index.html'], capture_output=True, text=True).stdout
cur = open('/root/backyard-designer/index.html').read()

def tail(src, tag):
    lines = src.split('\n')
    out = []
    grabbing = False
    for i, l in enumerate(lines, 1):
        if 'btn-duplicate' in l and 'addEventListener' in l:
            grabbing = True
        if grabbing:
            out.append(f'{i}\t{l[:110]}')
            if 'function hideProperties' in l:
                break
    print(f'===== {tag} =====')
    print('\n'.join(out))

tail(orig, 'ORIGINAL')
tail(cur, 'CURRENT')
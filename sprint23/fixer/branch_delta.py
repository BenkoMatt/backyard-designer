#!/usr/bin/env python3
"""Compare Escape branch brace depth between ORIGINAL and CURRENT to find the missing '}'.
ORIGINAL: lines 5409-5455. Track balance from 5409 (opening at bal+1 within handler).
Print the last 6 lines of the Escape branch in each version with their running balance
relative to the START of the Escape-branch line."""
import subprocess

orig_src = subprocess.run(['git', 'show', 'HEAD:index.html'], capture_output=True, text=True).stdout
cur = open('/root/backyard-designer/index.html').read()

def tok(l):
    out = []; i = 0; n = len(l)
    while i < n:
        ch = l[i]
        if ch == '/' and i + 1 < n and l[i+1] == '/':
            while i < n and l[i] != '\n': i += 1
        elif ch == '/' and i + 1 < n and l[i+1] == '*':
            i += 2
            while i + 1 < n and not (l[i] == '*' and l[i+1] == '/'): i += 1
            i += 2
        elif ch == '`':
            i += 1
            while i < n and l[i] != '`':
                if l[i] == '\\': i += 1
                i += 1
            i += 1
        elif ch in ('"', "'"):
            q = ch; i += 1
            while i < n and l[i] != q:
                if l[i] == '\\': i += 1
                i += 1
            i += 1
        else:
            out.append(ch); i += 1
    return ''.join(out)

def bal_from(lines, start, end):
    bal = 0
    out = {}
    for ln in range(start, end + 1):
        bal += tok(lines[ln - 1]).count('{') - tok(lines[ln - 1]).count('}')
        out[ln] = bal
    return out

# ORIGINAL Escape branch: 5409..5455 (ends before 'Tab' at 5456)
ob = bal_from(orig_src.split('\n'), 5409, 5455)
# CURRENT: 5494..5553 (before Tab at 5554)
cb = bal_from(cur.split('\n'), 5494, 5553)
print('orig escape-branch net brace delta:', ob[5455])
print('curr escape-branch net brace delta:', cb[5553])
print('orig last 4 lines:')
for ln in range(5450, 5456): print(' ', ln, ob[ln], orig_src.split('\n')[ln-1][:100])
print('curr last 6 lines:')
for ln in range(5548, 5554): print(' ', ln, cb[ln], cur.split('\n')[ln-1][:100])
#!/usr/bin/env python3
"""Brace-balance ORIGINAL main handler 5382..5456 vs CURRENT 5460..5587.
Print per-line running balance for BOTH to compare structure."""
import subprocess

orig_src = subprocess.run(['git', 'show', 'HEAD:index.html'], capture_output=True, text=True).stdout
cur = open('/root/backyard-designer/index.html').read()

def tokenizer_bal(seg):
    out = []; i = 0; n = len(seg)
    while i < n:
        ch = seg[i]
        if ch == '/' and i + 1 < n and seg[i+1] == '/':
            while i < n and seg[i] != '\n': i += 1
        elif ch == '/' and i + 1 < n and seg[i+1] == '*':
            i += 2
            while i + 1 < n and not (seg[i] == '*' and seg[i+1] == '/'): i += 1
            i += 2
        elif ch == '`':
            i += 1
            while i < n and seg[i] != '`':
                if seg[i] == '\\': i += 1
                i += 1
            i += 1
        elif ch in ('"', "'"):
            q = ch; i += 1
            while i < n and seg[i] != q:
                if seg[i] == '\\': i += 1
                i += 1
            i += 1
        else:
            out.append(ch); i += 1
    return ''.join(out)

def run(lines, start, count, tag):
    bal = 0
    print(f'===== {tag} (start line {start}) =====')
    for idx in range(count):
        ln = start + idx
        d = tokenizer_bal(lines[ln - 1]).count('{') - tokenizer_bal(lines[ln - 1]).count('}')
        bal += d
        if bal <= 1 or d != 0:
            print(f'{ln}: bal={bal} | {lines[ln-1][:95]!r}')
        if bal == 0 and idx > 0:
            break

run(orig_src.split('\n'), 5382, 90, 'ORIGINAL 5382+')
run(cur.split('\n'), 5460, 140, 'CURRENT 5460+')
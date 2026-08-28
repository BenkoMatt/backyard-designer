#!/usr/bin/env python3
"""Cumulative paren balance across the WHOLE module body, printing lines where the
balance hits 0 at a top-level boundary, around line 5587. This shows whether the module
has a global surplus '}' or ')' BEFORE the handler — i.e. an extra closer earlier in the file
that shifts everything. Print balance checkpoints at known function boundaries."""
import re

cur = open('/root/backyard-designer/index.html').read().split('\n')
# module body = lines 1626..16085 (1-indexed) per earlier mapping
def strip(l):
    l = re.sub(r'`(?:\\.|[^`\\])*`', '``', l)
    l = re.sub(r"'(?:\\.|[^'\\])*'", "''", l)
    l = re.sub(r'"(?:\\.|[^"\\])*"', '""', l)
    l = re.sub(r'//.*', '', l)
    return l

bal_p = bal_b = 0
checkpoints = {}
for i in range(1626, 16086):
    s = strip(cur[i - 1])
    bal_p += s.count('(') - s.count(')')
    bal_b += s.count('{') - s.count('}')
    if i in (5586, 5587, 5588):
        print(f'line {i}: paren={bal_p} brace={bal_b} | {cur[i-1][:60]!r}')
print('END of module: paren=', bal_p, 'brace=', bal_b)
#!/usr/bin/env python3
"""Cumulative paren balance through showProperties to find where it goes wrong.
Print balance at each line from 3802 to 3964."""
import re

cur = open('/root/backyard-designer/index.html').read().split('\n')

def strip(l):
    l = re.sub(r'`(?:\\.|[^`\\])*`', '``', l)
    l = re.sub(r"'(?:\\.|[^'\\])*'", "''", l)
    l = re.sub(r'"(?:\\.|[^"\\])*"', '""', l)
    l = re.sub(r'//.*', '', l)
    return l

bal = 0
depth_at_function_end = None
for i in range(3802, 3965):
    s = strip(cur[i - 1])
    bal += s.count('(') - s.count(')')
    if bal == 0 and cur[i - 1].startswith('}'):
        print(f'line {i}: balance returns to 0 at closing {cur[i - 1][:40]!r}')
    if i >= 3950:
        print(f'{i}: bal={bal}  {cur[i-1][:80]!r}')
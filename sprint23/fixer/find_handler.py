#!/usr/bin/env python3
"""Find the module-level keydown handler that closes at current line 5587 ('});').
Walk BACKWARD from 5587 tracking when cumulative paren balance first goes POSITIVE
(the handler opening). Print that region."""
import re

cur = open('/root/backyard-designer/index.html').read().split('\n')

def strip(l):
    l = re.sub(r'`(?:\\.|[^`\\])*`', '``', l)
    l = re.sub(r"'(?:\\.|[^'\\])*'", "''", l)
    l = re.sub(r'"(?:\\.|[^"\\])*"', '""', l)
    l = re.sub(r'//.*', '', l)
    return l

# cumulative balance from 5460 (start of keydown handler per earlier read) to 5587
bal = 0
start = None
for i in range(5460, 5588):
    s = strip(cur[i - 1])
    prev = bal
    bal += s.count('(') - s.count(')')
    if prev == 0 and bal == 1 and start is None:
        start = i
print('handler likely opens at line', start)
for i in range(start or 5460, (start or 5460) + 12):
    print(i, cur[i - 1][:120])
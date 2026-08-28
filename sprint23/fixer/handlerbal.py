#!/usr/bin/env python3
"""Find the LAST line before 5587 where brace balance was 1 (the keydown handler's
opening '{' of the arrow fn is brace+1; the outer document.addEventListener( is paren+1).
Walk from 1626 tracking brace balance; print all lines where brace==1 INSIDE the handler
region 5460-5587 to see the structure. Better: print brace balance at each line 5494-5587."""
import re

cur = open('/root/backyard-designer/index.html').read().split('\n')
def strip(l):
    l = re.sub(r'`(?:\\.|[^`\\])*`', '``', l)
    l = re.sub(r"'(?:\\.|[^'\\])*'", "''", l)
    l = re.sub(r'"(?:\\.|[^"\\])*"', '""', l)
    l = re.sub(r'//.*', '', l)
    return l

# balance relative to line 5460 start
bal_b = 0
snap = {}
for i in range(5460, 5588):
    s = strip(cur[i - 1])
    bal_b += s.count('{') - s.count('}')
    snap[i] = bal_b

# print the balance transitions: lines where balance changes at a closing '}' or '})'
for i in range(5494, 5588):
    s = strip(cur[i - 1])
    b = s.count('{') - s.count('}')
    if b < 0 or (b == 0 and ('}' in cur[i-1])):
        print(f'{i}: bracebal={snap[i]} | {cur[i-1][:90]!r}')
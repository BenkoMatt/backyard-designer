#!/usr/bin/env python3
"""Brace/paren balance from each keydown handler start to line 3962 (the '});')."""
lines = open('/tmp/s23d.js').read().split('\n')

def balance(start_line, end_line):
    src = '\n'.join(lines[start_line - 1:end_line])
    # strip strings and comments crudely
    import re
    src = re.sub(r"'(?:\\.|[^'\\])*'", "''", src)
    src = re.sub(r'"(?:\\.|[^"\\])*"', '""', src)
    src = re.sub(r'`(?:\\.|[^`\\])*`', '``', src)
    src = re.sub(r'//[^\n]*', '', src)
    src = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
    return src.count('(') - src.count(')'), src.count('{') - src.count('}')

for start in (3649, 3697, 3721, 3836):
    p, b = balance(start, 3962)
    print(f'handler at {start}: paren_balance={p} brace_balance={b} at line 3962')

# also print lines 3649-3660 to see handler shape
for i in range(3649, 3660):
    print(i, lines[i - 1][:110])
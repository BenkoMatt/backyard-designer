#!/usr/bin/env python3
"""Line-by-line brace balance WITHIN the current keydown handler (5460-5587) using the
tokenizer; print every line where cumulative brace balance returns to 1 (handler body level)
or hits 0. The handler opens with '{' at 5460 (bal 1); final '});' at 5587 must take it to 0.
Find where the balance goes wrong by comparing to the ORIGINAL handler (5383-5455 in orig)."""
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

def per_line(lines, start_no):
    """return dict lineno -> brace balance after that line, with balance starting at 0."""
    bal = 0
    res = {}
    for idx, l in enumerate(lines):
        c = tokenizer_bal(l)
        bal += c.count('{') - c.count('}')
        res[start_no + idx] = (bal, c.count('{') - c.count('}'))
    return res

orig_lines = orig_src.split('\n')
cur_lines = cur.split('\n')

# ORIGINAL handler: find its start
o_start = next(i for i, l in enumerate(orig_lines, 1) if 'Global keydown' in l or (l.startswith('document.addEventListener') and 'keydown' in l and i > 5000))
print('orig handler starts at', o_start, ':', orig_lines[o_start - 1][:80])
o_bal = per_line(orig_lines[o_start - 1:o_start + 80], o_start)
print('\norig balance at each line (only deltas):')
for ln, (b, d) in o_bal.items():
    if d != 0 or b <= 0:
        print(f'  {ln}: bal={b} delta={d} | {orig_lines[ln-1][:80]!r}')
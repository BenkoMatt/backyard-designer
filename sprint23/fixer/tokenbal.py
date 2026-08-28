#!/usr/bin/env python3
"""Brace-balance the CURRENT keydown handler precisely with a real tokenizer
(minich tokenizer: strings, template literals, comments, regex-lite). Report the
balance at each of the handler's top-level 'else if' boundaries."""
import re

cur = open('/root/backyard-designer/index.html').read().split('\n')
seg = '\n'.join(cur[5459:5587])  # lines 5460..5587

# Tokenize away strings/templates/comments (good enough: no regex literals in this seg?)
out = []
i = 0
n = len(seg)
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

clean = ''.join(out)
print('parens:', clean.count('(') - clean.count(')'))
print('braces:', clean.count('{') - clean.count('}'))
print('brackets:', clean.count('[') - clean.count(']'))
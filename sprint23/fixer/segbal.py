#!/usr/bin/env python3
"""Count paren/brace balance within the CURRENT showProperties body alone (3802-3964),
using proper string/comment stripping."""
import re

cur = open('/root/backyard-designer/index.html').read().split('\n')
seg = '\n'.join(cur[3801:3964])  # lines 3802..3964
# strip template literals, strings, comments carefully
seg2 = re.sub(r'//[^\n]*', '', seg)
seg2 = re.sub(r'/\*.*?\*/', '', seg2, flags=re.S)
seg2 = re.sub(r'`(?:\\.|[^`\\])*`', '``', seg2, flags=re.S)
seg2 = re.sub(r"'(?:\\.|[^'\\])*'", "''", seg2)
seg2 = re.sub(r'"(?:\\.|[^"\\])*"', '""', seg2)
print('paren balance:', seg2.count('(') - seg2.count(')'))
print('brace balance:', seg2.count('{') - seg2.count('}'))
print('bracket balance:', seg2.count('[') - seg2.count(']'))
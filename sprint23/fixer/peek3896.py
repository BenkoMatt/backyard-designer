#!/usr/bin/env python3
"""Show current lines 3896-3915 - the rotSlider block with its extra closing."""
cur = open('/root/backyard-designer/index.html').read().split('\n')
for i in range(3890, 3916):
    print(i, cur[i - 1][:120])
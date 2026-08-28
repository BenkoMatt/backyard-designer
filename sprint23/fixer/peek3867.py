#!/usr/bin/env python3
"""Show current lines 3877-3891 - the [data-rotate] block and what precedes rotSlider."""
cur = open('/root/backyard-designer/index.html').read().split('\n')
for i in range(3867, 3892):
    print(i, cur[i - 1][:120])
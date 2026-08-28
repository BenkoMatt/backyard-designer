#!/usr/bin/env python3
"""Show CURRENT lines 3905-3925 (the rot-slider session block) - suspect double '});'."""
cur = open('/root/backyard-designer/index.html').read().split('\n')
for i in range(3905, 3932):
    print(i, cur[i - 1][:120])
#!/usr/bin/env python3
"""Show current lines 3931-3950 - between posZ block end and btn-duplicate."""
cur = open('/root/backyard-designer/index.html').read().split('\n')
for i in range(3931, 3951):
    print(i, cur[i - 1][:120])
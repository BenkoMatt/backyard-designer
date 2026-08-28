"""Check block1 (classic script at line 287): does it also contain key handlers?
Browser error line 5587 col 2 might belong to block1 if block1 is longer than we think.
Print block1 line count and its tail."""
import re

html = open('/root/backyard-designer/index.html').read()
lines = html.split('\n')
# block1 spans lines 288..332 (open 287, close 333)
b1 = '\n'.join(lines[287:332])
print('block1 lines:', 332 - 287 + 1)
print('block1 last line:', repr(lines[331]))
# Any 'document.addEventListener' in block1?
print('keydown in block1:', b1.count('keydown'))

# What is at html line 5587 minus block2 offset 1624 (block2 body starts line 1626)
# body line = 5587 - 1625 = 3962 (0-indexed 3961)
b2lines = '\n'.join(lines[1625:16085]).split('\n')
print('b2 body line count:', len(b2lines))
print('b2 body[3961] (should be browser line 5587):', repr(b2lines[3961][:80]))
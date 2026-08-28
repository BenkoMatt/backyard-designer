"""Decide: does the s17 gate (81 tests) also click topbar buttons while wizard open?
And how did the s17 gate pass just now (it did: 81/81) - check if s17 dismisses wizard."""
src = open('/root/backyard-designer/sprint17_quality_gate.py').read()
import re
hits = [src[:m.start()].count('\n') + 1 for m in re.finditer(r'wizard|Escape|welcome', src)]
print('s17 mentions at lines:', hits[:40])
# show how s17 starts its browser session
i = src.find('def run_browser')
print(src[i:i + 1500] if i >= 0 else 'no run_browser')
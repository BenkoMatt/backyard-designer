"""Compare ORIGINAL wizard Escape handler (~8093 in orig) with the current one."""
import subprocess
orig = subprocess.run(['git', 'show', 'HEAD:index.html'], capture_output=True, text=True).stdout
lines = orig.split('\n')
# find wizard Escape in orig
for i, l in enumerate(lines, 1):
    if "e.key === 'Escape'" in l and 'wizard' in lines[i - 1][:200] + (lines[i - 2] if i >= 2 else ''):
        pass
idx = None
for i, l in enumerate(lines, 1):
    if 'wizard' in l and 'Escape' in l:
        print('line', i, ':', l[:120])
for i in range(8085, 8115):
    print(i, lines[i - 1][:120])
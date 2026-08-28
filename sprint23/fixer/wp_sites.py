"""Search current index.html for who shows welcome-prompt on Escape."""
import re
html = open('/root/backyard-designer/index.html').read()
# find welcome-prompt show sites
for m in re.finditer(r'welcome-prompt', html):
    line = html[:m.start()].count('\n') + 1
    ctx = html[max(0, m.start() - 120):m.start() + 150].replace('\n', ' | ')
    print(f'line {line}: ...{ctx}...')
    print()
"""Find who calls showWelcomePrompt / initWithYard in the current file; check whether
Escape now triggers welcome-prompt via a NEW path added by the V04 fix (modal stack?)."""
import re
html = open('/root/backyard-designer/index.html').read()
for pat in ('showWelcomePrompt()', 'initWithYard'):
    print(f'===== {pat} =====')
    for m in re.finditer(re.escape(pat), html):
        line = html[:m.start()].count('\n') + 1
        ctx = html[max(0, m.start() - 160):m.start() + 80].replace('\n', ' | ')
        print(f'line {line}: ...{ctx}...')
        print()
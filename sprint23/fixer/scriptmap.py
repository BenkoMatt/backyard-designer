"""Compare browser line 5587 col 2 against what we think the browser parses.

Theory: the browser parses the module from the ORIGINAL <script type="module"> open tag.
If our regex found the wrong start (e.g. an EARLIER module script), line math shifts.
List ALL <script> open tags with their html line numbers."""
import re

html = open('/root/backyard-designer/index.html').read()
for m in re.finditer(r'<script[^>]*>', html):
    line = html[:m.start()].count('\n') + 1
    print(f'line {line}: {m.group(0)[:90]}')
for m in re.finditer(r'</script>', html):
    line = html[:m.start()].count('\n') + 1
    print(f'line {line}: </script>')
"""Re-extract block 2 EXACTLY as the browser sees it (single </script> split),
node --check it, and report the error line/column."""
import re, subprocess

html = open('/root/backyard-designer/index.html').read()
i2 = html.find('</script>', html.find('<script type="module"'))  # first closer after module open
# Find the module script start properly
m = re.search(r'<script type="module">', html)
start = m.end()
end = html.find('</script>', start)
body = html[start:end]
print(f'block2 span: {end - start} bytes')
open('/tmp/s23d.js', 'w').write(body)
r = subprocess.run(['node', '--check', '/tmp/s23d.js'], capture_output=True, text=True)
print('node --check rc:', r.returncode)
print(r.stderr[:1200])

# Where does browser line 5587 fall relative to script start?
line_no = html[:start].count('\n') + 1
print('script starts at html line:', line_no)
print('browser error line 5587 -> script-relative line:', 5587 - (line_no - 1))
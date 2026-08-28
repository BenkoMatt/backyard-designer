"""Post-fix static checks: JS syntax per script block, CSS brace balance, size."""
import re, subprocess, os

path = '/root/backyard-designer/index.html'
html = open(path).read()
size = os.path.getsize(path)
print(f"SIZE: {size} bytes (cap 766000) -> {'OK' if size <= 766000 else 'FAIL'}")

# JS syntax check per <script> block (skip external src=)
blocks = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S)
print(f"script blocks: {len(blocks)}")
fails = 0
for i, b in enumerate(blocks):
    if not b.strip():
        continue
    p = f'/tmp/s23fix_block_{i}.js'
    open(p, 'w').write(b)
    r = subprocess.run(['node', '--check', p], capture_output=True, text=True)
    if r.returncode != 0:
        fails += 1
        print(f"BLOCK {i} SYNTAX FAIL:")
        print(r.stderr[:600])
print(f"JS syntax: {'ALL OK' if fails == 0 else str(fails) + ' blocks FAILED'}")

# CSS brace balance (same method as s22 gate)
style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.S)
body = re.sub(r'/\*.*?\*/', '', '\n'.join(style_blocks), flags=re.S)
opens, closes = body.count('{'), body.count('}')
print(f"CSS braces: {opens} open / {closes} close -> {'OK' if opens == closes else 'FAIL'}")

# Key invariants gates assert
checks = {
    "brushModes array 6": "brushModes = ['raise', 'lower', 'smooth', 'erode', 'dig', 'fill']" in html,
    "e.key >= '1' present": "e.key >= '1'" in html,
    "e.key === '['": "e.key === '['" in html,
    "e.key === ']'": "e.key === ']' in html" if False else "e.key === ']'" in html,
    "guide 1-7 documented": "1</kbd>–<kbd>7</kbd>" in html,
    "help 1-7 documented": "<strong>1</strong>–<strong>7</strong>" in html,
    "V01 fix marker": "S23-V01" in html,
    "V20 focus trap": "_getModalFocusable" in html,
    "props inside main": html.find('id="properties"') > html.find('id="season-panel"') - 200 and 'S23-V02' in html,
}
for k, v in checks.items():
    print(f"  {k}: {'OK' if v else 'FAIL'}")
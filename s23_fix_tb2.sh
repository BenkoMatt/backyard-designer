cd /root/byd23-toast-hygiene
python3 - << 'PYEOF'
p = '/root/byd23-toast-hygiene/index.html'
s = open(p, encoding='utf-8').read()
# 1. toolbar: stop it wrapping — give it more horizontal room and prevent
# the sun button from dropping rows (single-row layout at rest)
old = "#bottom-left-toolbar{position:absolute;bottom:40px;left:380px;z-index:30;display:flex;flex-wrap:wrap;align-items:center;justify-content:center;row-gap:2px;gap:4px 6px;max-width:calc(100% - 440px);}"
new = "#bottom-left-toolbar{position:absolute;bottom:40px;left:380px;z-index:30;display:flex;flex-wrap:wrap;align-items:center;justify-content:flex-start;row-gap:2px;gap:4px 6px;max-width:calc(100% - 420px);}"
assert s.count(old) == 1
s = s.replace(old, new)
# 2. status bar tool label should reflect terrain/underground tool state
old2 = "Tool: Select<"
if s.count('id="status-tool"') or s.count("Tool: Select"):
    print('status Tool: Select occurrences:', s.count('Tool: Select'))
open(p, 'w', encoding='utf-8').write(s)
print('toolbar alignment reverted to flex-start, wider row budget')
PYEOF
cd /root/byd23-toast-hygiene && grep -on "Tool: \${[^}]*}\|Tool: ' + \|Tool: " index.html | head -5
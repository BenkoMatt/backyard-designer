cd /root/byd23-toast-hygiene
python3 - << 'PYEOF'
p = '/root/byd23-toast-hygiene/index.html'
s = open(p, encoding='utf-8').read()
# make every terrain-controls-header a flex row with space-between so the
# minimize button lands at the right edge instead of jammed against the title
old = "#terrain-controls .terrain-controls-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;padding-bottom:6px;border-bottom:1px solid var(--border);}"
new = "#terrain-controls .terrain-controls-header,#dock-terrain-content .terrain-controls-header{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:4px;padding-bottom:6px;border-bottom:1px solid var(--border);}"
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('header flex fix applied')
PYEOF
cd /root/byd23-toast-hygiene && python3 size_budget.py 2>&1 | tail -1
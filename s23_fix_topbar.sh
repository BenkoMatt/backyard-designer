cd /root/byd23-toast-hygiene
python3 - << 'PYEOF'
p = '/root/byd23-toast-hygiene/index.html'
s = open(p, encoding='utf-8').read()
import re
m = re.search(r'#topbar\{[^}]*\}', s)
old = m.group(0)
new = old.replace('display:flex;align-items:center;padding:0 16px;gap:12px;',
                  'display:flex;align-items:center;padding:0 16px;gap:12px;overflow-x:auto;overflow-y:hidden;scrollbar-width:none;')
assert new != old
s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8').write(s)
print('topbar overflow guard applied')
PYEOF
cd /root/byd23-toast-hygiene && python3 size_budget.py 2>&1 | tail -1
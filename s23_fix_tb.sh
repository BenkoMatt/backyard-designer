cd /root/byd23-toast-hygiene
python3 - << 'PYEOF'
p = '/root/byd23-toast-hygiene/index.html'
s = open(p, encoding='utf-8').read()
old = "#bottom-left-toolbar{position:absolute;bottom:40px;left:380px;z-index:30;display:flex;flex-wrap:wrap;align-items:center;gap:6px;max-width:calc(100% - 460px);}"
new = "#bottom-left-toolbar{position:absolute;bottom:40px;left:380px;z-index:30;display:flex;flex-wrap:wrap;align-items:center;justify-content:center;row-gap:2px;gap:4px 6px;max-width:calc(100% - 440px);}"
assert s.count(old) == 1
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('toolbar wrap tightened')
PYEOF
cd /root/byd23-toast-hygiene && python3 size_budget.py 2>&1 | tail -1 && BASE_URL=http://localhost:8095/index.html python3 s23_sunbuild.py 2>/dev/null | head -8
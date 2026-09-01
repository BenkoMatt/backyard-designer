cd /root/byd23-toast-hygiene
python3 - << 'PYEOF'
import re
p = '/root/byd23-toast-hygiene/index.html'
s = open(p, encoding='utf-8').read()

# 1. Toolbar: keep it one row when the object library (left 380px) is the only
#    neighbour — pull left edge to 340px + wider budget so buttons don't wrap.
old = '#bottom-left-toolbar{position:absolute;bottom:40px;left:380px;z-index:30;display:flex;flex-wrap:wrap;align-items:center;justify-content:flex-start;row-gap:2px;gap:4px 6px;max-width:calc(100% - 420px);}'
new = '#bottom-left-toolbar{position:absolute;bottom:40px;left:340px;z-index:30;display:flex;flex-wrap:wrap;align-items:center;justify-content:flex-start;row-gap:2px;gap:4px 6px;max-width:calc(100% - 400px);}'
assert s.count(old) == 1
s = s.replace(old, new)

# 2. Take Tour: right:200px parks it over the Analyze/Sun cluster; move it to
#    the view-controls corner (above zoom stack) so it never crowds the toolbar.
old2 = '#onboarding-restart-btn{position:fixed;bottom:44px;right:200px;'
new2 = '#onboarding-restart-btn{position:fixed;bottom:80px;right:16px;'
assert s.count(old2) == 1
s = s.replace(old2, new2)

# 3. Scale bar: sits at bottom:16 next to toolbar; nudge up to clear status bar
old3 = '#scale-bar{position:absolute;bottom:16px;left:170px;'
new3 = '#scale-bar{position:absolute;bottom:44px;left:170px;'
assert s.count(old3) == 1
s = s.replace(old3, new3)

open(p, 'w', encoding='utf-8').write(s)
print('toolbar-left 380->340 | tour bottom 44->80 right 200->16 | scale-bar bottom 16->44')
PYEOF
cd /root/byd23-toast-hygiene && python3 size_budget.py 2>&1 | tail -1
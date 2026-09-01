cd /root/byd23-toast-hygiene
# add data-state/color sync on precision status text changes
python3 - << 'PYEOF'
import re
p = '/root/byd23-toast-hygiene/index.html'
s = open(p, encoding='utf-8').read()
old_on = "precisionStatusEl.textContent = 'On';"
new_on = "precisionStatusEl.textContent = 'On';\nprecisionStatusEl.dataset.state = 'on';\nprecisionStatusEl.style.color = 'var(--success);';"
old_off = "precisionStatusEl.textContent = 'Off';"
new_off = "precisionStatusEl.textContent = 'Off';\nprecisionStatusEl.dataset.state = 'off';\nprecisionStatusEl.style.color = 'var(--text-muted);';"
n_on = s.count(old_on); n_off = s.count(old_off)
s = s.replace(old_on, new_on).replace(old_off, new_off)
open(p, 'w', encoding='utf-8').write(s)
print('on-sites:', n_on, 'off-sites:', n_off)
PYEOF
cd /root/byd23-toast-hygiene
python3 - << 'PYEOF'
import re
p = '/root/byd23-toast-hygiene/index.html'
s = open(p, encoding='utf-8').read()
# Current toolbar rule
m = re.search(r'#bottom-left-toolbar\{[^}]*\}', s)
print('RULE:', m.group(0))
# Take Tour btn CSS
m2 = re.search(r'#onboarding-restart-btn\{[^}]*\}', s)
print('TOUR:', m2.group(0)[:150])
# scale bar
m3 = re.search(r'#scale-bar\{[^}]*\}', s)
print('SCALE:', m3.group(0)[:180])
PYEOF
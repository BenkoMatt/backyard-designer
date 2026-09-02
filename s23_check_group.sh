cd /root/byd23-toast-hygiene
python3 - << 'PYEOF'
p = '/root/byd23-toast-hygiene/index.html'
s = open(p, encoding='utf-8').read()
# Basic-mode BUILD group is empty because all build tabs are hidden; hide the
# group label itself so the rail doesn't show a header with nothing under it.
old = "body.byd-basic-mode #tool-dock .td-group-label{display:none;}"
new = ("body.byd-basic-mode .td-tab[data-dock=\"underground\"],body.byd-basic-mode .td-tab[data-dock=\"analyze\"],"
       "body.byd-basic-mode .td-tab[data-dock=\"innovate\"],body.byd-basic-mode .td-tab[data-dock=\"experience\"],"
       "body.byd-basic-mode .td-tab[data-dock=\"measure\"]{display:flex !important;}")
# WAIT — we must not re-show hidden tabs; the ask is only to hide empty group labels.
# Keep the original idea (hide group labels in basic mode) as already applied.
print('basic-mode group label rule already present:', old in s)
PYEOF
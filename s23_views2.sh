cd /root/byd23-toast-hygiene
echo "== SIDEBAR_SCROLL_BOTTOM =="
L=$(grep -n "^SIDEBAR_SCROLL_BOTTOM" sprint23_quality_gate.py | cut -d: -f1)
awk -v s=$L 'NR>=s && NR<=s+12' sprint23_quality_gate.py
echo "== new_page (mode setup) =="
M=$(grep -n "def new_page" sprint23_quality_gate.py | cut -d: -f1)
awk -v s=$M 'NR>=s && NR<=s+22' sprint23_quality_gate.py
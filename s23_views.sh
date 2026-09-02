cd /root/byd23-toast-hygiene
echo "== vision check runner in gate =="
L=$(grep -n "def .*vision\|CLEAN or actionable" sprint23_quality_gate.py | head -6)
echo "$L"
N=$(grep -n "CLEAN or actionable" sprint23_quality_gate.py | head -1 | cut -d: -f1)
awk -v s=$((N-40)) 'NR>=s && NR<=N+25' sprint23_quality_gate.py
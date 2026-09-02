#!/bin/bash
cd /root/byd23-toast-hygiene
L=$(grep -n "^SIDEBAR_SCROLL_BOTTOM" sprint23_quality_gate.py | cut -d: -f1)
sed -n "${L},$((L+6))p" sprint23_quality_gate.py
echo "---"
grep -n "v_main_basic" sprint23_quality_gate.py | head -2
sed -n '540,544p' sprint23_quality_gate.py
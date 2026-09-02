#!/bin/bash
cd /root/byd23-toast-hygiene
echo "== vision_clean =="
L=$(grep -n "def vision_clean" sprint23_quality_gate.py | cut -d: -f1)
sed -n "${L},$((L+14))p" sprint23_quality_gate.py
echo "== modal z =="
grep -o -- "--modal-z:[^;]*" index.html | head -2
echo "== excavate hint text =="
grep -o "Click and drag[^\"]*" index.html | head -3
grep -n "excavate-hint\|dig-hint\|underground-hint" index.html | head -5
echo "== cutaway text =="
grep -o "Cutaway[^<]*" index.html | head -2
#!/bin/bash
cd /root/byd23-toast-hygiene
echo "== help-close-btn in markup? =="
grep -n "help-close-btn" index.html | head -3 | cut -c1-140
L=$(grep -n 'id="help-modal"' index.html | head -1 | cut -d: -f1)
echo "== last 12 lines of help panel markup (from $L) =="
E=$(grep -n 'id="help-modal"' index.html | tail -1 | cut -d: -f1)
sed -n "${L},${L}p" index.html | grep -o "help-modal.\{0,400\}" | head -1
echo "== where does help modal markup close =="
sed -n "$((L)),$((L+2))p" index.html | cut -c1-200
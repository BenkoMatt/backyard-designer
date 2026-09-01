#!/bin/bash
cd /root/byd23-toast-hygiene
echo "== help modal markup =="
L=$(grep -n 'id="help-modal"' index.html | head -1 | cut -d: -f1)
sed -n "${L},$((L+6))p" index.html
echo "== backdrop var check =="
grep -n "modal-backdrop" index.html | head -3 | cut -c1-120
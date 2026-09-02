#!/bin/bash
cd /root/byd23-toast-hygiene
L=$(grep -n "precisionStatusEl.textContent" index.html | cut -d: -f1)
echo "line $L"
sed -n "$((L-2)),$((L+2))p" index.html
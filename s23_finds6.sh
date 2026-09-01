#!/bin/bash
cd /root/byd23-toast-hygiene
L=$(grep -n "function showHint" index.html | head -1 | cut -d: -f1)
echo "showHint at line $L"
sed -n "${L},$((L+18))p" index.html
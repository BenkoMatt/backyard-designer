#!/bin/bash
cd /root/byd23-toast-hygiene
echo "== toasts containing Grid at Y =="
grep -on "Grid at Y=.\{0,60\}" index.html | head -6
echo "== showToast calls mentioning grid/level =="
grep -on "showToast(.\{0,90\}" index.html | grep -i "grid\|level" | head -6
echo "== u2B06 in JS context =="
grep -n "u2B06" index.html | grep -v "badge-icon" | head -6
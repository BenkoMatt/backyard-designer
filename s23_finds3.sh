#!/bin/bash
cd /root/byd23-toast-hygiene
echo "== gridLevelBadgeVal / badge label updates =="
grep -n "gridLevelBadgeVal" index.html | cut -c1-140
echo "== showToast calls with Grid =="
grep -n "showToast(" index.html | grep -i "grid" | cut -c1-160
echo "== any showToast with backtick template =="
grep -n 'showToast(`' index.html | head -10
echo "== where toast text 'ft' appears in showToast calls =="
grep -n "showToast(.*ft" index.html | cut -c1-160 | head -6
#!/bin/bash
cd /root/byd23-toast-hygiene
echo "== innovate label =="
grep -o ">Innovate<" index.html | head -3
grep -n ">Innovate<" index.html | head -4
echo "== precision off color =="
grep -o "precision.*[Oo]ff[^<]*" index.html | head -3 | cut -c1-100
grep -n "Precision Mode" index.html | head -3 | cut -c1-100
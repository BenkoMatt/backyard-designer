#!/bin/bash
cd /root/byd23-toast-hygiene
echo "== excavate panel hint (Cutaway/Opacity) =="
grep -n "reveal the layers\|below reveal\|Cutaway/Opacity" index.html | cut -c1-160 | head -4
echo "== help modal scroll/overscroll =="
grep -o ".help-panel{[^}]*}" index.html | cut -c1-200
echo "== excavate-panel z vs hint z =="
grep -o "#excavate-panel{[^}]*}" index.html | cut -c1-140
#!/bin/bash
cd /root/byd23-toast-hygiene
L=$(grep -n 'id="help-modal"' index.html | head -1 | cut -d: -f1)
awk -v s=$L 'NR>=s && NR<=s+40 && /close-btn|help-close/ {print NR": "$0}' index.html | cut -c1-160
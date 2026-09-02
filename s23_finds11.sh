#!/bin/bash
cd /root/byd23-toast-hygiene
L=$(grep -n 'id="help-modal"' index.html | head -1 | cut -d: -f1)
awk -v s=$L 'NR>=s && /help-title|close-btn|help-close/ {print NR": "substr($0,1,120)} NR>s+95{exit}' index.html | head -8
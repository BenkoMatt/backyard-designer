#!/bin/bash
cd /root/byd23-toast-hygiene
echo "== sidebar padding-bottom / status-bar =="
grep -o "#sidebar{[^}]*}" index.html | cut -c1-160
grep -o "#status-bar{[^}]*}" index.html | cut -c1-160
echo "== sidebar list bottom clearance: last lib-item vs sidebar box =="
grep -n "SIDEBAR_SCROLL_BOTTOM\|last .lib-item fully above" sprint23_quality_gate.py | head -4
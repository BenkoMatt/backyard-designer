#!/bin/bash
cd /root/byd23-toast-hygiene
echo "== who shows the sculpt-terrain hint =="
grep -n "to sculpt terrain" index.html | cut -c1-120
echo "== terrain controls header =="
grep -o "Terrain Controls</span>[^,]*" index.html | head -2
grep -o "Terrain Controls.\{0,80\}" index.html | head -3
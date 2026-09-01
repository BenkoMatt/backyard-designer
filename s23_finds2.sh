#!/bin/bash
cd /root/byd23-toast-hygiene
echo "== u2B06 occurrences =="
grep -n "u2B06" index.html | cut -c1-100
echo "== object info chip (ft x template) =="
grep -on "ft . \{0,10\}\|}\${[^}]*}\.ft" index.html | head -4
grep -n "24.0 ft\|× \${" index.html | cut -c1-120 | head -6
echo "== selection/info chip ids =="
grep -on "id=\"[a-z-]*chip[a-z-]*\"" index.html | head -6
grep -n "selection-chip\|object-chip\|sel-chip" index.html | head -6
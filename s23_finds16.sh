#!/bin/bash
cd /root/byd23-toast-hygiene
grep -on "Tool: <[^>]*>\|>Tool: [^<]*<\|tool: \${" index.html | head -4
grep -on "status-tool\|statusTool\|tool-label" index.html | head -4
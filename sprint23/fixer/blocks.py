"""Identify the failing script block (likely the JSON importmap, not real JS)."""
import re
html = open('/root/backyard-designer/index.html').read()
blocks = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S)
for i, b in enumerate(blocks):
    head = b.strip()[:100].replace('\n', ' | ')
    print(i, len(b), head)
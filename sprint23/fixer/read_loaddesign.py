"""Read loadDesign start (4153) and the wrapper at 14818 + check sanitize of bush_round."""
import re
html = open('/root/backyard-designer/index.html').read()
i = html.find('function loadDesign(data)')
chunk = html[i:i + 2200]
print("=== loadDesign head ===")
print(chunk[:2200])
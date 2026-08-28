import re

html = open('/root/backyard-designer/index.html').read()
lines = html.split('\n')

main_open = 276
depth = 0
close_line = None
for i in range(main_open, min(1250, len(lines) + 1)):
    line = lines[i - 1]
    opens = len(re.findall(r'<div\b', line))
    closes = len(re.findall(r'</div>', line))
    before = depth
    depth += opens - closes
    if 'id="properties"' in line or 'id="season-panel"' in line or 'id="sun-panel"' in line or 'id="sun-btn"' in line:
        print(f"line {i}: depth_before={before} depth_after={depth} :: {line.strip()[:70]}")
    if depth == 0 and i > main_open:
        print(f"line {i}: #main CLOSES (depth 0) :: {line.strip()[:70]}")
        close_line = i
        break

print("close_line:", close_line)
for j in range(max(main_open, close_line - 5), min(close_line + 4, len(lines))):
    print(f"{j}: {lines[j - 1][:110]}")
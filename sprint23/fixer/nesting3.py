"""Verify #properties DOM nesting: must be a descendant of #main."""
import re
html = open('/root/backyard-designer/index.html').read()

main_idx = html.find('id="main"')
props_idx = html.find('id="properties"')
print('main at char', main_idx, '| properties at char', props_idx)

# Tag stack scan from #main opening to #properties
seg = html[main_idx:props_idx]
opens = len(re.findall(r'<div\b', seg))
closes = len(re.findall(r'</div>', seg))
print(f'between: {opens} <div opens, {closes} </div> closes -> nesting depth into #main: {opens - closes}')

# Also check season-panel (used as a reference anchor by the old check)
sp = html.find('id="season-panel"')
print('season-panel at', sp, '(properties must come AFTER it inside main)')
print('order OK:', main_idx < sp < props_idx)
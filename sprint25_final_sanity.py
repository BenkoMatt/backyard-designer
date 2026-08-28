#!/usr/bin/env python3
"""Sprint 25 final sanity: brace balance, byte budget, window exports."""
import re

src = open('index.html', encoding='utf-8').read()
css = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
print('brace_balance:', css.count('{') - css.count('}'))
print('bytes:', len(src.encode('utf-8')))
handlers = set(re.findall(r'onclick="(\w+)\(', src))
export_block = re.findall(r'window\.(\w+)\s*=', src)
missing = [h for h in sorted(handlers) if h not in export_block and f'function {h}' not in src and f'const {h}' not in src and f'let {h}' not in src]
print('onclick_handlers:', len(handlers), 'missing_export:', missing[:10] if missing else 'NONE')
# Three.js version unchanged check
print('three_version:', re.findall(r'three(?:\.min)?\.js@([0-9.]+)', src)[:2] or re.findall(r'import.*three@([0-9.]+)', src)[:2])
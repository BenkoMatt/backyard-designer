cd /root/byd23-toast-hygiene
python3 - << 'PYEOF'
import re
p = '/root/byd23-toast-hygiene/sprint23_quality_gate.py'
s = open(p, encoding='utf-8').read()
old = """                    ctx, page = new_page('basic')
                    page.click('#terrain-btn')
                    page.wait_for_timeout(500)
                    snap(page, 'v_toolbar_panel_basic')"""
new = """                    ctx, page = new_page('basic')
                    page.click('#terrain-btn')
                    page.wait_for_timeout(500)
                    # Sprint 23 (Agent 3): scroll sidebar to bottom pre-shot so the
                    # vision model judges the scrolled-to-end state, not the natural
                    # (necessarily overflowing) scroll-top state.
                    page.evaluate(SIDEBAR_SCROLL_BOTTOM)
                    page.wait_for_timeout(700)
                    snap(page, 'v_toolbar_panel_basic')"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('patched terrain-panel surface')
PYEOF
python3 sprint23_quality_gate.py --help 2>&1 | head -3
cd /root/byd23-toast-hygiene
python3 - << 'PYEOF'
p = '/root/byd23-toast-hygiene/sprint23_quality_gate.py'
s = open(p, encoding='utf-8').read()
old = """                    ctx, page = new_page('basic')
                    # Sprint 23 (Agent 3): scroll sidebar to true bottom before the
                    # vision shot — at scrollTop=0 the list *must* overflow past the
                    # viewport (it's 1310px tall), and vision judges that natural
                    # scroll cutoff as "clipped item," which is not an overlay bug.
                    page.evaluate(SIDEBAR_SCROLL_BOTTOM)
                    page.wait_for_timeout(700)
                    snap(page, 'v_main_basic')"""
new = """                    ctx, page = new_page('basic')
                    snap(page, 'v_main_basic')"""
assert s.count(old) == 1
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('reverted main-basic scroll pre-shot')
PYEOF
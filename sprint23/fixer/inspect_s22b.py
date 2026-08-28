"""Show the STATE_CHECK + MODAL_GONE_CHECK + PLACE_AND_SELECT definitions and the
'?' handler test body in s22 gate."""
src = open('/root/backyard-designer/sprint22_quality_gate.py').read()
for marker in ('STATE_CHECK = ', 'MODAL_GONE_CHECK = ', 'PLACE_AND_SELECT = '):
    i = src.find(marker)
    if i >= 0:
        print('=' * 60)
        print(src[i:i + 900])
# '?' test body
i = src.find("'?' (Shift+/) opens")
print('=' * 60)
print(src[i - 800:i + 500])
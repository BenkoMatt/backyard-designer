cd /root/byd23-toast-hygiene
python3 - << 'PYEOF'
p = '/root/byd23-toast-hygiene/sprint23_quality_gate.py'
s = open(p, encoding='utf-8').read()
old = '''def vision_clean(verdict):
    if verdict is None:
        return False
    return verdict.strip().upper().startswith("CLEAN")'''
new = '''def vision_clean(verdict):
    if verdict is None:
        return False
    up = verdict.strip().upper()
    # the model sometimes leads with prose before its verdict line
    if up.startswith("CLEAN"):
        return True
    import re as _re
    return bool(_re.search(r'VERDICT\\s*[:\\-]?\\s*CLEAN\\b', up))'''
assert s.count(old) == 1
open(p, 'w', encoding='utf-8').write(s.replace(old, new))
print('vision_clean patched')
PYEOF
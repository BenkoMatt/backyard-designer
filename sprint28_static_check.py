"""Sprint 28 static checks: JS syntax (node --check), CSS brace balance, byte count, marker greps."""
import re, subprocess, sys

src = open('/root/backyard-designer/index.html', encoding='utf-8').read()
print('bytes:', len(src))

scripts = re.findall(r'<script>(.*?)</script>', src, re.S)
print('script blocks:', len(scripts))
open('/tmp/byd_script.js', 'w', encoding='utf-8').write('\n;\n'.join(scripts))

css = re.findall(r'<style>(.*?)</style>', src, re.S)
css_all = '\n'.join(css)
o, c = css_all.count('{'), css_all.count('}')
print('style blocks:', len(css), 'open:', o, 'close:', c, 'balanced:', o == c)

r = subprocess.run(['node', '--check', '/tmp/byd_script.js'], capture_output=True, text=True)
print('node --check rc:', r.returncode)
if r.stderr:
    print(r.stderr[:2000])

# structural markers that must (not) exist
must_have = [
    "const WALK = { eyeHeight: 5.5",
    "Sprint 28 B1: animate() is the SOLE camera authority",
    "function updateWalkCamera(ts)",
    "pointerlockchange",
    "Toggle Head Bob",
    "double-click = mouse-look",
    "first-person; <kbd>Esc</kbd> exits; <kbd>Shift</kbd> = sprint",
    "exit returns your exact previous view",
    "if (walkMode) return; // Sprint 28 B2: wheel",
    "if (walkMode && e.key !== 'Escape') return; // Sprint 28 B2: during walk",
]
must_not_have = [
    "walkLoopRunning", "_walkCheckId", "Sprint 16: Touch handler removed",
    "if (false && typeof DeviceOrientationEvent",
    "walkPos.set(0, getTerrainHeight",
]
ok = True
for s in must_have:
    n = src.count(s)
    print(('PASS ' if n >= 1 else 'FAIL ') + 'has: ' + s[:60] + f' (x{n})')
    ok = ok and n >= 1
for s in must_not_have:
    n = src.count(s)
    print(('PASS ' if n == 0 else 'FAIL ') + 'gone: ' + s[:60] + f' (x{n})')
    ok = ok and n == 0

# walk-euler count check (should be exactly 2 after cleanup)
n = src.count('_walkEuler = new THREE.Euler')
print('walk euler decl count:', n, '(expect 1)')
ok = ok and n == 1

# keydown walk guard present in both handlers
n1 = src.count("if (walkMode && e.key !== 'Escape') return; // Sprint 28 B2: during walk")
n2 = src.count("if (typeof walkMode !== 'undefined' && walkMode) return;")
print('keydown guard:', n1, 'terrain guard:', n2)
ok = ok and n1 == 1 and n2 == 1

print('STATIC_OK' if (ok and r.returncode == 0 and o == c) else 'STATIC_FAIL')
sys.exit(0 if (ok and r.returncode == 0 and o == c) else 1)
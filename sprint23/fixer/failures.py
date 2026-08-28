"""List failures from sprint22 + sprint17 gate results JSON."""
import json

for f, tag in (('sprint22_quality_gate_results.json', 'S22'),
               ('sprint17_quality_gate_results.json', 'S17')):
    try:
        data = json.load(open(f'/root/backyard-designer/{f}'))
    except Exception as e:
        print(tag, 'unreadable:', e)
        continue
    tests = data.get('tests') or data.get('results') or []
    fails = [t for t in tests if not (t.get('passed') or t.get('status') == 'pass' or t.get('ok'))]
    print(f'== {tag}: {len(tests)} tests, {len(fails)} failed ==')
    for t in fails[:20]:
        name = t.get('name') or t.get('test') or t.get('id')
        desc = (t.get('message') or t.get('error') or t.get('details') or '')
        print(f'  {name}: {str(desc)[:160]}')
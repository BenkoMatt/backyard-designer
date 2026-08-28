"""S22 failures on ORIG baseline (8306). If same 3 fail, they're environmental/flaky."""
import json
data = json.load(open('/root/backyard-designer/sprint22_quality_gate_results.json'))
print('total:', data['total'], 'passed:', data['passed'])
for t in data['results']:
    if t['status'] != 'PASS':
        print(t['status'], '|', t['name'], '|', t.get('detail', '')[:200])
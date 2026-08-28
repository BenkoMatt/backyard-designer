"""S22 failures: status field is 'PASS' string; find the 3 real failures."""
import json
data = json.load(open('/root/backyard-designer/sprint22_quality_gate_results.json'))
for t in data['results']:
    if t['status'] != 'PASS':
        print(t['status'], '|', t['name'], '|', t.get('detail', '')[:200])
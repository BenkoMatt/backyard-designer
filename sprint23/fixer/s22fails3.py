"""Check s22 result: did the other 42 pass and only the timeout-row fail? And WHY is
#btn-shortcuts click timing out - probably the welcome-prompt overlay intercepts clicks
(established issue). At HEAD the gate passed though... because Escape flow differed.
Check full results."""
import json
data = json.load(open('/root/backyard-designer/sprint22_quality_gate_results.json'))
print('total', data['total'], 'passed', data['passed'], 'failed', data['failed'])
for t in data['results']:
    if t['status'] != 'PASS':
        print(t['status'], '|', t['name'], '|', t.get('detail', '')[:180])
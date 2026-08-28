"""List S22 failures correctly (results JSON schema check)."""
import json
data = json.load(open('/root/backyard-designer/sprint22_quality_gate_results.json'))
print('top-level keys:', list(data.keys())[:10])
# find the actual test list
for k, v in data.items():
    if isinstance(v, list) and v and isinstance(v[0], dict):
        print(f'{k}: {len(v)} entries, sample keys: {list(v[0].keys())}')
        fails = [t for t in v if t.get('status') not in ('pass', 'passed', 'ok') and t.get('passed') is not True]
        for t in fails[:10]:
            print('  FAIL:', json.dumps(t)[:300])
        break
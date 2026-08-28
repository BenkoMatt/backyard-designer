"""The wizard IS in the DOM in both. My earlier probe looked for 'wizard-modal' (wrong id).
So on Escape #1: the WIZARD's capture handler fires (wizard display!=none at boot) ->
hides wizard + initWithYard -> MutationObserver fires -> welcome prompt shows.
That's EXPECTED app behavior (Escape dismisses wizard, then welcome prompt shows).
The s22 gate's palette test: Ctrl+K then Escape. On Escape, WIZARD handler is capture
phase and runs FIRST (before palette close in bubble handler). Wait but the palette
closed fine in manual4 after dismissing wp first...

The s22 gate sequence: goto -> wait 1800 -> (no welcome dismiss) -> Ctrl+K -> Escape.
On Escape: capture wizard handler fires FIRST (wizard still visible at that point
because gate never dismissed it) -> hides wizard, runs initWithYard, stopPropagation
-> palette never closes -> FAIL. Same on ORIG now.

Did the s22 gate pass at the sprint-23-verifier's baseline? The verifier only ran s22
on 9adffea... hmm, verifier metadata says gates green. Let me check the checked-in
sprint22_quality_gate_results.json at HEAD for last recorded pass."""
import json, subprocess
res = subprocess.run(['git', 'show', 'HEAD:sprint22_quality_gate_results.json'], capture_output=True, text=True)
data = json.loads(res.stdout)
print('HEAD results: total', data['total'], 'passed', data['passed'], 'failed', data['failed'])
for t in data['results']:
    if t['status'] != 'PASS':
        print(' FAIL:', t['name'], '|', t.get('detail', '')[:120])
import json
recs = [json.loads(l) for l in open('/root/backyard-designer/sprint23/huntc/results.jsonl')]
v2 = {}
for r in recs:
    if 'error' in r and len(r) <= 4:
        continue
    v2[r['flow']] = r
r = v2['F08_doc_drift']
print("=== F08 CHANGED FIELDS PER KEY ===")
for k, v in r['changed_fields_per_key'].items():
    print(f"  {k!r}: {v}")
print("\n=== F08 SNAP DETAIL ===")
for key in ('g', 'v', 'b', 't', 'x', '1', '5', '[', ']', 'ArrowLeft', 'Delete', 'm', '?', 'r'):
    pv = (r.get('probes') or {}).get(key)
    if not pv:
        continue
    b, a = pv.get('before', {}), pv.get('after', {})
    interesting = {kk: (b.get(kk), a.get(kk)) for kk in ('grid', 'sel', 'n', 'body', 'terrainMode', 'brush', 'activeBrush', 'view2d', 'objX')}
    print(f"  {key!r}: {json.dumps(interesting, default=str)[:400]}")
print("\n=== F15 ===")
r = v2['F15_tab_trap']
print("focus_seq_first8:", r['focus_seq_first8'])
print("focus_after_escape:", r['focus_after_escape'])
print("OUT-count:", r['tab_escape_modal_to_background_count'])
print("tab_seq_full:", r.get('tab_seq_full'))
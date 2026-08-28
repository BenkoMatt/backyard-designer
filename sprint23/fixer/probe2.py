"""Retry probe with retries + longer timeout; then compare serving content vs disk."""
import urllib.request, hashlib, time, os

disk = open('/root/backyard-designer/index.html', 'rb').read()
for attempt in range(3):
    try:
        req = urllib.request.Request('http://127.0.0.1:8304/index.html', headers={'Connection': 'close'})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
        print(f'attempt {attempt}: {len(data)} bytes, match_disk={hashlib.md5(data).hexdigest() == hashlib.md5(disk).hexdigest()}, V01={"S23-V01".encode() in data}')
        break
    except Exception as e:
        print(f'attempt {attempt}: {type(e).__name__}: {e}')
        time.sleep(2)
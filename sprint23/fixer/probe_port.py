"""Probe port 8304: is it serving? Does content match the current index.html?"""
import urllib.request, hashlib, os

for port in (8304,):
    try:
        with urllib.request.urlopen(f'http://localhost:{port}/index.html', timeout=5) as r:
            data = r.read()
        disk = open('/root/backyard-designer/index.html', 'rb').read()
        print(f'port {port}: HTTP OK, {len(data)} bytes, match_disk={hashlib.md5(data).hexdigest() == hashlib.md5(disk).hexdigest()}, S23-V01={"S23-V01".encode() in data}')
    except Exception as e:
        print(f'port {port}: FAIL {type(e).__name__}: {e}')
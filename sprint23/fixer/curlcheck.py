"""Fetch with curl exactly (no python decode games), diff vs disk, byte counts + hash.
Also serve on a FRESH port and compare to rule out stale http.server caches."""
import subprocess, hashlib

r = subprocess.run(['curl', '-s', 'http://127.0.0.1:8304/index.html', '-o', '/tmp/served.html'], capture_output=True)
print('curl rc:', r.returncode)
disk = open('/root/backyard-designer/index.html', 'rb').read()
served = open('/tmp/served.html', 'rb').read()
print('disk:', len(disk), 'served:', len(served), 'equal:', disk == served)
print('disk md5:', hashlib.md5(disk).hexdigest())
print('served md5:', hashlib.md5(served).hexdigest())

# fresh server on 8306
srv = subprocess.Popen(['python3', '-m', 'http.server', '8306', '--bind', '127.0.0.1'],
                       cwd='/root/backyard-designer', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
import time, urllib.request
time.sleep(1)
try:
    fresh = urllib.request.urlopen('http://127.0.0.1:8306/index.html', timeout=10).read()
    print('fresh-8306 bytes:', len(fresh), 'equal to disk:', fresh == disk)
finally:
    srv.terminate()
    srv.wait(timeout=5)
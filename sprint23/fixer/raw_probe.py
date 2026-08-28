"""Raw TCP probe of 8304 to see what protocol it actually speaks."""
import socket

s = socket.create_connection(('localhost', 8304), timeout=5)
s.sendall(b'GET /index.html HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
chunks = []
try:
    while True:
        c = s.recv(65536)
        if not c:
            break
        chunks.append(c)
        if sum(len(c) for c in chunks) > 200000:
            break
except socket.timeout:
    pass
data = b''.join(chunks)
print('total bytes:', len(data))
print('first 300:', data[:300])
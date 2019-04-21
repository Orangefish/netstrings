#fileencoding=utf-8
#!/usr/bin/env python3
"""
Client for echo server.
"""

import socket
import os #for PID
import time

SERVER_ADDR = '127.0.0.1'
SERVER_TCP_PORT = 9000 
BUFFER_SIZE = 1024
CLIENT_WAIT = 2
CLIENT_REQ_NUM = 10

if __name__ == '__main__':
    PID = os.getpid()
    print('Client PID: {}'.format(PID))
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.connect((SERVER_ADDR, SERVER_TCP_PORT))

    # (host, port)
    local_addr = client_sock.getsockname()
    remote_addr = client_sock.getpeername()
    print('Connection  {}:{} --> {}:{}'.format(
                    local_addr[0], local_addr[1],
                    remote_addr[0], remote_addr[1])
                    )
    for i in range(1, CLIENT_REQ_NUM+1):
        req = 'Test! From:{}, PID:{}, {}/{}'.format(local_addr, PID, i, CLIENT_REQ_NUM)
        req = bytes(req, 'utf8')
        print('req:')
        print('{!r}'.format(req))
        client_sock.send(req)
        resp = client_sock.recv(BUFFER_SIZE)
        print('resp:')
        print('{!r}'.format(resp))
        print('req == res:', req == resp)
        time.sleep(CLIENT_WAIT)
    # leave it open for REPL
    #client_sock.close()

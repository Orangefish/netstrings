#fileencoding=utf-8
#!/usr/bin/env python3
"""
Client for echo server.
"""

import socket
import os #for PID
import time
import json

import netstrings as ns


SERVER_ADDR = '127.0.0.1'
SERVER_TCP_PORT = 9000 
BUFFER_SIZE = 1024
MAX_BACKLOG = 5
CLIENT_WAIT = 1
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
    # default NsStream, pack/unpack: pack_str/unpack_str
    nstream = ns.NsStream(client_sock)    
    for i in range(1, CLIENT_REQ_NUM+1):
        req = 'Test! From:{}, PID:{}, {}/{}'.format(local_addr, PID, i, CLIENT_REQ_NUM)
        print('req:', '(len:{})'.format(len(req)))
        print('{!r}'.format(req))
        nstream.write(req)
        resp  = nstream.read()
        if resp is not None:
            print('resp:', '(len:{})'.format(len(resp)))
            print('{!r}'.format(resp))
            print('req == res:', req == resp)
        time.sleep(CLIENT_WAIT)

    # JSON example 
    req = {'A':1, 'B':2, 'C':[3,4,5]}
    print('req: {!r}'.format(req))
    nstream.write(json.dumps(req))
    resp = json.loads(nstream.read())  
    print('resp: {!r}'.format(resp))
    print('req == res:', req == resp)
    # leave it open for REPL
    #client_sock.close()

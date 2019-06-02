#fileencoding=utf-8
#!/usr/bin/env python3
"""
Client for sending pickled object over nsetstring.

python client_pickle_ns.py
"""

import socket
import time
import netstrings as ns
import pickle
# pack and unpack defined in server file
from server_pickle_ns import make_pickle_packer, make_pickle_unpacker

SERVER_ADDR = '127.0.0.1'
SERVER_TCP_PORT = 9000 

if __name__ == '__main__':
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.connect((SERVER_ADDR, SERVER_TCP_PORT))
    # (host, port)
    local_addr = client_sock.getsockname()
    remote_addr = client_sock.getpeername()
    print('Connection  {}:{} --> {}:{}'.format(
                    local_addr[0], local_addr[1],
                    remote_addr[0], remote_addr[1])
                    )

    fd = client_sock.makefile('rwb', buffering=0)
    # NsStream wiht custom pack/unpack
    nstream = ns.NsStream(fd,
            pack_f=make_pickle_packer(),
            unpack_f=make_pickle_unpacker())    
    L = [1,2,3]
    D = {'A':1, 'B':None, 'C':True}
    S = set(['AAA', 'BBB', 'CCC', ('1', 2)])
    nstream.write(L)
    time.sleep(1)
    nstream.write(D)
    time.sleep(1)
    nstream.write(S)
    time.sleep(1)
    # leave it open for REPL
    #client_sock.close()

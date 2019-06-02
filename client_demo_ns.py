#fileencoding=utf-8
#!/usr/bin/env python3
"""
Demo Client for netstrings.
Must be used with echo server.
"""
# Example 1.
import socket
import netstrings as ns
SERVER_ADDR = '127.0.0.1'
SERVER_TCP_PORT = 9000 
client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_sock.connect((SERVER_ADDR, SERVER_TCP_PORT))
# Make file-like object form socket.
fd = client_sock.makefile('rwb', buffering=0)
nstream = ns.NsStream(fd)    
req = 'Hello world!'
nstream.write(req)
resp = nstream.read()
print('req == res:', req == resp)

# Example 2.
import json
req = {'A':1, 'B':2, 'C':[3,4,5]}
nstream.write(json.dumps(req))
resp = json.loads(nstream.read())  
print('req == res:', req == resp)


# Example 3.
import pickle
NS_PICKLE_MAX = 16384

def make_pickle_packer(max_len=NS_PICKLE_MAX):
    def pack_pickle(x):
        return ns.pack(pickle.dumps(x), max_len=max_len)
    return pack_pickle

def make_pickle_unpacker(max_len=NS_PICKLE_MAX):
    def unpack_pickle(x):
        (payload, tail) = ns.unpack(x, max_len=max_len)
        if payload is not None:
            payload_obj = pickle.loads(payload) 
            return (payload_obj, tail)
        else:
            return (None, x)
    return unpack_pickle


nstream = ns.NsStream(fd,
    pack_f=make_pickle_packer(),
    unpack_f=make_pickle_unpacker())    
req = {'A':1, 'B':None, 'C':3}
# now any picklable object can be transported over NsStream 
nstream.write(req)
resp = nstream.read()
print('req == res:', req == resp)

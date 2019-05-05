### Netstrings protocol implementation for Python 3

https://tools.ietf.org/html/draft-bernstein-netstrings-02

Netstrings definition (from draft-bernstein-netstrings-02):  

> Any string of 8-bit bytes may be encoded as [len]":"[string]",".
> Here [string] is the string and [len] is a nonempty sequence of ASCII
> digits giving the length of [string] in decimal. The ASCII digits are
> <30> for 0, <31> for 1, and so on up through <39> for 9. 
> ...

> For example, the string "hello world!" is encoded as <31 32 3a 68
> 65 6c 6c 6f 20 77 6f 72 6c 64 21 2c>, i.e., "12:hello world!,". The
> empty string is encoded as "0:,".


Package provides low-level functions for create and parse netstrings 
for Python's `bytes` and `str`:

```python
import netstrings as ns
>>> ns.pack(b'hello world!')
b'12:hello world!,'
>>> ns.unpack(b'12:hello world!,')
(b'hello world!', b'')
>>>
>>> ns.pack_str('Ж')
b'2:\xd0\x96,'
>>> ns.unpack_str(b'2:\xd0\x96,')
('Ж', b'')
>>>

```

And high-level API `NsStream`, whose instances wraps any file-like object 
(TCP socket/binary file/binary IO Stream) and has configurable packer/unpacker 
functions for any particular data.
`NsStream` uses `pack_str` and `unpack_str` as default packer/unpacker.  

(For full example see `client_demo_ns.py` this clients works with echo-server `server_echo_stream_delay.py`)  

Example 1.

```python
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
```    

Any type that can be serialized/deserialized to/from `str` works fine with defaults.  
  
Example 2. (continue of Ex. 1)  for JSON:  

```python
import json
req = {'A':1, 'B':2, 'C':[3,4,5]}
nstream.write(json.dumps(req))
resp = json.loads(nstream.read())  
print('req == res:', req == resp)
```

Example 3. (continue of Ex. 1,2)  for custom pickle packer/unpacker:  

```python
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
```

Additional examples for pickle in `server_pickle_ns.py` and `client_pickle_ns.py`  

### Some implementation details

-   Python 3.7 on Linux/Win10 is used for development/testing

-   It is assumed that TCP byte stream brings only contiguous netstrings  
    Valid bytestream: b'3:abc,3:123,'  
    Invalid bytestream: b'3:abc,J3:123,' the 'J' breaks it  
    In case if TCP byte stream brings uncontiguos netstrings then `NsMailformed`
    exception is raised.

-   Low-level unpack function accept netstrings with leading ASCII digits zeroes in len:  
    For example:   
        b'03:abc,'  
    But low-level pack function always produces netstrings without leading zeroes.    

-   Byte stream termination handled by `NsStreamUnexpectedEnd` exception.  
    For example:  
    The exception is raised when receiver gets b'3:ab' and TCP connection is closed or file/stream is corrupted.  

-  `NsMalformed` exception is raised when low-level functions called with malformed/corrupted
    netstrings or when length of netstrings exceed `max_len`  

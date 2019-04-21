### Netstrings protocol implementation.

https://tools.ietf.org/html/draft-bernstein-netstrings-02

Definition (from draft-bernstein-netstrings-02):  

> Any string of 8-bit bytes may be encoded as [len]":"[string]",".
> Here [string] is the string and [len] is a nonempty sequence of ASCII
> digits giving the length of [string] in decimal. The ASCII digits are
> <30> for 0, <31> for 1, and so on up through <39> for 9. Extra zeros
> at the front of [len] are prohibited: [len] begins with <30> exactly
> when [string] is empty.

> For example, the string "hello world!" is encoded as <31 32 3a 68
> 65 6c 6c 6f 20 77 6f 72 6c 64 21 2c>, i.e., "12:hello world!,". The
> empty string is encoded as "0:,".


Examples of netstrings in Python's bytes type notation:  

```
input   ->  resulting netstring 
b'123'  ->  b'3:123,' 
b''     ->  b'0:,'     
```


Example of code:

```python    
import netstrings as ns
client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_sock.connect((SERVER_ADDR, SERVER_TCP_PORT))
nstream = ns.NsStream(client_sock)    
req_str = 'Hello world!'
nstream.write(req)
resp_str = nstream.read()
```    

NsStream uses as default packer/unpacker pack_str and unpack_str functions for  
Pythons 3 str type( unicode string).  
Module has low-level pack/unpack functions that accepts bytes and produce  
netstrings. Using these two types packers/unpackers can cover many cases.  

JSON works fine with defaults.  
    
Example for JSON:

```python    
req = {'A':1, 'B':2, 'C':[3,4,5]}
nstream.write(json.dumps(req))
resp = json.loads(nstream.read())  
print('req == res:', req == resp)
```


Example of customs packer/unpacker for Pickle 

```python
import netstrings as ns
NS_PICKLE_MAX = 16384
def make_pickle_packer(max_len=NS_PICKLE_MAX):
    def pickle_packer(x):
        return ns.pack(pickle.dumps(x), max_len=max_len)
return pickle_packer

def make_pickle_unpacker(max_len=NS_PICKLE_MAX):
    def pickle_unpacker(x):
        (payload, tail) = ns.unpack(x, max_len=max_len)
        if payload is not None:
            payload_obj = pickle.loads(payload) 
            return (payload_obj, tail)
        else:
            return (None, x)
return pickle_unpacker

nstream = ns.NsStream(self.request,
    pack_f=make_pickle_packer(),
    unpack_f=make_pickle_unpacker())    
D = {'A':1, 'B':2, 'C':3}
# now any picklable object can be transported over NsStream 
nstream.write(D)
data = nstream.read()
```

### Some implementation details

-   Python 3.7 on Linux/Win10 is used for development/testing

-   It is assumed that TCP byte stream brings only contiguous netstrings  
    Valid bytestream: b'3:abc,3:123,'  
    Invalid bytestream: b'3:abc,J3:123,' the 'J' breaks it  
    In case if TCP byte stream brings uncontiguos netstrings  NsMaiformed
    exception is raised.

-   Low-level unpack function accept netstrings with leading ascii digits zeroes in len:  
    For example:   
        b'03:abc,'  
    But low-level pack function produces netstrings without leading zeroes.    

-   If TCP byte stream terminates unexpectedly, NsStream.read() raises
    exception.  
    For example:
        receiver got b'3:ab' and TCP connection was closed then
        NsStreamUnexpectedEnd is raised


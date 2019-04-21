#fileencoding=utf-8
#!/usr/bin/env python3

from functools import partial

# Default maximum full netstring len.
# ascii len digits  +  delemitter ':' + payload + terminator ','
# packer and unpacker function can redifine it see max_len
NS_MAX_LEN = 4096 

# Default size of bytes for NsStream read single read  
# it affect socket read operation in following way: 
# sock.recv(STREAM_MAX_READ), 
# NsStream constructor can redifine it see max_read
STREAM_MAX_READ = 8192 

def hex_fragment(ba):
    """HEX represenatation of bytes.

    Parameters
    ----------
    ba : bytes
        Bytes to be converted in HEX.

    Returns
    -------
    str
        String with HEX representaion of bytes.
    """
    return ' '.join(['{:02X}'.format(i) for i in ba])

class NsError(Exception):
    """
    Base Class for netstring Exceptions.
    """
    pass

class NsMaiformed(NsError):
    pass

class NsStreamUnexpectedEnd(NsError):
    pass

def pack(x, max_len=NS_MAX_LEN):
    """Packing bytes to netesring.

    Parameters
    ----------
    x : bytes
        Bytes to be packed.

    Returns
    -------
    bytes 
        Netstring represented as bytes.    

    >>> pack(b'abc')
    b'3:abc,'

    >>> pack(b'')
    b'0:,'

    >>> pack(b'123456789AB', max_len=10)
    Traceback (most recent call last):
    NsMaiformed: Too big netstring. len:15, max_len:10

    >>> unpack(pack(b'abc')) 
    (b'abc', b'')

    >>> unpack(pack(b'a:b:c')) 
    (b'a:b:c', b'')
    
    """
    ascii_dig_len = bytes(str(len(x)), 'utf8')
    total_len = len(ascii_dig_len) + len(x) + 2
    if  total_len > max_len:
            raise NsMaiformed('Too big netstring. len:{}, max_len:{}'.format(total_len, max_len))
    return ascii_dig_len + b':' + x + b','

def unpack(x, max_len=NS_MAX_LEN):
    """Unpacking netesring to bytes.

    Parameters
    ----------
    x : bytes
        Netstring represented as bytes.    

    Returns
    -------
    bytes 
        Bytes unpacked from netstring.    

    >>> unpack(b'3:abc,')
    (b'abc', b'')
    
    >>> unpack(b'0:,')
    (b'', b'')

    leading ascii didit zeroes is valid 
    >>> unpack(b'03:abc,')
    (b'abc', b'')

    >>> unpack(b'12:123456789ABC,', max_len=10)
    Traceback (most recent call last):
    NsMaiformed: Too big netstring. len:12, max_len:10

    >>> unpack(pack(b'abc')) 
    (b'abc', b'')

    >>> unpack(pack(b'a:b:c')) 
    (b'a:b:c', b'')

    case when not all bytes arrived yet
    >>> unpack(b'3:abc')
    (None, b'3:abc')

    >>> unpack(b'abc')
    Traceback (most recent call last):
    NsMaiformed: Not found semicolon ":" as delimiter bytes:b'abc' HEX:61 62 63

    >>> unpack(b'V:abc,')
    Traceback (most recent call last):
    NsMaiformed: Cannot parse as ascii digits. bytes:b'V:abc,' HEX:56 3A 61 62 63 2C

    """
    i =  x.find(b':')
    if i != -1:
        try:
            payload_l = int(x[0:i]); 
        except ValueError as e:
            raise NsMaiformed('Cannot parse as ascii digits. bytes:{} HEX:{}'.format( 
                            repr(x[0:8]),
                            hex_fragment(x[0:8])))
        if payload_l > max_len:
            raise NsMaiformed('Too big netstring. len:{}, max_len:{}'.format(payload_l, max_len))
        payload = x[i+1:i+1+payload_l]
        # also skip ',' 
        tail = x[i+2+payload_l:]
        # but check that ',' is present 
        if payload_l == len(payload) and x[i+1+payload_l:i+2+payload_l] == b',':  
            return (payload, tail)
        elif len(x) > max_len:
            raise NsMaiformed('Too big netstring. len:{}, max_len:{}'.format(len(x), max_len))
        else: 
            # not all bytes arrived yet
            return (None, x)
    elif len(x) == 0:            
            # not all bytes arrived yet
            return (None, x)
    elif len(x) < max_len and x.isdigit():
            # not all bytes arrived yet
            return (None, x)
    else:
        raise NsMaiformed('Not found semicolon ":" as delimiter. bytes:{} HEX:{}'.format( 
                    repr(x[0:8]), 
                    hex_fragment(x[0:8])))

def pack_str(x, errors='strict', max_len=NS_MAX_LEN):
    """Packing str to netesring.

    Parameters
    ----------
    x : str 
        str to be packed.
    errors: string
        The `errors` propogated to bytes() codec. Possible values:
        'strict' meaning that encoding errors raise a
        UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
        'xmlcharrefreplace' as well as any other name registered with
        codecs.register_error that can handle UnicodeEncodeErrors.

    Returns
    -------
    bytes 
        Netstring representation of str `x`.   

    >>> pack_str('abc')
    b'3:abc,'

    >>> pack_str('')
    b'0:,'

    >>> pack_str('Ж')
    b'2:\xd0\x96,'

    >>> unpack_str(pack_str('abc')) 
    ('abc', b'')

    """
    payload = bytes(x, encoding='utf8', errors=errors)
    return pack(payload, max_len=max_len)

def unpack_str(x, errors='strict', max_len=NS_MAX_LEN):
    """Unpacking netesring to str.

    Parameters
    ----------
    x : bytes 
        Netstring that contains some str.   
    errors : string
        The `errors` propogated to str() codec. Possible values:
        strict' meaning that decoding errors raise a
        UnicodeDecodeError. Other possible values are 'ignore' and 'replace'
        as well as any other name registered with codecs.register_error that
        can handle UnicodeDecodeErrors

    Returns
    -------
    str 
        string unpacked from netstring `x`.   

    >>> unpack_str(b'3:abc,')
    ('abc', b'')
    
    >>> unpack_str(b'0:,')
    ('', b'')

    Unicode symbol 'Ж'
    doctest does not run correctly: unpack_str(b'2:\xd0\x96,')
    SyntaxError: bytes can only contain ASCII literal characters.
    so i construct bytes object
    >>> unpack_str(b'2:' + 'Ж'.encode('utf8') + b',')
    ('Ж', b'')

    Half of Unicode symbol 'Ж' -- incorrect, so must be unpackable
    doctest does not run correctly: unpack_str(b'1:\x96,')
    SyntaxError: bytes can only contain ASCII literal characters.
    so i construct bytes object
    >>> unpack_str(b'1:' + 'Ж'.encode('utf8')[1:] + b',')
    Traceback (most recent call last):
    UnicodeDecodeError: 'utf-8' codec can't decode byte 0x96 in position 0: invalid start byte

    # it can be unpacked in case of ignore errors 
    >>> unpack_str(b'1:' + 'Ж'.encode('utf8')[1:] + b',', errors='ignore')
    ('', b'')

    >>> unpack_str(pack_str('a:b:c'))
    ('a:b:c', b'')

    >>> unpack_str(b'abc')
    Traceback (most recent call last):
    NsMaiformed: Not found semicolon ":" as delimiter bytes:b'abc' HEX:61 62 63
    
    """
    (payload, tail) = unpack(x, max_len=max_len)
    if payload is not None:
        payload_str = str(payload, encoding='utf8', errors=errors)
        return (payload_str, tail)
    else:
        return (None, x)

pack_str_strict = partial(pack_str, errors='strict', max_len=NS_MAX_LEN)
unpack_str_strict = partial(unpack_str, errors='strict', max_len=NS_MAX_LEN)

class NsStream:
    """
    Stream of netstring messages over TCP protocol. 

    Attributes
    ----------
    sock : socket 
        TCP socket, initialized by constructor.
    pack_f
        Packer function, initialized by constructor.
        It must be single argument function  
        that accepts any object and returns netstirng.  
    unpack_f
        Unpacker function, initialized by constructor.
        It must be single argument function  
        that accepts buff:bytes and returns tuple: 
            - in case of success (any_object, rest_of_buff_bytes) 
            - in case of failure (None, buff) 
    max_read : int
        Default size of bytes for NsStream single read operation from socket, 
        is initialized by constructor.
    buff : bytes
        Internal buffer to store intermediate byres that already was received
        from `sock` but not yet processed.

    Methods
    -------
    write(pyload) 
        Converts payload to netstring using `pack_f` and sends over TCP.
    read()
        Parse internall buffer as netstring, unpack it using `unpack_f` and returns to
        caller.
    __iter__()
        Python's Iterator protocol support.
    __next__()
        Python's Iterator protocol support.

    """
    def __init__(self, sock, max_read=STREAM_MAX_READ, pack_f=pack_str_strict, unpack_f=unpack_str_strict):
        self.sock = sock
        self.pack_f = pack_f
        self.unpack_f = unpack_f
        self.max_read = max_read 
        self.buff = b''
        self.closed_rx = False
        self.processed_rx = False

    def write(self, payload):
        """Converts payload to netstring and it sends over TCP.

        Blocking call.
        Pack data to netstring, using configurable packer, `pack_f`.
        Sends netstring over TCP socket.

        Parameters
        ----------
        payload 
            Object to be packed.
    
        """
        return self.sock.sendall(self.pack_f(payload))

    def read(self):
        """Parse internall buffer as netstring, unpack it and returns to
        caller.

        Blocking call.
        Fill in internal buffer from TCP for up to `max_read` bytes.

        Parameters
        ----------

        Returns
        -------
        None 
            Underlying TCP connection is closed in rx direction and internal buffer is empty.
        Any object
            The result of parsing netstring and unpacking it by `unpack_f`. 
            
        """
        if not self.processed_rx:
            (payload, tail) = self.unpack_f(self.buff)
            if payload is not None:
                self.buff = tail
                return payload
            elif not self.closed_rx:
                # not all bytes arrived yet
                while not self.closed_rx:
                    raw_b = self.sock.recv(self.max_read)
                    # was closed
                    if raw_b == b'':
                        self.closed_rx = True
                    self.buff += raw_b
                    (payload, tail) = self.unpack_f(self.buff)
                    if payload is not None:
                        self.buff = tail
                        return payload
            # we reach this point 
            # if we cannot parse buff
            # and closed_rx 
            if self.buff == b'':
                self.processed_rx = True
                return None
            else: 
                raise NsStreamUnexpectedEnd('Uexpected end of byte stream. bytes:{} HEX:{}'.format(
                            repr(self.buff[0:8]),
                                hex_fragment(self.buff[0:8])))
        else:
            return None

    def __iter__(self):
        return self
    
    def __next__(self):
        consumed = False
        while not consumed:
            res = self.read()  
            if res is not None:
                return res 
            else:
                consumed = True
        raise StopIteration

if __name__ == '__main__':
    import doctest
    doctest.testmod()

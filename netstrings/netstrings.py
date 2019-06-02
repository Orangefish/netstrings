#fileencoding=utf-8
#!/usr/bin/env python3

from functools import partial
from io import BytesIO

# Default maximum assembled netstring len.
# ascii len digits  +  delemitter ':' + payload + terminator ','
# packer and unpacker function can redifine it see max_len
NS_MAX_LEN = 4096 

# Default size of bytes for NsStream single read operation 
# fd.read(STREAM_MAX_READ), 
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

class NsMalformed(NsError):
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
    NsMalformed: Too big netstring. len:15, max_len:10

    >>> unpack(pack(b'abc')) 
    (b'abc', b'')

    >>> unpack(pack(b'a:b:c')) 
    (b'a:b:c', b'')
    
    """
    ascii_dig_len = bytes(str(len(x)), 'utf8')
    total_len = len(ascii_dig_len) + len(x) + 2
    if  total_len > max_len:
            raise NsMalformed('Too big netstring. len:{}, max_len:{}'.format(total_len, max_len))
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
    NsMalformed: Too big netstring. len:12, max_len:10

    >>> unpack(pack(b'abc')) 
    (b'abc', b'')

    >>> unpack(pack(b'a:b:c')) 
    (b'a:b:c', b'')

    case when not all bytes arrived yet
    >>> unpack(b'3:abc')
    (None, b'3:abc')

    >>> unpack(b'abc')
    Traceback (most recent call last):
    NsMalformed: Not found semicolon ":" as delimiter. Buffer fragment (at begin):b'abc' HEX:61 62 63

    >>> unpack(b'V:abc,')
    Traceback (most recent call last):
    NsMalformed: Cannot parse ASCII digits giving the length of netstring. Buffer fragment (at begin):b'V:abc,' HEX:56 3A 61 62 63 2C

    >>> unpack(b'3:abcd,')
    Traceback (most recent call last):
    NsMalformed: Not found comma "," as delimiter. Buffer fragment (at begin):b'3:abcd,' HEX:33 3A 61 62 63 64 2C

    """
    i =  x.find(b':')
    if i != -1:
        try:
            payload_l = int(x[0:i]); 
        except ValueError as e:
            raise NsMalformed('Cannot parse ASCII digits giving the length of netstring. Buffer fragment (at begin):{} HEX:{}'.format( 
                            repr(x[0:8]),
                            hex_fragment(x[0:8])))
        if payload_l > max_len:
            raise NsMalformed('Too big netstring. len:{}, max_len:{}'.format(payload_l, max_len))
        # payload always <=  payload_l
        # because slice
        payload = x[i+1:i+1+payload_l]
        # also skip ',' 
        tail = x[i+2+payload_l:]
        # but check that ',' is present 
        comma = x[i+1+payload_l:i+2+payload_l]
        if payload_l == len(payload) and comma == b',':  
            return (payload, tail)
        elif payload_l == len(payload) and len(comma) == 1 and comma != b',':
            raise NsMalformed('Not found comma "," as delimiter. Buffer fragment (at begin):{} HEX:{}'.format(
                            repr(x[0:8]),
                            hex_fragment(x[0:8])))
        else: 
            # we here if not all bytes arrived yet
            #   len(payload) < payload_l
            #   or 
            #   payload_l == len(payload) and comma == b'' (comma not arrived)
            return (None, x)
    else:
        if len(x) == 0 or (len(x) <= max_len and x.isdigit()):
            # not all bytes arrived yet
            return (None, x)
        else:
            raise NsMalformed('Not found semicolon ":" as delimiter. Buffer fragment (at begin):{} HEX:{}'.format( 
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
    NsMalformed: Not found semicolon ":" as delimiter. Buffer fragment (at begin):b'abc' HEX:61 62 63
    
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
    fd : file-like object in binary mode
        opened file in binary mode: open()
        io Stream: io.BytesIO()
        file-like object form opened TCP socket: sosk.makefile('rwb', buffering=0) 
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
        Default size of bytes for NsStream single read operation from `fd`, 
        is initialized by constructor.
    buff : bytes
        Internal buffer to store intermediate bytes that already was 
        readed/received from `fd` but not processed yet.

    Methods
    -------
    write(pyload) 
        Converts payload to netstring using `pack_f` and writes it to file-like
        objet `fd`.
    read()
        Reads data form file-like object `fd` into internal buffer, parses it as netstring, 
        unpacks it using `unpack_f` and returns to caller.
    __iter__()
        Python's Iterator protocol support.
    __next__()
        Python's Iterator protocol support.

    Basic test
    >>> b_stream = BytesIO()
    >>> ns_stream = NsStream(b_stream)
    >>> req = 'Ж'*100
    >>> req_ns_len = len(pack_str(req)) 
    >>> wr_len = ns_stream.write(req)
    >>> req_ns_len == wr_len
    True
    >>> b_stream.seek(0)
    0
    >>> resp = ns_stream.read() 
    >>> req == resp
    True

    Exception test: NsStreamUnexpectedEnd
    >>> b_stream = BytesIO()
    >>> ns_stream = NsStream(b_stream)
    >>> req = 'Ж'*100
    >>> req_ns_len = len(pack_str(req)) 
    >>> wr_len = ns_stream.write(req)
    >>> req_ns_len == wr_len
    True
    >>> b_stream.seek(0)
    0
    >>> new_wr_len = b_stream.truncate(50)
    >>> resp = ns_stream.read() 
    Traceback (most recent call last):
    NsStreamUnexpectedEnd: Unexpected end of byte stream. Buffer fragment (at begin):b'200:\xd0\x96\xd0\x96' HEX:32 30 30 3A D0 96 D0 96

    """
    def __init__(self, fd, max_read=STREAM_MAX_READ, pack_f=pack_str_strict, unpack_f=unpack_str_strict):
        self.fd = fd 
        self.pack_f = pack_f
        self.unpack_f = unpack_f
        self.max_read = max_read 
        self.buff = b''
        self.eof = False
        self.buff_processed = False

    def write(self, payload):
        """Converts payload to netstring using `pack_f` and write it to file-like
        objet `fd`.

        Blocking call.
        Pack data to netstring, using configurable packer, `pack_f`.
        Writes netstring to file-like obhect `fd`.

        Parameters
        ----------
        payload 
            Object to be packed.
    
        """
        return self.fd.write(self.pack_f(payload))

    def read(self):
        """Reads data form file-like object `fd` into internal buffer, parses it as netstring, 
        unpacks it using `unpack_f` and returns to caller.

        Blocking call.
        Fills in internal buffer from `fd` for up to `max_read` bytes.

        Parameters
        ----------

        Returns
        -------
        None 
            Underlying `fd` object reach EOF or when remote socket is closed and internal buffer is empty.
        Any object
            The result of parsing netstring and unpacking it by `unpack_f`. 
            
        """
        if not self.buff_processed:
            (payload, tail) = self.unpack_f(self.buff)
            if payload is not None:
                self.buff = tail
                return payload
            elif not self.eof:
                # not all bytes arrived yet
                while not self.eof:
                    raw_b = self.fd.read(self.max_read)
                    # socket was closed
                    # file or stream  reach EOF
                    if raw_b == b'':
                        self.eof = True
                    self.buff += raw_b
                    (payload, tail) = self.unpack_f(self.buff)
                    if payload is not None:
                        self.buff = tail
                        return payload
            # we reach this point 
            # if we cannot parse buff
            # and eof 
            if self.buff == b'':
                self.buff_processed = True
                return None
            else: 
                raise NsStreamUnexpectedEnd('Unexpected end of byte stream. Buffer fragment (at begin):{} HEX:{}'.format(
                            repr(self.buff[0:8]),
                                hex_fragment(self.buff[0:8])))
        else:
            return None

    def __iter__(self):
        # This breaks best practice regarding
        # distinct iterators over iterable.
        # But it is not possible/very hard to have distinct iterators over
        # near infinite sequence (TCP stream/file much bigger than memory).
        # So we have only one global itaration context over given NsStream.
        return self
    
    def __next__(self):
        # iterator is iterable
        res = self.read()  
        if res is not None:
            return res 
        else:
            raise StopIteration

if __name__ == '__main__':
    import doctest
    doctest.testmod()

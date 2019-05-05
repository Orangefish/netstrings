#fileencoding=utf-8
#!/usr/bin/env python3

"""
Netstrings protocol implementation.
https://tools.ietf.org/html/draft-bernstein-netstrings-02

Netstrings definition (from draft-bernstein-netstrings-02):

    > Any string of 8-bit bytes may be encoded as [len]":"[string]",". Here
    > [string] is the string and [len] is a nonempty sequence of ASCII digits
    > giving the length of [string] in decimal. The ASCII digits are <30> for 0,
    > <31> for 1, and so on up through <39> for 9. ...

    > For example, the string "hello world!" is encoded as <31 32 3a 68 65 6c 6c
    > 6f 20 77 6f 72 6c 64 21 2c>, i.e., "12:hello world!,". The empty string is
    > encoded as "0:,".

Package provides low-level functions for create and parse netstrings from/to
bytes, and high level API NsStream

See help for: NsStream, pack, unpack, pack_str, unpack_str defined in this module.
"""

from .netstrings import pack, unpack, pack_str, unpack_str
from .netstrings import NsStream, NsError, NsMalformed, NsStreamUnexpectedEnd  

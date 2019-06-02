#fileencoding=utf-8
#!/usr/bin/env python3
"""
Multithread server for receive 
pickled objects over netstrings.
Prints received object to console.

python server_pickle_ns.py 
"""
import socketserver
import socket 
from threading import Thread
from queue import Queue 
import pickle
import sys

import netstrings as ns

SERVER_ADDR = '127.0.0.1'
SERVER_TCP_PORT = 9000 
MAX_BACKLOG = 5
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

# Printer thread
def printer(printerQ):
    while True:
        # blocked until some string is arrived
        s = printerQ.get()
        print(s)

class TCPRequestHandler(socketserver.BaseRequestHandler):
    """
    The RequestHandler class for server.

    """
    def __init__(self, params, *args, **kwargs):
        self.printerQ = params[0] 
        socketserver.BaseRequestHandler.__init__(self, *args, **kwargs)

    def handle(self):
        self.printerQ.put('Accepted conection from {}:{}'.format(
                self.client_address[0],
                self.client_address[1]))
        # self.request is the TCP socket connected to the client
        # make file-like object
        nstream = ns.NsStream(self.request.makefile('rwb', buffering=0),
            pack_f=make_pickle_packer(),
            unpack_f=make_pickle_unpacker())    
        try:
            for data in nstream:
                self.printerQ.put('req from {}:{}\n  {!r}'.format(
                    self.client_address[0], 
                    self.client_address[1], 
                    data))
        except (ns.NsMalformed, ns.NsStreamUnexpectedEnd) as e:
            raise e
    

def make_handler(params):
    def TCPRequestHandlerParams(*args, **kwargs):
        return TCPRequestHandler(params, *args, **kwargs)
    return TCPRequestHandlerParams

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == '__main__':
    print('Starting ...<Ctrl-C> to stop.')
    # Printer Thread
    printerQ = Queue()
    printer_thread = Thread(
        target=printer,
        args=(printerQ, )
        )
    printer_thread.daemon = True
    printer_thread.start()

    # ThreadedTCPServer.allow_reuse_address = True
    # sets flag SO_REUSEADDR for server socket BEFORE binding
    #
    # The SO_REUSEADDR flag tells the kernel to reuse a local socket in
    # TIME_WAIT state, without waiting for its natural timeout to expire. 
    # 
    # without this flag got folliwing error when restert server and some sockets still
    # not closed:
    # [Errno 98] Address already in use 
    ThreadedTCPServer.allow_reuse_address = True
    server = ThreadedTCPServer((SERVER_ADDR, SERVER_TCP_PORT),
                    make_handler((printerQ,)))
    # Serever thread is daemon
    server.daemon = True
    # Threads that will sereve request also deamons.
    # main thread does not wait untill deamont-thread terminated 
    # this gives chance for main thread to process KeyboardInterrupt 
    server.daemon_threads = True
    local_addr = server.socket.getsockname()
    print('Listening on {}:{}'.format(local_addr[0], local_addr[1]))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print ('Stopping ...')
        sys.exit(1)

#fileencoding=utf-8
#!/usr/bin/env python3
"""
Multithread Echo protocol server, with ability to add delays to byte stream.

python echo_thread_stream_delay.py max_delay

max_delay -- seconds, server will use [0 .. delay_max] inteval for random delays
       if this parametr is 0 server will not perform delays for streams.
"""

import socket
from threading import Thread, Event
import time
import random
import sys
from queue import Queue 

SERVER_ADDR = '127.0.0.1'
SERVER_TCP_PORT = 9000 
BUFFER_SIZE = 8192
MAX_BACKLOG = 32

# Printer thread
def printer(printerQ):
    while True:
        # blocked until some string is arrived
        s = printerQ.get()
        print(s)

def process_client_connection(client_sock, max_delay, printerQ):
    while True:
        req = client_sock.recv(BUFFER_SIZE)
        if req == b'':
            break
        else:
            remote_addr = client_sock.getpeername()
            printerQ.put('req from {}:{} (len:{})\n  {!r}'.format(
                    remote_addr[0], 
                    remote_addr[1], 
                    len(req), 
                    req))
            if max_delay == 0: 
                # replay
                client_sock.send(req)
            else:
                # or split req to 2 part  and replay with delay
                req1 = req[0:len(req)%2]; req2=req[len(req)%2:];
                client_sock.send(req1)
                time.sleep(random.randint(0, max_delay))
                client_sock.send(req2)
    client_sock.close()

# separate thread for server 
# blocking calls are moved to his thread 
# this gives chance for main thread to process KeyboardInterrupt 
def server(server_sock, server_stop_event, max_delay, printerQ):
    while not server_stop_event.is_set():
        client_sock, client_addr = server_sock.accept()
        printerQ.put('Accepted conection from {}:{}'.format(client_addr[0], client_addr[1]))
        client_thread = Thread(
            target=process_client_connection,
            args=(client_sock, max_delay, printerQ)
            )
        # The entire Python programs (main thread) exits
        # only if no no-deamon thread left 
        # The program can exit witout waitiong for 
        # temination of all client_threads
        client_thread.deamon = True
        client_thread.start()


if __name__ == '__main__':
    print('Starting ...<Ctrl-C> to stop.')
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    else:
        max_delay = int(sys.argv[1])
        if  max_delay < 0 :
            print(__doc__)
            sys.exit(1)
    # Printer Thread
    printerQ = Queue()
    printer_thread = Thread(
        target=printer,
        args=(printerQ, )
        )
    printer_thread.daemon = True
    printer_thread.start()

    # Preparing server Socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((SERVER_ADDR, SERVER_TCP_PORT))
    server_sock.listen(MAX_BACKLOG)
    local_addr = server_sock.getsockname()
    print('Listening on {}:{}'.format(local_addr[0], local_addr[1]))
    server_stop_event = Event()
    # Starting server Thread
    server_thread = Thread(
        target=server,
        args=(server_sock, server_stop_event, max_delay, printerQ)
        )
    # The entire Python programs exits
    # only if no no-deamon thread left 
    # The main thread stops server-thread before exit 
    # but this is not helps, programs does not terminates and stuck 
    #
    # In [2]: server_thread.is_alive()
    # Out[2]: True
    #
    # Only with daemon = True option for 
    # server-thread programm can exit normally (Tested on Win10 Python 3.7.3)
    server_thread.daemon = True
    server_thread.start()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print ('Stopping ...')
        server_stop_event.set()
        sys.exit(1)



import socket
import select

sock1 = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
sock2 = socket.socket( socket.AF_INET, socket.SOCK_STREAM )

sock1.connect( ('192.168.1.1', 25) )
sock2.connect( ('192.168.1.1', 25) )

while 1:

    # Await a read event
    rlist, wlist, elist = select.select( [sock1, sock2], [], [], 5 )

    # Test for timeout
    if [rlist, wlist, elist] == [ [], [], [] ]:
        print "Five seconds elapsed.\n"

    else:
        # Loop through each socket in rlist, read and print the available data
        for sock in rlist:
            print sock.recv( 100 )


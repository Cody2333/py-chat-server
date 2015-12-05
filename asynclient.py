#-*-coding:utf-8-*-
import threading
import time
from socket import *

lCallback = {}
iFuncId = 0 



def StartListener():
    global iFuncId
    global lCallback
    HOST = ""
    PORT = 7800
    BUFSIZE = 1024
    ADDR = (HOST, PORT)
    tcpSerSock = socket(AF_INET, SOCK_STREAM)
    tcpSerSock.bind(ADDR)
    tcpSerSock.listen(5)
    print "Listener bind port %d ,starting ...." % PORT
    while 1:
        print 'waiting for connection ...'
        tcpCliSock, addr = tcpSerSock.accept()
        print '...connected from:',addr
        while 1:
            try:
                data = tcpCliSock.recv(BUFSIZE)
                if not data:
                    break
                print 'data = %s' % data
                i = data.find('[')
                j = data.find(']')
                if i!=-1 and j!=-1:
                    iFuncId = int(data[i+1:j])
                    message = data[j+1:].strip()
                    func = lCallback.get(iFuncId,None)
                    if func:
                        func(message)
                        del lCallback[iFuncId]
            except Exception,e:
                print e
                break
        tcpCliSock.close()
    tcpSerSock.close()


def onLogin(message):
    if message=='1':
        print 'login success'
    else:
        print 'login denied'


def Send(callback,message):
    global iFuncId
    global lCallback
    lCallback[iFuncId] = callback
    listenerSock = socket(AF_INET, SOCK_STREAM)
    listenerSock.connect(('localhost',5000))
    listenerSock.send('ssss')
    listenerSock.close()
    iFuncId += 1
    print 'send message to YoSQL : %s'%message

def DoSomeThing():
    print '......DoSomeThing......'
if __name__ == '__main__':

    DoSomeThing()
    DoSomeThing()
    Send(onLogin,"login")
    time.sleep(3)
    print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
#-*-coding:utf-8-*-
import threading
import time
from socket import *
import random

lCallback = {}
iFuncId = 1 
RECV_BUFFER = 1024 
PORT = 3316
HOST='localhost'

def dataHandler(data):
    print 'data = %s' % data
    i = data.find('[')
    j = data.find(']')
    if i!=-1 and j!=-1:
        sFuncId = data[i+1:j].strip()
        message = data[j+1:].strip()
    else:
        sFuncId='0'
        message='error'
    return sFuncId,message

def messageHandler(message):
    list=message.split('&')
    return list


def recvListener(socket):
    while 1:
        try:
            data = socket.recv(RECV_BUFFER)
            if not data:
                break

            iFuncId,message=dataHandler(data)
            iFuncId=int(iFuncId)
            func = lCallback.get(iFuncId,None)
            if func:
                func(message)
                del lCallback[iFuncId]
        except Exception,e:
            print e
            break        
        


def loginIn(message):
    if message == '1':
        print 'login success !!!!!!!!!!'
    else:
        print 'login failed !Please choose another name!'


def Send(callback,message,listenerSock):
    global iFuncId
    global lCallback
    lCallback[iFuncId] = callback
    time.sleep(0.1)
    listenerSock.send("[%d] %s" % (iFuncId,message))
    iFuncId += 1
    print 'send message to ChatServer : %s'%message
    
class ChatClient():
    def __init__(self):
        self.listenerSock = socket(AF_INET, SOCK_STREAM)
        self.listenerSock.connect((HOST,PORT))
        self.t = threading.Thread(target=recvListener,args=(self.listenerSock,))
        self.t.setDaemon(True)
        self.t.start()
    
    def loop(self):
        while 1:
            self.name=raw_input()
            if self.name.strip()=='':
                continue
            if self.name=='exit':
                break
            Send(loginIn,"login&"+self.name,self.listenerSock)    
if __name__ == '__main__':
    chatClient=ChatClient()
    chatClient.loop()

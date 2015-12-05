#-*-coding:utf-8-*-
from socket import *
import time
import select
import UserDict

#global variables
RECV_BUFFER = 1024 
PORT = 3316
HOST="0.0.0.0"
NAME="CodyChatServer"

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

    
def send(message,sock):
    sock.send(message)
    print 'send to listener: %s' % message    

class ChatMember():
    def __init__(self,name,sock):
        self.name=name
        self.sock=sock

class ChatServer():
    def __init__(self,port,name):
        self.cmdDict={}
        self.cmdDict['login']=self.doLogin
        self.CONNECTION_LIST=[]
        self.port=port
        self.host=''
        self.name=name
        self.userDict={}
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((self.host,self.port))
        self.server_socket.listen(5)
        
        self.CONNECTION_LIST.append(self.server_socket)
        print "Chat server %s started on port %d" %(self.name,self.port) 
        
    def createNewMember(self,name,sock):
        self.userDict[name]=sock

    def doLogin(self,cmdList,sock,funcId):
        if cmdList[1] not in self.userDict.keys():
            name=cmdList[1]
            send('[%s]1' %funcId,sock)
            self.createNewMember(name, sock)            
        else:
            send('[%s]0' %funcId,sock)
            
    def doTalkto(self,cmdList,sock,funcId):
        name=cmdList[1]
        content=cmdList[2]
        for key,value in self.userDict.items():
            if value==sock:
                sourceName=key
        if name not in self.userDict.keys():
            send('[%s]0' %funcId,sock)
        else:
            targetSock=self.userDict[name]
            try:
                send('[-1]sourceName&content',targetSock)
                send('[%s]1' %funcId,sock)
            except:
                send('[%s]-1' %funcId,sock)
                
    def doGetMemberList(self,cmdList,sock,funcId):
        msg='[%s]' %funcId
        for name in self.userDict.keys():
            msg=msg+name+'&'
        msg=msg.strip('&')
        send(msg, sock)

    def logout(self,sock,addr):
        print "Client (%s, %s) is offline" % addr
        sock.close()
        self.CONNECTION_LIST.remove(sock)
        for key,value in self.userDict.items():
            if value==sock:
                del self.userDict[key]
                print key,'deleted'

    def loop(self):
        while 1:
            self.read_sockets,self.write_sockets,self.error_sockets = select.select(self.CONNECTION_LIST,[],[])
     
            for sock in self.read_sockets:
                if sock == self.server_socket:
                    sockfd, addr = self.server_socket.accept()
                    send("welcome to %s" %self.name, sockfd)
                    self.CONNECTION_LIST.append(sockfd)
                    print "Client (%s, %s) connected" % addr
                                
                else:
                    try:
                        data = sock.recv(RECV_BUFFER)
                        if not data:
                            break
                        funcId,message=dataHandler(data)
                        if funcId!='0':
                            cmdList=messageHandler(message)
                            time.sleep(0.5)
                            try:
                                self.cmdDict.get(cmdList[0])(cmdList,sock,funcId)
                            except:
                                print 'command not match'    
                        else:
                            print 'cmd error'         
                     
                    except:
                        self.logout(sock, addr)
                        continue
         
        self.server_socket.close()    
if __name__ == '__main__':
        chatServer=ChatServer(PORT,NAME)
        chatServer.loop()
    
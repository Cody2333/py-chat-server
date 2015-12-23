#-*-coding:utf-8-*-
from socket import *
import time
import select
import UserDict
import os
#global variables
RECV_BUFFER = 1024 
PORT = 3316
HOST=""
NAME="CodyChatServer"
INTERVAL=0.1

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
    	if not os.path.exists('server'):
            os.mkdir('server')
        self.cmdDict={'login':self.doLogin,
                      'getmember':self.doGetMemberList,
                      'talkto':self.doTalkto,
                      'filename':self.doGetFileName,
                      'ready':self.doSendFile,
                      'file':self.doGetFile}
        self.CONNECTION_LIST=[]
        self.port=port
        self.host=''
        self.name=name
        self.userDict={}
        self.userDict['admin']=None
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((self.host,self.port))
        self.server_socket.listen(5)
        
        self.CONNECTION_LIST.append(self.server_socket)
        print "Chat server %s started on port %d" %(self.name,self.port) 
        
    def broadcast(self,sock,message):
        for socket in self.CONNECTION_LIST:
            if socket != self.server_socket and socket != sock :
                try :
                    socket.send(message)
                except :
                    socket.close()
                    self.CONNECTION_LIST.remove(socket)
        
    def createNewMember(self,name,sock):
        self.userDict[name]=sock
        self.broadcast(sock, '[-101]lalala')

    def doGetFile(self,cmdList,sock,funcId):
        content=cmdList[1]
        f=open('idk','w')
        f.writelines(content)
        
    def doLogin(self,cmdList,sock,funcId):
        if cmdList[1] not in self.userDict.keys():
            name=cmdList[1]
            send('[%s]1' %funcId,sock)
            self.createNewMember(name, sock)            
        else:
            send('[%s]0' %funcId,sock)
            
    def getSockByName(self,name):
        return self.userDict[name]
    
    def doTalkto(self,cmdList,sock,funcId):
        name=cmdList[1]
        content=cmdList[2]
        print '@@@'+name
        for key,value in self.userDict.items():
            if value==sock:
                sourceName=key
        if name not in self.userDict.keys():
            send('[%s]0' %funcId,sock)
        else:
            targetSock=self.getSockByName(name)
            try:
                send('[-102]%s&%s' %(sourceName,content),targetSock)
                send('[%s]1' %funcId,sock)
            except:
                send('[%s]-1' %funcId,sock)
                
    def doGetMemberList(self,cmdList,sock,funcId):
        #time.sleep(0.5)
        msg='[%s]' %funcId
        for name in self.userDict.keys():
            msg=msg+name+'&'
        msg=msg.strip('&')
        send(msg, sock)

    def doGetFileName(self,cmdList,sock,funcId):
        name=cmdList[1]
        print 'get file name %s' %cmdList[2]
        self.fileName=cmdList[2].strip()
        if self.fileName:
            #接收文件名成功
            message='[%s]1' %funcId
            send(message,sock)
            
            #接收文件成功之后，进行文件接收
            self.recvFile(self.fileName,sock)
            self.sendFile(name,self.fileName,sock)
        else:
            #接收文件名失败
            message='[%s]0' %funcId
            send(message, sock)
            
    def doSendFile(self,cmdList,sock,funcId):
        #send file
        print "server sending file to client   ~~~"
        filename=cmdList[1]
        msg='[%s]1' %funcId
        send(msg,sock)
        time.sleep(INTERVAL)
        try:
            f = open('server/'+filename, 'rb') 
            while True: 
                data = f.read(RECV_BUFFER) 
                if not data: 
                    break
                sock.sendall(data) 
            f.close() 
            time.sleep(INTERVAL)
    
            sock.sendall('EOF')
            print "send file success!"
        except:
            print "senf file failed!!"
            
    def sendFile(self,name,filename,sock):
        #先传输文件名,客户端响应，回调doSendFile函数
        targetSock=self.getSockByName(name)
        for key,value in self.userDict.items():
            if value==sock:
                sourceName=key        
        msg='[-104]%s&%s'%(filename,sourceName)
        send(msg,targetSock)
              
    def recvFile(self,filename,sock):
        #TODO
        #现在处理文件传输的方式是非异步的，服务器一次只能处理一个文件传输？
        print "starting revc file!"
        try:
            f = open('server/'+filename, 'wb') 
            while True:
                data = sock.recv(RECV_BUFFER) 
                if data == 'EOF': 
                    print "recv file success!"
                    break
                f.write(data) 
            f.close()
        except:
            print 'recv file failed'         
    
    def logout(self,sock,addr):
        print "Client (%s, %s) is offline" % addr
        sock.close()
        self.CONNECTION_LIST.remove(sock)
        for key,value in self.userDict.items():
            if value==sock:
                del self.userDict[key]
                print key,'deleted'
        self.broadcast(sock, '[-101]lalala')


    def loop(self):
        while 1:
            self.read_sockets,self.write_sockets,self.error_sockets = select.select(self.CONNECTION_LIST,[],[])
     
            for sock in self.read_sockets:
                if sock == self.server_socket:
                    sockfd, addr = self.server_socket.accept()
                    # send("welcome to %s" %self.name, sockfd)
                    self.CONNECTION_LIST.append(sockfd)
                    print "Client (%s, %s) connected" % addr
                                
                else:
                    try:
                        data = sock.recv(RECV_BUFFER)
                        if not data:
                            pass
                        else:
                            funcId,message=dataHandler(data)
                            if funcId!='0':
                                cmdList=messageHandler(message)
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
    
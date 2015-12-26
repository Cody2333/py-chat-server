#coding:utf-8
import socket
import threading
import sys
import time
import os

from PyQt4.QtGui import *  
from PyQt4.QtCore import * 

recvContent=''
lCallback = {}
iFuncId = 1 
RECV_BUFFER = 1024 
PORT = 3316
HOST='www.cody.wang'
INTERVAL=0.1
DIR_PREFIX='client/'

#两个工具函数，用于处理接收到的数据指令

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

#会话聊天主界面
class ChatWindow(QWidget):
    #fromUser:本机名字
    #toUser  :通信方名字
    def __init__(self,fromUser,toUser):
        super(ChatWindow, self).__init__()
        #init data
        self.fromUser=fromUser
        self.toUser=toUser
        self.listwindow=lw
        self.title='talking to %s .' %self.toUser
        chatDict.setdefault(toUser,'')
        #init gui
        self.initView(toUser)
        self.initLayout()
        self.createAction()

    def initView(self,toUser=''):
        self.setWindowTitle(self.title)
        self.layout = QGridLayout(self)
        self.btnSend = QPushButton('send')
        self.file=QPushButton("File")
        self.input = QLineEdit()
        self.name = QLineEdit('Default')
        self.chatText = QTextEdit()
        self.chatText.setReadOnly(True)
        self.chatText.setText(chatDict[toUser])
        self.timer = QTimer()
                        
    def initLayout(self):
        self.layout.addWidget(self.chatText, 0, 0, 5, 4)
        self.layout.addWidget(self.input, 5, 0, 1, 4)
        self.layout.addWidget(self.btnSend, 6, 0)
        self.layout.addWidget(self.file, 5,4)

    def createAction(self):
        self.btnSend.clicked.connect(self.sendMsg)
        self.file.clicked.connect(self.getFileName)
        
        
    #响应window关闭事件
    def closeEvent(self, event):
        self.listwindow.cwDict.pop(self.toUser)
        event.accept()
        
    #响应客户端gui的文件选择操作，发送给服务器文件名
    def getFileName(self):
        self.fileDir=QFileDialog.getOpenFileName(self,"Open file dialog","/","All files (*)")
        print self.fileDir
        self.fileName=self.fileDir.split('/')[-1]
        print self.fileName
        #self.input.setText(self.fileDir)
        try:
            data='filename&%s&%s' %(self.toUser,self.fileName)
            #回调函数为onReadyForSend
            self.listwindow.Send(self.onReadyForSend,data)
            self.listwindow.appendChatDict(self.toUser, "send file:"+self.fileName)
        except:
            QMessageBox.warning(  
                    self, 'Error', 'send file failed---')   
    
        
 
    def onReadyForSend(self,message):
        if message=='1':
            time.sleep(INTERVAL)
            #服务器已经收到文件信息，打开相应文件发送到服务器
            print 'send filename success'
            self.sendFile()         
        else:
            print 'send filename failed'

            self.listwindow.appendChatDict(self.toUser, 'send file failed')
            QMessageBox.warning(  
                    self, 'Error', 'send file failed')

    #点击发送信息执行的函数
    def sendMsg(self):
        text = str(self.input.text())
        self.input.setText('')
        if text.strip() == '':
            return
        try:
            data='talkto&%s&%s' %(self.toUser,text)
            print data
            self.listwindow.Send(self.onSendMsg, data)
            self.listwindow.appendChatDict(self.toUser, text,self.fromUser)
        except:
            QMessageBox.warning(  
                    self, 'Error', 'send message failed--- ')   

    #发送信息的回调函数
    def onSendMsg(self,message):
        if message=='1':
            print 'send message success--'
        else:
            print 'send message failed --'
            QMessageBox.warning(  
                    self, 'Error', 'send message failed -')

 
    def sendFile(self):
        #send file
        print "server ready, now client sending file~~"
        self.listwindow.appendChatDict(self.toUser, 'sending file ~~')
        try:
            f = open(self.fileDir, 'rb') 
            time.sleep(INTERVAL)
            while True:  
                data = f.read(RECV_BUFFER) 
                if not data: 
                    break
                s.sendall(data) 
            f.close() 
            time.sleep(INTERVAL)
            s.sendall('EOF') 
            print "send file success!"  
            self.listwindow.appendChatDict(self.toUser, 'send file success ~~')
        except:
            self.listwindow.appendChatDict(self.toUser, 'send file failed !!')            
            print 'sending file failed!!!'
                
class ListWindow(QMainWindow):
    global accountName
    def __init__(self):
        super(ListWindow, self).__init__()
        #init data
        #flag 用于控制recvListener线程的启动与暂停，现在接收线程是阻塞的，接收文件时无法接收其他信息。
        self.flag= 1
        self.cwDict={}
        
        #init view and layout
        self.initView()
        self.initLayout()
        
        #初始化信号和槽的关系
        self.createAction() 
        
        #响应服务器的请求function的字典format---->key<int>:value<function>
        self.resActionDict={-101:self.updateList,
                            -102:self.getMessage,
                            -104:self.readyForRecvFile}
        
        #开启接收数据的监听线程
        recvThread = threading.Thread(target=self.recvListener,args=(s,))
        recvThread.setDaemon(True)
        recvThread.start()
    
        
    def initView(self):
        self.setGeometry(100, 100, 250, 550)
        self.setWindowTitle(accountName)
        self.timer=QTimer()
        self.lists=QListWidget()
        self.quit = QPushButton("Quit")
        self.refresh=QPushButton("refresh")

    def initLayout(self):
        vLayout = QVBoxLayout()
        vLayout.addWidget(self.lists)
        vLayout.addWidget(self.quit)
        vLayout.addWidget(self.refresh)
        widget = QWidget()
        widget.setLayout(vLayout)
        self.setCentralWidget(widget)
        
    def createAction(self):
        self.updateList()
        self.quit.clicked.connect(self.exit)
        self.refresh.clicked.connect(self.updateList)
        self.lists.itemDoubleClicked.connect(self.onItemDoubleClicked)
    
    def closeEvent(self, event):
        self.cwDict={}
        s.close()
        event.accept()
        print 'close'

    def exit(self):
        self.cwDict={}
        s.close()
        print 'exit'
        sys.exit()

    #双击 user name 与该 user 进行交谈，打开chat window
    def onItemDoubleClicked(self,item):
        global accountName
        item.setTextColor(QColor(0,0,0))  
        toUser=str(item.text())
        self.openChatWindow(accountName,toUser)
        
    def recvFile(self,message):
        self.flag=0
        print "starting revc file!!!"
        print self.recvsourceName
        print self.recvfilename

        self.appendChatDict(self.recvsourceName, 'send a file to you, receiving~~',self.recvsourceName)
        f = open(DIR_PREFIX+accountName+'/'+self.recvfilename, 'wb') 
        while True: 
            data = s.recv(RECV_BUFFER) 
            if data == 'EOF': 
                print "recv file success!"
                self.flag=1
                break
            f.write(data) 
        f.close() 
        self.appendChatDict(self.recvsourceName, "recv file '%s' successfully" %self.recvfilename )

    '''用于改变chatDict的工具函数
        args:name     --->   chatDict的key
             content  --->   显示的内容
             showName --->   显示的发送者[可选]
    '''
    def appendChatDict(self,name,content,showName='>>>>>'):
        if showName:
            chatDict.setdefault(name,"")
            chatDict[name]+=showName+' : '+content+'\r\n'
            isUnread=self.setUnread(name)
                        
        #如果会话窗口存在，刷新会话窗口
        if not isUnread:
            self.cwDict[name].chatText.append(showName+":"+content)
            
    def readyForRecvFile(self,message):
        l=messageHandler(message)
        self.recvfilename=l[0]
        self.recvsourceName=l[1]
        self.Send(self.recvFile, 'ready&%s' %self.recvfilename)

        
    #更新在线成员列表
    def updateList(self,message=''):          
        global accountName
        self.Send(self.onGetMemberList,'getmember&%s' %accountName)
    
    #如果不存在和user的会话窗口那么将user设置为未读。
    def setUnread(self,user):
        #改变listWidget的对应item的外观
        c=self.lists.count()
        i=0
        for i in range(0,c):
            x=self.lists.item(i)
            if str(x.text())==user:
                #todo here
                x_str=str(x.text())
                if x_str not in self.cwDict.keys():
                    x.setTextColor(QColor(255,0,0))
                    return True
        return False
                    
    #更新聊天记录字典
    def getMessage(self,message):
        l=messageHandler(message)
        print l
        fromUser=l[0]
        content=l[1]

        self.appendChatDict(fromUser, content, fromUser)
        #print 'chat content now--->\r\n'+chatDict[fromUser]
        #改变listWidget的对应item的外观
        self.setUnread(fromUser)

                

    def Send(self,callback,message):
        global iFuncId
        global lCallback
        lCallback[iFuncId] = callback
        time.sleep(INTERVAL)
        s.send("[%d] %s" % (iFuncId,message))
        iFuncId += 1
        print 'send message to ChatServer : %s'%message
    
    def onGetMemberList(self,message):
        self.userlist=messageHandler(message)
        self.lists.clear()
        for item in self.userlist:
            if item!=accountName:
                self.lists.addItem(item)
    
    def openChatWindow(self,fromUser,toUser):
        print 'open chat window'
        if toUser not in self.cwDict.keys():
            self.cw=ChatWindow(fromUser,toUser)
            self.cwDict[toUser]=self.cw
            self.cw.show()    
        
    def Send(self,callback,message):
        global iFuncId
        global lCallback
        lCallback[iFuncId] = callback
        time.sleep(INTERVAL)
        s.send("[%d] %s" % (iFuncId,message))
        iFuncId += 1
        print 'send message to ChatServer : %s'%message
            
    #接收服务器数据的线程
    def recvListener(self,socket):
        while 1:
            try:
                if self.flag:
                    data = socket.recv(RECV_BUFFER)
                    if not data:
                        pass
                    else:
                        iFuncId,message=dataHandler(data)
                        iFuncId=int(iFuncId)
                        
                        #id号小于-100的为响应服务器指令的回调函数，通过resActionDict字典获取
                        #id号为正整数的是客户端发送请求，服务器响应客户端请求的的回调函数，通过iCallback字典获取
                        if iFuncId<-100:
                                self.resActionDict.get(iFuncId)(message)
                        else:
                            func = lCallback.get(iFuncId,None)
                            if func:
                                func(message)
                                del lCallback[iFuncId]
                            else:
                                pass
                else:
                    pass
            except Exception,e:
                print e
                break        

#登陆界面主类
class LoginGui(QDialog):  
    def __init__(self):  
        QDialog.__init__(self)
        self.setWindowTitle('login')
        self.lableName=QLabel("please enter a nick name :")
        self.username = QLineEdit(self)  
        self.buttonLogin = QPushButton('Login', self)  
        self.buttonLogin.clicked.connect(self.handleLogin)  
        layout = QVBoxLayout(self)  
        layout.addWidget(self.lableName)  
        layout.addWidget(self.username)  
        layout.addWidget(self.buttonLogin)  
    
    
    def handleLogin(self):  
        global accountName
        username=self.username.text()
        username=str(username).strip()
        if username=='':
            QMessageBox.warning(  
                self, 'Error', 'Please enter a nick name')  
            return
        a='[-2]login&'+username
        s.send(a)
        data=s.recv(RECV_BUFFER)
        print data
        sFuncId,message=dataHandler(data)
        if message=='1' :
            accountName=username
            if not os.path.exists(DIR_PREFIX+accountName):
                os.makedirs(DIR_PREFIX+accountName)
            self.accept()
        else:  
            QMessageBox.warning(  
                self, 'Error', 'Name has already been taken,Please try again')   

if __name__ == '__main__':
    #用户名
    accountName=None
    
    #实现异步回调
    lCallback = {}
    iFuncId = 1
    
    #存储聊天数据在客户端上面，不在服务器端。使用字典实现
    #format------>key<toUser>:value<chat content>
    chatDict={}
    
    #创建套接字
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    
    #运行app
    app = QApplication(sys.argv)
    if LoginGui().exec_()==QDialog.Accepted:
        lw=ListWindow()
        lw.show()
        app.exec_()
 
    
    
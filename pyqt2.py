#coding:utf-8
import socket
import threading
import sys
import time
 
from PyQt4 import QtCore as core
from PyQt4 import QtGui as gui
 
host = 'localhost'
port = 5005
recvContent=''
cmdList=['look','userls','roomls','back','chatto','login','logout']
class RecvThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    
    def run(self):
        while True:
            try:
                data = s.recv(1024)
                if not data:
                    exit()
                self.messages.append(data)
                print self.messages
            except:
                return    
            
            
    def getMsg(self):
        return self.messages
    


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
    
    
class LoginGui(gui.QDialog):  
    def __init__(self):  
        gui.QDialog.__init__(self)
        self.lableName=gui.QLabel(self)
        self.textName = gui.QLineEdit(self)  
        self.buttonLogin = gui.QPushButton('LoginGui', self)  
        self.buttonLogin.clicked.connect(self.handleLogin)  
        layout = gui.QVBoxLayout(self)  
        layout.addWidget(self.lableName)  
        layout.addWidget(self.textName)  
        layout.addWidget(self.buttonLogin)  

  
    def handleLogin(self):  
        username=self.textName.text()
        username=str(username)
        a='login '+username+'\r\n'
        s.send(a)
        s.recv(1024)
        d=s.recv(1024)
        if username.split() :
            if cmp(d,username+' has entered the MAIN room.\r\n')==0:
                self.accept()
            else:  
                gui.QMessageBox.warning(  
                    self, 'Error', 'Name has already been taken,Please try again')   
        else:
            gui.QMessageBox.warning(  
                self, 'Error', 'Please enter a  nick name')               
            

            
class Client(gui.QWidget):
    def __init__(self, parent = None):
        super(Client, self).__init__(parent)
        self.setWindowTitle('CLient')
        self.layout = gui.QGridLayout(self)
        self.btnSend = gui.QPushButton('send')
        self.input = gui.QLineEdit()
        self.name = gui.QLineEdit('Default')
        self.chat = gui.QTextEdit()
        self.timer = core.QTimer()
        self.messages = []
        self.build()
        self.createAction()
        recvThread = threading.Thread(target = self.recvFromServer)
        recvThread.setDaemon(True)
        recvThread.start()
 
    def sendToServer(self):
        text = str(self.input.text())
        self.input.setText('')
        if text.strip() == '':
            return
        try:
            parts = text.split(' ',1)
            cmd = parts[0]
            if cmd not in cmdList:
                s.send('say '+text+'\r\n')
            else:
                s.send(text+'\r\n')
            print '>> %s' %text
        except:
            self.exit()
 
    def recvFromServer(self):
        while 1:
            try:
                data = s.recv(1024)
                if not data:
                    exit()
                self.messages.append(data)
                print self.messages
            except:
                return
 
    def showChat(self):
        for m in self.messages:
            self.chat.append(m)
        self.messages = []
 
    def exit(self):
        s.close()
        sys.exit()
 
    def build(self):
        self.layout.addWidget(self.chat, 0, 0, 5, 4)
        self.layout.addWidget(self.input, 5, 0, 1, 4)
        self.layout.addWidget(self.btnSend, 5, 4)
 
        self.layout.setSizeConstraint(gui.QLayout.SetFixedSize)
 
    def createAction(self):
        self.btnSend.clicked.connect(self.sendToServer)
        self.timer.timeout.connect(self.showChat)
        self.timer.start(500)
 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))

print s
app = gui.QApplication(sys.argv)
if LoginGui().exec_()==gui.QDialog.Accepted:
    c = Client()
    c.show()
    app.exec_()
 
    
    
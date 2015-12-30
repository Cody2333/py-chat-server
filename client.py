# coding:utf-8
import socket
import threading
import sys
import time
import os

from PyQt4.QtGui import *
from PyQt4.QtCore import *

recvContent = ''
lCallback = {}
iFuncId = 1
RECV_BUFFER = 1024
PORT = 3316
HOST = 'localhost'
INTERVAL = 0.1
DIR_PREFIX = 'client/'


# 两个工具函数，用于处理接收到的数据指令

def data_handle(data):
    print 'data = %s' % data
    i = data.find('[')
    j = data.find(']')
    if i != -1 and j != -1:
        sFuncId = data[i + 1:j].strip()
        message = data[j + 1:].strip()
    else:
        sFuncId = '0'
        message = 'error'

    return sFuncId, message


def message_handler(message):
    list = message.split('&')
    return list


# 会话聊天主界面
class ChatWindow(QWidget):
    # fromUser:本机名字
    # toUser  :通信方名字
    def __init__(self, fromUser, toUser):
        super(ChatWindow, self).__init__()
        # init data
        self.fromUser = fromUser
        self.toUser = toUser
        self.listwindow = lw
        self.title = 'talking to %s .' % self.toUser
        chat_dict.setdefault(toUser, '')
        # init gui
        self.init_view(toUser)
        self.init_layout()
        self.create_action()

    def init_view(self, toUser=''):
        self.setWindowTitle(self.title)
        self.layout = QGridLayout(self)
        self.btnSend = QPushButton('send')
        self.file = QPushButton("File")
        self.input = QLineEdit()
        self.name = QLineEdit('Default')
        self.chatText = QTextEdit()
        self.chatText.setReadOnly(True)
        self.chatText.setText(chat_dict[toUser])
        self.timer = QTimer()

    def init_layout(self):
        self.layout.addWidget(self.chatText, 0, 0, 5, 4)
        self.layout.addWidget(self.input, 5, 0, 1, 4)
        self.layout.addWidget(self.btnSend, 6, 0)
        self.layout.addWidget(self.file, 5, 4)

    def create_action(self):
        self.btnSend.clicked.connect(self.send_msg)
        self.file.clicked.connect(self.get_file_name)

    # 响应window关闭事件
    def closeEvent(self, event):
        self.listwindow.cw_dict.pop(self.toUser)
        event.accept()

    # 响应客户端gui的文件选择操作，发送给服务器文件名
    def get_file_name(self):
        self.file_dir = QFileDialog.getOpenFileName(self, "Open file dialog", "/", "All files (*)")
        if str(self.file_dir) == '':
            return
        # print self.file_dir
        self.file_name = self.file_dir.split('/')[-1]
        # print self.file_name

        # self.input.setText(self.fileDir)
        try:
            data = 'filename&%s&%s' % (self.toUser, self.file_name)
            # 回调函数为onReadyForSend
            self.listwindow.send(self.on_ready_for_send, data)
            self.listwindow.append_chat_dict(self.toUser, "send file:" + self.file_name)
        except:
            QMessageBox.warning(
                    self, 'Error', 'send file failed---')

    def on_ready_for_send(self, message):
        if message == '1':
            time.sleep(INTERVAL)
            # 服务器已经收到文件信息，打开相应文件发送到服务器
            print 'send filename success'
            self.send_file()
        else:
            print 'send filename failed'

            self.listwindow.append_chat_dict(self.toUser, 'send file failed')
            QMessageBox.warning(
                    self, 'Error', 'send file failed')

    # 点击发送信息执行的函数
    def send_msg(self):
        text = str(self.input.text())
        self.input.setText('')
        if text.strip() == '':
            return
        else:
            try:
                data = 'talkto&%s&%s' % (self.toUser, text)
                print data
                self.listwindow.send(self.on_send_msg, data)
                self.listwindow.append_chat_dict(self.toUser, text, self.fromUser)
            except:
                QMessageBox.warning(
                        self, 'Error', 'send message failed--- ')

    # 发送信息的回调函数
    def on_send_msg(self, message):
        if message == '1':
            print 'send message success--'
        else:
            print 'send message failed --'
            QMessageBox.warning(
                    self, 'Error', 'send message failed -')

    def thread_send_file(self, dir, to_user):
        try:
            f = open(dir, 'rb')
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
            self.listwindow.append_chat_dict(to_user, 'send file success ~~')
        except:
            self.listwindow.append_chat_dict(to_user, 'send file failed !!')
            print 'sending file failed!!!'

    def send_file(self):
        # send file
        print "server ready, now client sending file~~"
        self.listwindow.append_chat_dict(self.toUser, 'sending file ~~')
        send_thread = threading.Thread(target=self.thread_send_file, args=(self.file_dir, self.toUser,))
        send_thread.setDaemon(True)
        send_thread.start()


class ListWindow(QMainWindow):
    global account_name

    def __init__(self):
        super(ListWindow, self).__init__()
        # init data
        # run_flag 用于控制recv_listener线程的启动与暂停，现在接收线程是阻塞的，接收文件时无法接收其他信息。
        self.run_flag = 1
        self.cw_dict = {}

        # init view and layout
        self.init_view()
        self.init_layout()

        # 初始化信号和槽的关系
        self.create_action()

        # 响应服务器的请求function的字典format---->key<int>:value<function>
        self.res_action_dict = {-101: self.update_list,
                                -102: self.get_msg,
                                -104: self.ready_for_recv_file}

        # 开启接收数据的监听线程
        recv_thread = threading.Thread(target=self.recv_listener, args=(s,))
        recv_thread.setDaemon(True)
        recv_thread.start()

    def init_view(self):
        self.setGeometry(100, 100, 250, 550)
        self.setWindowTitle(account_name)
        self.timer = QTimer()
        self.lists = QListWidget()
        self.quit = QPushButton("Quit")
        self.refresh = QPushButton("refresh")

    def init_layout(self):
        vLayout = QVBoxLayout()
        vLayout.addWidget(self.lists)
        vLayout.addWidget(self.quit)
        vLayout.addWidget(self.refresh)
        widget = QWidget()
        widget.setLayout(vLayout)
        self.setCentralWidget(widget)

    def create_action(self):
        self.update_list()
        self.quit.clicked.connect(self.exit)
        self.refresh.clicked.connect(self.update_list)
        self.lists.itemDoubleClicked.connect(self.on_item_double_clicked)

    def closeEvent(self, event):
        self.cw_dict = {}
        s.close()
        event.accept()
        print 'close'

    def exit(self):
        self.cw_dict = {}
        s.close()
        print 'exit'
        sys.exit()

    # 双击 user name 与该 user 进行交谈，打开chat window
    def on_item_double_clicked(self, item):
        global account_name
        item.setTextColor(QColor(0, 0, 0))
        toUser = str(item.text())
        self.open_chat_window(account_name, toUser)

    def recv_file(self, message):
        self.run_flag = 0
        print "starting revc file!!!"
        print self.recv_sourcename
        print self.recv_filename

        self.append_chat_dict(self.recv_sourcename, 'send a file to you, receiving~~', self.recv_sourcename)
        f = open(DIR_PREFIX + account_name + '/' + self.recv_filename, 'wb')
        while True:
            data = s.recv(RECV_BUFFER)
            if data == 'EOF':
                print "recv file success!"
                self.run_flag = 1
                break
            f.write(data)
        f.close()
        self.append_chat_dict(self.recv_sourcename, "recv file '%s' successfully" % self.recv_filename)

    '''用于改变chat_dict的工具函数
        args:name     --->   chat_dict的key
             content  --->   显示的内容
             showName --->   显示的发送者[可选]
    '''

    def append_chat_dict(self, name, content, showName='>>>>>'):
        if showName:
            chat_dict.setdefault(name, "")
            chat_dict[name] += showName + ' : ' + content + '\r\n'
            isUnread = self.set_list_state(name)

        # 如果会话窗口存在，刷新会话窗口
        if not isUnread:
            self.cw_dict[name].chatText.append(showName + ":" + content)

    def ready_for_recv_file(self, message):
        l = message_handler(message)
        self.recv_filename = l[0]
        self.recv_sourcename = l[1]
        self.send(self.recv_file, 'ready&%s' % self.recv_filename)

    # 更新在线成员列表
    def update_list(self, message=''):
        global account_name
        self.send(self.on_get_member_list, 'getmember&%s' % account_name)

    # 如果不存在和user的会话窗口那么将user设置为未读。
    def set_list_state(self, user):
        # 改变listWidget的对应item的外观
        c = self.lists.count()
        i = 0
        for i in range(0, c):
            x = self.lists.item(i)
            if str(x.text()) == user:
                # todo here
                x_str = str(x.text())
                if x_str not in self.cw_dict.keys():
                    x.setTextColor(QColor(255, 0, 0))
                    return True
        return False

    # 更新聊天记录字典
    def get_msg(self, message):
        l = message_handler(message)
        print l
        from_user = l[0]
        content = l[1]

        self.append_chat_dict(from_user, content, from_user)
        # print 'chat content now--->\r\n'+chatDict[fromUser]
        # 改变listWidget的对应item的外观
        self.set_list_state(from_user)

    @staticmethod
    def send(callback, message):
        global iFuncId
        global lCallback
        lCallback[iFuncId] = callback
        time.sleep(INTERVAL)
        s.send("[%d] %s" % (iFuncId, message))
        iFuncId += 1
        print 'send message to ChatServer : %s' % message

    def on_get_member_list(self, message):
        self.userlist = message_handler(message)
        self.lists.clear()
        for item in self.userlist:
            if item != account_name:
                self.lists.addItem(item)

    def open_chat_window(self, fromUser, toUser):
        print 'open chat window'
        if toUser not in self.cw_dict.keys():
            self.cw = ChatWindow(fromUser, toUser)
            self.cw_dict[toUser] = self.cw
            self.cw.show()

    # 接收服务器数据的线程
    def recv_listener(self, socket):
        while 1:
            try:
                if self.run_flag:
                    data = socket.recv(RECV_BUFFER)
                    if not data:
                        pass
                    else:
                        iFuncId, message = data_handle(data)
                        iFuncId = int(iFuncId)

                        # id号小于-100的为响应服务器指令的回调函数，通过resActionDict字典获取
                        # id号为正整数的是客户端发送请求，服务器响应客户端请求的的回调函数，通过iCallback字典获取
                        if iFuncId < -100:
                            self.res_action_dict.get(iFuncId)(message)
                        else:
                            func = lCallback.get(iFuncId, None)
                            if func:
                                func(message)
                                del lCallback[iFuncId]
                            else:
                                pass
                else:
                    pass
            except Exception, e:
                print e
                break


# 登陆界面主类
class LoginGui(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setWindowTitle('login')
        self.lableName = QLabel("please enter a nick name :")
        self.username = QLineEdit(self)
        self.buttonLogin = QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handle_login)
        layout = QVBoxLayout(self)
        layout.addWidget(self.lableName)
        layout.addWidget(self.username)
        layout.addWidget(self.buttonLogin)

    def handle_login(self):
        global account_name
        username = self.username.text()
        username = str(username).strip()
        if username == '':
            QMessageBox.warning(
                    self, 'Error', 'Please enter a nick name')
            return
        a = '[-2]login&' + username
        s.send(a)
        data = s.recv(RECV_BUFFER)
        print data
        sFuncId, message = data_handle(data)
        if message == '1':
            account_name = username
            if not os.path.exists(DIR_PREFIX + account_name):
                os.makedirs(DIR_PREFIX + account_name)
            self.accept()
        else:
            QMessageBox.warning(
                    self, 'Error', 'Name has already been taken,Please try again')


if __name__ == '__main__':
    # 用户名
    account_name = None

    # 实现异步回调
    lCallback = {}
    iFuncId = 1

    # 存储聊天数据在客户端上面，不在服务器端。使用字典实现
    # format------>key<toUser>:value<chat content>
    chat_dict = {}

    # 创建套接字
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    # 运行app
    app = QApplication(sys.argv)
    if LoginGui().exec_() == QDialog.Accepted:
        lw = ListWindow()
        lw.show()
        app.exec_()

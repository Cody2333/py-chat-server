# -*- coding:utf-8 -*-
from PyQt4.QtGui import *

class ChatWindow(QMainWindow):
    def __init__(self,fromUser,toUser):
        super(ChatWindow, self).__init__()
        self.resize(400, 300)
        self.setWindowTitle("this is chat window")
        self.fromUser=fromUser
        self.toUser=toUser
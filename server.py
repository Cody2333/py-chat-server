# -*-coding:utf-8-*-
from socket import *
import time
import select
import UserDict
import os

# global variables
RECV_BUFFER = 1024
PORT = 3316
HOST = ""
NAME = "CodyChatServer"
INTERVAL = 0.1


def data_handler(data):
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
    l = message.split('&')
    return l


def send(message, sock):
    sock.send(message)
    print 'send to listener: %s' % message


class ChatServer(object):
    def __init__(self, port, name):
        if not os.path.exists('server'):
            os.mkdir('server')
        self.cmd_dict = {'login': self.do_login,
                         'getmember': self.do_get_member_list,
                         'talkto': self.do_talk,
                         'filename': self.do_get_file_name,
                         'ready': self.do_send_file}
        self.CONNECTION_LIST = []
        self.port = port
        self.host = ''
        self.name = name
        self.user_dict = {}
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        self.CONNECTION_LIST.append(self.server_socket)
        print "Chat server %s started on port %d" % (self.name, self.port)

    def broadcast(self, sock, message):
        for s in self.CONNECTION_LIST:
            if s != self.server_socket and s != sock:
                try:
                    s.send(message)
                except:
                    s.close()
                    self.CONNECTION_LIST.remove(s)

    def create_new(self, name, sock):
        self.user_dict[name] = sock
        self.broadcast(sock, '[-101]lalala')

    def do_login(self, cmd_list, sock, funcId):
        if cmd_list[1] not in self.user_dict.keys():
            name = cmd_list[1]
            send('[%s]1' % funcId, sock)
            self.create_new(name, sock)
        else:
            send('[%s]0' % funcId, sock)

    def get_sock_by_name(self, name):
        return self.user_dict[name]

    def do_talk(self, cmd_list, sock, funcId):
        name = cmd_list[1]
        content = cmd_list[2]
        print '@@@' + name
        for key, value in self.user_dict.items():
            if value == sock:
                source_name = key
        if name not in self.user_dict.keys():
            send('[%s]0' % funcId, sock)
        else:
            targetSock = self.get_sock_by_name(name)
            try:
                send('[-102]%s&%s' % (source_name, content), targetSock)
                send('[%s]1' % funcId, sock)
            except:
                send('[%s]-1' % funcId, sock)

    def do_get_member_list(self, cmd_list, sock, funcId):
        # time.sleep(0.5)
        msg = '[%s]' % funcId
        for name in self.user_dict.keys():
            msg = msg + name + '&'
        msg = msg.strip('&')
        send(msg, sock)

    def do_get_file_name(self, cmd_list, sock, funcId):
        name = cmd_list[1]
        print 'get file name %s' % cmd_list[2]
        self.file_name = cmd_list[2].strip()
        if self.file_name:
            # 接收文件名成功
            message = '[%s]1' % funcId
            send(message, sock)

            # 接收文件成功之后，进行文件接收
            self.recv_file(self.file_name, sock)
            self.send_file(name, self.file_name, sock)
        else:
            # 接收文件名失败
            message = '[%s]0' % funcId
            send(message, sock)

    @staticmethod
    def do_send_file(cmd_list, sock, funcId):
        # send file
        print "server sending file to client   ~~~"
        filename = cmd_list[1]
        msg = '[%s]1' % funcId
        send(msg, sock)
        time.sleep(INTERVAL)
        try:
            f = open('server/' + filename, 'rb')
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

    def send_file(self, name, filename, sock):
        # 先传输文件名,客户端响应，回调doSendFile函数
        targetSock = self.get_sock_by_name(name)
        for key, value in self.user_dict.items():
            if value == sock:
                sourceName = key
        msg = '[-104]%s&%s' % (filename, sourceName)
        send(msg, targetSock)

    @staticmethod
    def recv_file(filename, sock):
        # TODO
        # 现在处理文件传输的方式是非异步的，服务器一次只能处理一个文件传输？
        print "starting revc file!"
        try:
            f = open('server/' + filename, 'wb')
            while True:
                data = sock.recv(RECV_BUFFER)
                if data == 'EOF':
                    print "recv file success!"
                    break
                f.write(data)
            f.close()
        except:
            print 'recv file failed'

    def logout(self, sock, addr):
        print "Client (%s, %s) is offline" % addr
        sock.close()
        self.CONNECTION_LIST.remove(sock)
        for key, value in self.user_dict.items():
            if value == sock:
                del self.user_dict[key]
                print key, 'deleted'
        self.broadcast(sock, '[-101]lalala')

    def loop(self):
        while 1:
            self.read_sockets, self.write_sockets, self.error_sockets = select.select(self.CONNECTION_LIST, [], [])

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
                            funcId, message = data_handler(data)
                            if funcId != '0':
                                cmd_list = message_handler(message)
                                try:
                                    self.cmd_dict.get(cmd_list[0])(cmd_list, sock, funcId)
                                except:
                                    print 'command not match'
                            else:
                                print 'cmd error'

                    except:
                        self.logout(sock, addr)
                        continue

        self.server_socket.close()


if __name__ == '__main__':
    chatServer = ChatServer(PORT, NAME)
    chatServer.loop()

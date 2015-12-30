from asyncore import dispatcher
from asynchat import async_chat
import socket, asyncore

PORT = 5005
NAME = 'TestChat'
'''
available commands:
	command				format				function
	login  				login<name>			login to the main room with the name
	say					say<something>		send a message in the specified room
	look				look				check the online people's list in the room
	userls				userls				check the online people's list in the server
	talkto				talkto<name>		create a new room that contains you and the person named 'name'
	back				back				go back to main chat room
	logout				logout				logout the user, exit the program
	roomls				roomls				check the total chat room list on the server
	create				create<room name>	create a new chat room for communication


'''


class EndSession(Exception): pass


class MyHandle():
    '''
    get user's first input word as a command
    '''

    def unmatched(self, session, cmd):
        session.push("No such command %s found\r\n" % cmd)

    def handle(self, session, line):
        if not line.strip():
            return
        parts = line.split(' ', 1)
        cmd = parts[0]
        try:
            line = parts[1].strip()
        except IndexError:
            line = ''
        func = getattr(self, 'do_' + cmd, None)
        try:
            func(session, line)
        except TypeError:
            self.unmatched(session, cmd)


class Room(MyHandle):
    '''
    base type
    '''

    def __init__(self, server):
        self.server = server
        self.sessions = []

    def add(self, session):
        self.sessions.append(session)

    def remove(self, session):
        if session in self.sessions:
            self.sessions.remove(session)

    def broadcast(self, line):
        for session in self.sessions:
            session.push(line)

    @staticmethod
    def do_logout(session, line):
        raise EndSession


class LoginRoom(Room):
    '''
    single user room for login
    '''

    def __init__(self, server):
        Room.__init__(self, server)

    def add(self, session):
        Room.add(self, session)
        session.push('Welcome to %s\r\n' % self.server.name)

    def unmatched(self, session, line):
        '''
        you can only do login in LoginRoom
        '''
        session.push('Please login first \nUse command login<name>\r\n')

    def do_login(self, session, line):
        name = line.strip()
        if not name:
            session.push('please enter a nick name first:\r\n')
        elif name in self.server.user_dict:
            session.push('Name is already taken')
            session.push('Please try again')
        else:
            session.name = name
            session.enter(self.server.mainRoom)


class LogoutRoom(Room):
    def __init__(self, server):
        Room.__init__(self, server)

    def add(self, session):
        '''
        do remove the session here
        '''
        self.logout(session)

    def logout(self, session):
        if session.name in self.server.user_dict.keys():
            del self.server.user_dict[session.name]
        print 'client disconnect------', session.name


class ChatRoom(Room):
    def __init__(self, server, name=''):
        Room.__init__(self, server)
        self.name = name
        self.server.room_dict[self.name] = self

    def add(self, session):
        Room.add(self, session)
        self.broadcast('%s has entered the %s room.\r\n' % (session.name, self.name))
        self.server.user_dict[session.name] = session

    def remove(self, session):
        Room.remove(self, session)
        self.broadcast('%s has left the room.\r\n' % session.name)

    def do_say(self, session, line):
        self.broadcast(session.name + ': ' + line + '\r\n')

    def do_look(self, session, line):
        session.push('the following users are in the room\r\n')
        for user in self.sessions:
            session.push(user.name + '\r\n')
        session.push('------------------\r\n')

    def do_userls(self, session, line):
        session.push('the following users are in the server\r\n')
        for username in self.server.user_dict:
            session.push(username + '\r\n')
        session.push('------------------\r\n')

    def do_create(self, session, line):
        line = line.strip()
        ls = line.split(' ')
        new_room = PrivateRoom(self.server, ls[0])
        session.enter(new_room)
        for name in ls:
            if name in self.server.user_dict.keys():
                session2 = self.server.user_dict[name]
                session2.enter(new_room)

    def do_talkto(self, session, line):
        line = line.strip()
        new_room = PrivateRoom(self.server, session.name + '&' + line)
        session.enter(new_room)
        if line in self.server.user_dict.keys():
            session2 = self.server.user_dict[line]
            session2.enter(new_room)
        else:
            session.push('no name matched:\r\n')

    def do_roomls(self, session, line):
        session.push('the following rooms are in the server\r\n')
        for roomname in self.server.room_dict:
            session.push(roomname + '\r\n')
        session.push('------------------\r\n')


class PrivateRoom(ChatRoom):
    '''
    when a user exit the room, the room destroyed
    '''

    def __init__(self, server, name='private'):
        ChatRoom.__init__(self, server, name)

    def do_back(self, session, line):
        session.enter(self.server.mainRoom)

    def remove(self, session):
        if session in self.sessions:
            self.sessions.remove(session)
        if len(self.sessions) == 0:
            del self.server.room_dict[self.name]


class ChatSession(async_chat):
    '''
    handle the connection
    between the server and a client
    '''

    def __init__(self, server, sock):
        async_chat.__init__(self, sock)
        self.server = server
        self.set_terminator("\r\n")
        self.data = []
        self.name = 'Anonymous'
        self.room = None
        self.enter(LoginRoom(server))

    def enter(self, room):

        current_room = self.room
        if current_room != None:
            current_room.remove(self)
        self.room = room
        room.add(self)

    def collect_incoming_data(self, data):
        self.data.append(data)

    def found_terminator(self):
        line = ''.join(self.data)
        self.data = []
        try:
            self.room.handle(self, line)
        except EndSession:
            self.handle_close()

    def handle_close(self):
        async_chat.handle_close(self)
        self.enter(LogoutRoom(self.server))


class ChatServer(dispatcher):
    def __init__(self, port, name):
        dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('', port))
        self.listen(5)
        self.name = name
        self.user_dict = {}
        self.room_dict = {}
        self.mainRoom = ChatRoom(self, 'MAIN')

    def handle_accept(self):
        conn, addr = self.accept()
        self.name = addr[0]
        print 'client connected------', addr
        ChatSession(self, conn)


if __name__ == '__main__':
    s = ChatServer(PORT, NAME)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        print

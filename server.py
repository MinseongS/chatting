import socketserver
import threading

HOST = ''
PORT = 8080
lock = threading.Lock()  # syncronized 동기화 진행하는 스레드 생성


class Manager:  # 사용자, 채팅방 관리

    def __init__(self):
        self.users = {}  # 사용자의 등록 정보를 담을 딕셔너리 {사용자 이름:[소켓,주소,방]}
        self.rooms = {'lobby': set()}  # 방의 정보를 담을 딕셔너리 {방 ID:set(참가자)}

    def addUser(self, username, conn, addr):
        if username in self.users:  # 이미 등록된 사용자라면
            conn.send('이미 등록된 사용자입니다.\n'.encode())
            return None
        # 새로운 사용자를 등록함
        lock.acquire()
        self.users[username] = [conn, addr, 'lobby']
        self.rooms['lobby'].add(username)
        lock.release()
        self.sendMessageTo(f'[{username}]님이 lobby에 입장했습니다.', username, log=True)
        print(f'--- 전체 대화 참여자 수 [{len(self.users)}]')
        return username

    def removeUser(self, username):  # 사용자를 제거하는 함수
        if username not in self.users:
            return

        self.changeRoom(username, 'lobby')

        lock.acquire()
        self.rooms['lobby'].remove(username)
        del self.users[username]
        lock.release()

        self.sendMessageTo(f'[{username}]님이 퇴장했습니다.', username, log=True)
        print(f'--- 대화 참여자 수 [{len(self.users)}]')

    def makeRoom(self, username, roomname):
        conn, addr, preroom = self.users[username]
        if roomname in self.rooms.keys():
            conn.send('이미 존재하는 방입니다.\n'.encode())
            return

        self.changeRoom(username, 'lobby')
        self.sendMessageTo(f'{roomname}방이 만들어졌습니다.', username, log=True)

        lock.acquire()
        self.rooms[roomname] = set([username])
        lock.release()

        self.changeRoom(username, roomname)

        return


    def changeRoom(self, username, room):
        conn, addr, preroom = self.users[username]
        if preroom == room:
            return

        if room not in self.rooms.keys():
            conn.send('존재하지 않는 방입니다.\n'.encode())
            return

        lock.acquire()
        self.users[username][2] = room
        self.rooms[preroom].remove(username)
        self.rooms[room].add(username)
        if len(self.rooms[preroom]) == 0 and preroom != 'lobby':
            del self.rooms[preroom]
            self.sendMessageTo(f'{preroom}방이 삭제됐습니다.', username, log=True)
        lock.release()

        self.sendMessageTo(f'{username}님이 {room}에 입장했습니다.\n', username, log=True)

        return

    def messageHandler(self, username, msg):  # 전송한 msg를 처리하는 부분
        conn, addr, room = self.users[username]
        if msg[0] != '/':  # 보낸 메세지의 첫문자가 '/'가 아니면
            self.sendMessageTo(f'{msg}', username)
            return
        else:
            cmd = msg.strip().split(' ')
            try:
                if cmd[0] == '/enter':
                    self.changeRoom(username, cmd[1])
                    return

                if cmd[0] == '/makeroom':
                    self.makeRoom(username, cmd[1])
                    return

                if cmd[0] == '/leave':
                    self.changeRoom(username, 'lobby')
                    return

                if cmd[0] == '/quit':
                    self.removeUser(username)
                    return -1

                if cmd[0] == '/showroom':
                    roomlist = ''
                    for r in self.rooms.keys():
                        if r != 0:
                            roomlist += r + ' '
                    if len(roomlist) != 0:
                        conn.send(f'{roomlist}'.encode())
                    else:
                        conn.send('생성된 방이 없습니다.'.encode())
                    return

                if cmd[0] == '/status':
                    conn.send(f'현재 {room}방에 있습니다.'.encode())
                    return

                else:
                    conn.send('명령어를 다시 확인해 주세요.\n/help를 입력하면 명령어 사용법을 볼 수 있습니다.'.encode())
                    return
            except:  # 잘못된 명령어
                conn.send('명령어를 다시 확인해 주세요.\n/help를 입력하면 명령어 사용법을 볼 수 있습니다.'.encode())
                return

    def sendMessageTo(self, msg, username, log=False):
        conn, addr, room = self.users[username]
        if room == 'lobby' and log == False:
            conn.send('채팅방에 입장해주세요'.encode())
            return
        for user in self.rooms[room]:
            conn, _, _ = self.users[user]
            if log:
                conn.send(f'{msg}'.encode())
            else:
                conn.send(f'{username} : {msg}'.encode())
        if log:
            print(f'{msg}')
        else:
            print(f'[{room}] {username} : {msg}')


class MyTcpHandler(socketserver.BaseRequestHandler):
    manager = Manager()

    def handle(self):  # 클라이언트가 접속시 클라이언트 주소 출력
        print(f'[{self.client_address[0]}] 연결됨')
        username = ''
        try:
            username = self.registerUsername()
            msg = self.request.recv(1024)
            while msg:
                status = self.manager.messageHandler(username, msg.decode())
                if status == -1:
                    self.request.close()
                    break

                msg = self.request.recv(1024)

        except Exception as e:
            print(e)

        print(f'[{self.client_address[0]}] 접속종료')
        if username in self.manager.users.keys():
            self.manager.removeUser(username)


    def registerUsername(self):
        while True:
            self.request.send('로그인ID:'.encode())
            username = self.request.recv(1024)
            username = username.decode().strip()
            if self.manager.addUser(username, self.request, self.client_address):
                return username


class ChatingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def runServer():
    print('--- 채팅 서버를 시작합니다.')
    print('--- 채텅 서버를 끝내려면 Ctrl-C를 누르세요.')

    try:
        server = ChatingServer((HOST, PORT), MyTcpHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print('--- 채팅 서버를 종료합니다.')
        server.shutdown()
        server.server_close()


runServer()

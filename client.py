import socket
from threading import Thread

HOST = 'localhost'
PORT = 8080


def rcvMsg(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            print(data.decode())
        except:
            pass


def runChat():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print('프로그램을 종료하려면 /quit 을 입력하세요.')
        print('/help로 명령어를 확인하세요.')
        sock.connect((HOST, PORT))
        t = Thread(target=rcvMsg, args=(sock,))
        t.daemon = True
        t.start()

        while True:
            msg = input()
            if msg == '/quit':
                sock.send(msg.encode())
                break

            if msg == '/help':
                print('/quit\t프로그램을 종료합니다.')
                print('/showroom\t방 목록을 확인합니다.')
                print('/status\t현재 방을 확입합니다.')
                print('/makeroom [roomname]\troomname 방을 만듭니다.')
                print('/enter [roomname]\troomname 방으로 들어갑니다.')
                print('/leave\t로비로 이동합니다.')
                continue

            sock.send(msg.encode())


runChat()

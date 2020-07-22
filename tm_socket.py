import socket

HOST = socket.gethostname()
PORT = 4242

def send(sock, msg):
    sent = sock.send(msg.encode('utf-8'))

def recv(sock):
    try:
        msg = sock.recv(1024)
    except ConnectionResetError:
        print('[Taskmaster] Fatal: Connection to taskmaster dameon lost')
        exit(1)
    return msg.decode('utf-8')

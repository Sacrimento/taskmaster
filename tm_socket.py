import socket

HOST = socket.gethostname()
PORT = 4242

def send(sock, msg):
    try:
        sock.send(msg.encode('utf-8'))
    except Exception as e:
        print('Could not send data : ', e)

def recv(sock):
    msg = ''
    try:
        msg = sock.recv(1024)
    except ConnectionResetError:
        print('[Taskmaster] Fatal: Connection to taskmaster daemon lost')
        exit(1)
    except Exception as e:
        print('Could not receive data : ', e)
    return msg.decode('utf-8')

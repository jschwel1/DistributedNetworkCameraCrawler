#!/usr/bin/python3
import socket
import threading
import sys
import pickle

class CameraClient():
    
    def __init__(self, name, left, right):
        self.ip = ''
        self.port = 0
        self.server_ip = ''
        self.server_port = int(sys.argv[1])
        self.socket = socket.socket()
        self.name = name
        self.left = left
        self.right = right
        
        self.open_connection()

    def socket_thread(self):
        info = {
            'name': self.name,
            'left': self.left,
            'right': self.right,
        }
        self.socket.send(pickle.dumps(info))
        print(str(self.socket.recv(2048), 'utf-8'))
        while True:
            msg = pickle.loads(self.socket.recv(2048))
            if (msg != ''):
                print(msg)
        self.socket.close()

    def open_connection(self):
        self.socket.connect((self.server_ip, self.server_port))
        print('Connected to %s on port %s' % (self.server_ip, self.server_port))
        threading.Thread(target=self.socket_thread).start()



if __name__=='__main__':
    names = {
        'N':{
            'l':['W'],
            'r':['E'],
        },
        'E':{
            'l':['N'],
            'r':['S'],
        },
        'S':{
            'l':['E'],
            'r':['W'],
        },
        'W':{
            'l':['W'],
            'r':['N'],
        },
    }
    cl = []
    for i in names:
        print('%s )'%i)
        cl.append(CameraClient(i, names[i]['l'], names[i]['r']))

    

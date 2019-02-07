#!/usr/bin/python3
import socket
import threading
import sys

class CameraClient():
    
    def __init__(self):
        self.ip = ''
        self.port = 0
        self.server_ip = ''
        self.server_port = int(sys.argv[1])
        self.socket = socket.socket()
        
        self.open_connection()

    def socket_thread(self):
        self.socket.send(bytes('Dave', 'utf-8'))
        while True:
            msg = str(self.socket.recv(1024), 'utf-8')
            if (msg != ''):
                print('%s'%msg)
        self.socket.close()

    def open_connection(self):
        self.socket.connect((self.server_ip, self.server_port))
        print('Connected to %s on port %s' % (self.server_ip, self.server_port))
        threading.Thread(target=self.socket_thread).start()



if __name__=='__main__':
    #cc = CameraClient()
    cl = []
    for i in range(125):
        print('%s )'%i)
        cl.append(CameraClient())

    

#!/usr/bin/python3

import socket
import threading

class CameraServer():
    
    def __init__(self):
        self.listen_port = 0 #51234
        self.server_socket = socket.socket()
        self.max_connections = 100
        self.cameras = {}

        # bind to port
        self.server_socket.bind(('', self.listen_port))
        print('Server is accessible at %s:%s'%(self.server_socket.getsockname()[0],self.server_socket.getsockname()[1]))
       

        self.await_connections()

    def new_connection(self, client):
        msg = str(client.recv(64), 'utf-8')
        print('Connected to %s'%msg)
        self.cameras[msg] = client
        #while True:
        client.send(bytes('Welcome to the network, %s'%msg, 'utf-8'))
        client.close()


    def await_connections(self):
        # Listen on port for arriving connections
        self.server_socket.listen(self.max_connections)
        while True:
            client, addr = self.server_socket.accept()
            threading.Thread(target=self.new_connection, args=(client,)).start()
        self.server_socket.close()

 


cs = CameraServer()


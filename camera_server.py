#!/usr/bin/python3

import socket
import threading
import pickle
import camera_client

class CameraServer():
    RECV_BLOCKING_TIMEOUT = 0.25 # seconds
    CONFIG_FILE = 'camera.cfg'

    def __init__(self):
        self.listen_port = 51235 #51234
        self.server_socket = socket.socket()
        self.max_connections = 100
        self.cameras = {}
        self.alert_list = [] # list of tuples of alerts: [(who, from, side), (who, from, side), ...]
        self.alert_list_lock = threading.Lock()

        # bind to port
        self.server_socket.bind(('', self.listen_port))
        print('Server is accessible at %s:%s'%(self.server_socket.getsockname()[0],self.server_socket.getsockname()[1]))
       

        self.await_connections()

    def new_connection(self, client):
        client.settimeout(CameraServer.RECV_BLOCKING_TIMEOUT) # timeout blocking operations
        data = pickle.loads(client.recv(2048))
        name = data['name']
        left = data['left']
        right = data['right']
        
        print('Connected to %s'%name)
        self.cameras[name] = client
        client.send(pickle.dumps('Welcome to the network, %s'%name))
        while True:
            # Acquire a lock on the alert list
            self.alert_list_lock.acquire()
            # See if this client is in the list of cameras to be alerted
            if len(self.alert_list) > 0 and name in list(zip(*self.alert_list))[0]:
                # get index of camera in the list
                idx = list(zip(*self.alert_list))[0].index(name)
                data = {
                    'from': self.alert_list[idx][1],
                    'side': self.alert_list[idx][2],
                }
                # Package the data and send it
                client.send(pickle.dumps(data))
                # Remove this alert from the list
                del self.alert_list[idx]
            # Release the mutex
            self.alert_list_lock.release()
            # Check if client sent an alert
            try:
                alert = pickle.loads(client.recv(4096))
                print('Received alert of type:',alert['type'])
            except socket.timeout:
                pass
            except BaseException as e:
                print(type(e),e)

        client.close()


    def await_connections(self):
        # Listen on port for arriving connections
        self.server_socket.listen(self.max_connections)
        while True:
            client, addr = self.server_socket.accept()
            threading.Thread(target=self.new_connection, args=(client,)).start()
        self.server_socket.close()

 

if __name__ == '__main__':
    cs = CameraServer()


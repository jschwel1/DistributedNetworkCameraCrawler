#!/usr/bin/python3

import socket
import threading
import pickle
from camera_client import CameraClient
import queue

class CameraServer():
    RECV_BLOCKING_TIMEOUT = 0.25 # seconds
    ACCEPT_CONN_TIMEOUT = 0.5
    CONFIG_FILE = 'camera.cfg'

    def __init__(self):
        self.listen_port = 51235 #51234
        self.listen_ip = '127.0.0.1'
        self.server_socket = socket.socket()
        self.max_connections = 100
        self.camera_alerts = {}
        self.shutdown_server = False

        # bind to port
        self.server_socket.settimeout(CameraServer.ACCEPT_CONN_TIMEOUT)
        self.server_socket.bind((self.listen_ip, self.listen_port))
        print('Server is accessible at %s:%s'%(self.server_socket.getsockname()[0],self.server_socket.getsockname()[1]))
       
        # start a new thread to wait for connections
        threading.Thread(target=self.await_connections).start()
        

    def new_connection(self, client):
        # Set a timeout for the connection
        client.settimeout(CameraServer.RECV_BLOCKING_TIMEOUT) # timeout blocking operations
        # Get information about this camera
        data = pickle.loads(client.recv(2048))
        name = data['name']
        left = data['left']
        right = data['right']
        should_shutdown_client = False

        print('Connected to %s'%name)
        # Add the camera to the dictionary
        if name not in self.camera_alerts:
            self.camera_alerts[name] = queue.Queue()
        else:
            print('Already connected to %s'%name)
            client.send(pickle.dumps('I have already been connected to someone with the same name. If this is unexpected, please change IDs and try again'))

        client.send(pickle.dumps('Welcome to the network, %s'%name))
        while not should_shutdown_client and not self.shutdown_server:
            # Send out any pending alerts to the client
            try:
                alert=self.camera_alerts[name].get(block=False)
                client.send(pickle.dumps(alert))
            except queue.Empty:
                pass

            # Receive alerts
            try:
                alert = pickle.loads(client.recv(4096))
                print('Received alert ',alert)
                if alert['type'] is CameraClient.LEAVE_ALERT:
                    if alert['side'] == CameraClient.LEFT:
                        cams_to_alert = left
                    elif alert['side'] == CameraClient.RIGHT:
                        cams_to_alert = right
                    else:
                        cams_to_alert = []

                    del alert['side']

                    # Add the alert to each camera's alert queue
                    for cam in cams_to_alert:
                        if cam in self.camera_alerts:
                            self.camera_alerts[cam].put(alert)
                
            except socket.timeout:
                pass
            except EOFError as e:
                print('Lost connection to %s'%name)
                break

        client.close()


    def await_connections(self):
        # Listen on port for arriving connections
        self.server_socket.listen(self.max_connections)
        while not self.shutdown_server:
            try:
                client, addr = self.server_socket.accept()
                threading.Thread(target=self.new_connection, args=(client,)).start()
            except socket.timeout:
                pass
        self.server_socket.close()

    def shutdown(self):
        self.shutdown_server = True
        print('shutting down')

 

if __name__ == '__main__':
    cs = CameraServer()

    while True:
        print('Enter q to quit')
        inpt = input()
        print('read: %s'%inpt)

        if inpt == 'q':
            cs.shutdown()
            break


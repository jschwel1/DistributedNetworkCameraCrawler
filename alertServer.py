#!/usr/bin/python3

import socket
import threading
import queue
import re
import uuid
import pickle
import time
from client import Client


class AlertServer():
    CONFIG_FILE = 'camera.cfg'
    SOCKET_BLOCKING_TIMEOUT = 0.25 # seconds
    MISSING_TIMEOUT = 3 # seconds

    def __init__(self, cfg=CONFIG_FILE):

        self.should_shutdown = False
        self.initialize_with_file(cfg)
        self.backlog_connections = 512

        self.p2p_id = uuid.uuid4()

        self.server_socket = socket.socket()
        self.server_socket.settimeout(Client.SOCKET_BLOCKING_TIMEOUT)
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(0)

        # Accept all incoming connection requests
        threading.Thread(target=self.await_connections).start()

        
    def await_connections(self):
        self.server_socket.listen(self.backlog_connections)
        while not self.should_shutdown:
            try:
                client, addr = self.server_socket.accept()
                threading.Thread(target=self.socket_thread, args=(client,)).start()
            except socket.timeout:
                pass
        self.server_socket.close()


    def initialize_with_file(self, filepath=CONFIG_FILE):
        try:
            cfg = open(filepath, 'r')
        except OSError:
            print('Config file, %s, does not exist'%filepath)
        config = self.read_config_file(filepath)
        #print(config)
        try:
            self.server_ip = config['server_ip']
            self.server_port = int(config['server_port'])
            self.name = config['name']
        except BaseException as e:
            print("INCOMPLETE CONFIG FILE")
            print(type(e), e)

    def read_config_file(self, file):
        config = {}
        with open(file) as f:
            for line in f:
                # ignore blank lines and commented out lines
                if len(line.strip()) == 0:
                    continue
                if line.strip()[0] == '#':
                    continue
                try:
                    key, val = line.split('=')
                except BaseException as e:
                    print(type(e), e)
                key = key.strip()
                val = val.strip()
                config[key] = val
        return config

    def buildAlert(self, to, alert_type, object_id):
        alert = {
            'from': self.p2p_id,
            'to': to,
            'type': alert_type,
            'time': time.time(),
            'obj': object_id,
        }
        return alert
 
       
    def handleAlert(self, alert):
        if alert['to'] != self.p2p_id and alert['to'] != Client.BROADCAST_MSG:
            return None
        
        elif alert['type'] == Client.MISSING_ALERT:
            print('WARNING: %s is missing! Last seen from camera: %s at %s'%(str(alert['obj']), str(alert['from']), str(alert['extra']['time'])))
        elif alert['type'] == Client.UNEXPECTED_ENTRANCE_ALERT:
            print('WARNING: %s unexpectedly entered at %s at %s'%(str(alert['obj']), str(alert['from']), str(alert['time'])))
        elif alert['type'] == Client.DISREGARD_MISSING_ALERT:
            print('DISREGARD: %s was found. Original alert from %s' % (str(alert['obj']), str(alert['from'])))

        return None

    def socket_thread(self, conn):
        # Send p2p id
        conn.send(pickle.dumps(self.p2p_id))

        while not self.should_shutdown:
            # Try reading incoming messages
            try:
                msg = pickle.loads(conn.recv(2048))
                if msg == '':
                    continue
                if self.handleAlert(msg) == Client.CLOSE_CONNECTION:
                    break

            except socket.timeout:
                pass
            except EOFError as e:
                print('Lost connection to peer')
                break
            except BaseException as e:
                print(type(e), e)


        
        conn.close()

    def shutdown(self):
        self.should_shutdown = True




if __name__=='__main__':
    print('Starting server...')
    s = AlertServer()
    while True:
        inpt = input()
        if (inpt == 'q'):
            s.shutdown()
            break



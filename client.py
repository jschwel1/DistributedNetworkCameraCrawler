#!/usr/bin/python3

import socket
import threading
import queue
import re
import uuid
import pickle


class Client():
    CONFIG_FILE = 'camera.cfg'
    SOCKET_BLOCKING_TIMEOUT = 0.25 # seconds
    LEFT = 0
    RIGHT = 1
    MISSING_TIMEOUT = 3 # seconds
    LEAVE_ALERT = 0
    FOUND_ALERT = 1
    MISSING_ALERT = 2
    QUITTING_ALERT = 3
    UNEXPECTED_ENTRANCE_ALERT = 4

    def __init__(self, cfg=CONFIG_FILE):

        self.expected_from_left = {} # list of alerts from the left side
        self.expected_from_right = {} # list of alerts from the right side
        self.should_shutdown = False
        self.send_dict = {}
        self.peer_connections = []
        self.peer_connections_mutex = threading.Lock()
        self.peers = {} # client object as key, queue.Queue as value
        self.peers_mutex = threading.Lock()
        self.should_shutdown = False
        self.initialize_with_file(cfg)
        self.max_connections = 2*len(self.peer_connections)

        self.server_socket = socket.socket()
        self.server_socket.settimeout(Client.SOCKET_BLOCKING_TIMEOUT)
        self.server_socket.bind((self.listen_ip, self.listen_port))
        self.server_socket.listen(0)

        self.p2p_id = uuid.uuid4() # generate a random UUID
 
        # Accept all incoming connection requests
        threading.Thread(target=self.await_connections).start()

        # For remaining requests, initiate requests
        self.peer_connections_mutex.acquire()
        for peer in self.peer_connections:
            threading.Thread(target=self.initiate_connection, args=(peer,)).start()
        self.peer_connections_mutex.release()

#        self.open_connection()


    def await_connections(self):
        self.server_socket.listen(self.max_connections)
        while not self.should_shutdown:
            try:
                client, addr = self.server_socket.accept()
                threading.Thread(target=self.new_connection, args=(True, client)).start()
            except socket.timeout:
                pass
        self.server_socket.close()

    def initiate_connection(self, peer):
        # create a new socket
        client_socket = socket.socket()
        client_socket.settimeout(Client.SOCKET_BLOCKING_TIMEOUT)
        while not self.should_shutdown:
            try:
                client_socket.connect((peer['ip'],peer['port']))
                threading.Thread(target=self.new_connection, args=(False,client_socket)).start()
                break
            except ConnectionRefusedError as cre:
                pass
            except ConnectionAbortedError as cae:
                pass
            except BaseException as e:
                print('ERROR: ', type(e), e)

    def new_connection(self, is_server, sock):
        ''' 
        When a connection is established, the server will listen,
        and the client will send first, then the server will send
        and the client will listen. Whoever has the lower UUID will
        drop the server connection. (server_uuid > client_uuid)
        '''
        print('Set up connection, I am the', 'server' if is_server else 'client')
        if is_server:
            client_uuid=pickle.loads(sock.recv(1024))
            sock.send(pickle.dumps(self.p2p_id))
            if client_uuid > self.p2p_id:
                sock.close()
                print('closing server connection')
        else:
            sock.send(pickle.dumps(self.p2p_id))
            server_uuid=pickle.loads(sock.recv(1024))
            if server_uuid < self.p2p_id:
                sock.close()
                print('closing client connection')

        sock.close()
            
            

    def send_unknown_entrance_alert(self, side):
        pass

    def send_found_alert(self, alert):
        pass

    def entered_screen_alert(self, side):
        pass
               

    def left_screen_alert(self, side):
        pass


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
            self.listen_port = int(config['listen_port'])
            self.listen_ip = config['listen_ip']
            self.name = config['name']
            self.left_endpoint = bool(config['left_endpoint'])
            self.right_endpoint = bool(config['right_endpoint'])
            # Add in the neighboring cameras
            neighbors = config['neighbors']
            for neighbor in neighbors.split(';'):
                temp = re.match('\((?P<ip>\d+\.\d+\.\d+\.\d+),(?P<port>\d+),(?P<side>\w)\)', neighbor)
                self.peer_connections.append({
                    'ip': temp.group('ip'),
                    'port': int(temp.group('port')),
                    'side': temp.group('side'),
                    'connected': False,
                })

                
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

    def socket_thread(self, conn):
        conn.close()

    def shutdown(self):
        self.should_shutdown = True



if __name__=='__main__':
    print('Starting camera...')
    #cc = Client(basics={'name':'C1','left':'c2','right':'c3,c4'})
    cc = Client()
    while True:
        inpt = input()
        if (inpt == 'l'):
            cc.left_screen_alert(Client.LEFT)
        elif (inpt == 'r'):
            cc.left_screen_alert(Client.RIGHT)
        elif (inpt == 'q'):
            cc.shutdown()
            break



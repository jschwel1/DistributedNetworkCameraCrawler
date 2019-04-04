#!/usr/bin/python3

import socket
import threading
import queue
import re
import uuid
import pickle
import time


class Client():
    CONFIG_FILE = 'camera.cfg'
    SOCKET_BLOCKING_TIMEOUT = 0.50 # seconds
    MISSING_TIMEOUT = 3 # seconds

    CLOSE_CONNECTION = 4
    LEFT = 0
    RIGHT = 1

    BROADCAST_MSG = -1

    LEAVE_ALERT = 0
    FOUND_NOTIFY = 1
    FOUND_BROADCAST = 2
    MISSING_ALERT = 3
    QUITTING_ALERT = 4
    UNEXPECTED_ENTRANCE_ALERT = 5
    DISREGARD_MISSING_ALERT = 6

    def __init__(self, cfg=CONFIG_FILE):

        self.expected_objects = {} # list of alerts. key is object id, value is who it was from
        self.missing_objects = {}   # When objects leave the screen,
                                    # they should be put here until
                                    # they are found. Key = obj_id
                                    # value = time missing
        self.missing_objects_mutex = threading.Lock()
        self.should_shutdown = False
        self.send_dict = {}
        self.peer_connections = []
        self.peer_connections_mutex = threading.Lock()
        self.peer_alerts = {} # client object as key, queue.Queue as value
        self.peer_alerts_mutex = threading.Lock()
        self.initialize_with_file(cfg)
        self.max_connections = 2*len(self.peer_connections)
        self.p2p_id = uuid.uuid4() # generate a random UUID
        print('I am %s'%str(self.p2p_id))

        # Setup connection to alert server
        self.setup_alert_server_connection()
       
        # Setup socket to listen for other peers
        self.server_socket = socket.socket()
        self.server_socket.settimeout(Client.SOCKET_BLOCKING_TIMEOUT)
        self.server_socket.bind((self.listen_ip, self.listen_port))
        self.server_socket.listen(0)

 
        # Accept all incoming connection requests
        threading.Thread(target=self.await_connections).start()

        # For remaining requests, initiate requests
        self.peer_connections_mutex.acquire()
        for peer in self.peer_connections:
            threading.Thread(target=self.initiate_connection, args=(peer,)).start()
        self.peer_connections_mutex.release()

        threading.Thread(target=self.missing_objects_watch_thread).start()

    def setup_alert_server_connection(self):
        self.alert_server_socket = socket.socket()
        self.alert_server_socket.settimeout(Client.SOCKET_BLOCKING_TIMEOUT)
        self.alert_server_socket.connect((self.server_ip, self.server_port))
        self.alert_server_id = pickle.loads(self.alert_server_socket.recv(1024))

    def send_server_alert(self, alert):
        self.alert_server_socket.send(pickle.dumps(alert))
 
    def missing_objects_watch_thread(self):
        while not self.should_shutdown:
            self.missing_objects_mutex.acquire()
            for obj in self.missing_objects:
                if time.time()-self.missing_objects[obj]['time'] > Client.MISSING_TIMEOUT\
                   and not self.missing_objects[obj]['alerted']:
                    self.missing_objects[obj]['alerted'] = True

                    alert = self.buildAlert(self.alert_server_id, Client.MISSING_ALERT, obj, self.missing_objects[obj])
                    self.send_server_alert(alert)
                    
            self.missing_objects_mutex.release()

            time.sleep(1)

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
        if is_server:
            peer_id=pickle.loads(sock.recv(1024))
            sock.send(pickle.dumps(self.p2p_id))
            if peer_id > self.p2p_id:
                sock.close()
                return
        else:
            sock.send(pickle.dumps(self.p2p_id))
            peer_id=pickle.loads(sock.recv(1024))
            if peer_id < self.p2p_id:
                sock.close()
                return
        # Sock is now the only communications socket for this connection
        self.peer_alerts_mutex.acquire()
        self.peer_alerts[peer_id]=queue.Queue()
        self.peer_alerts_mutex.release()
         
        sock.settimeout(Client.SOCKET_BLOCKING_TIMEOUT)
        self.socket_thread(sock, peer_id)
        sock.close()
            
            

    def send_unknown_entrance_alert(self, obj_id):
        pass

    def send_found_alert(self, obj_id):
        from_id = self.expected_objects[obj_id]
        del self.expected_objects[obj_id]

        print('Found %s, letting %s know...'%(str(obj_id), str(from_id)))
        self.send_alert(self.buildAlert(from_id, Client.FOUND_NOTIFY, obj_id))

    def entered_screen_alert(self, obj_id):
        pass
               

    def left_screen_alert(self, obj_id):
        self.send_alert(self.buildAlert(Client.BROADCAST_MSG, Client.LEAVE_ALERT, obj_id))
        self.missing_objects_mutex.acquire()
        self.missing_objects[obj_id] = {'time':time.time(), 'alerted':False}
        self.missing_objects_mutex.release()

    def send_alert(self, alert):
        self.peer_connections_mutex.acquire()
        for peer in self.peer_alerts:
            self.peer_alerts[peer].put(alert)
        self.peer_connections_mutex.release()

    def initialize_with_file(self, filepath=CONFIG_FILE):
        try:
            cfg = open(filepath, 'r')
        except OSError:
            print('Config file, %s, does not exist'%filepath)
        config = self.read_config_file(filepath)
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

    def buildAlert(self, to, alert_type, object_id, extra=None):
        alert = {
            'from': self.p2p_id,
            'to': to,
            'type': alert_type,
            'time': time.time(),
            'obj': object_id,
            'extra': extra,
        }
        return alert
        
    def handleAlert(self, alert):
        if alert['to'] != self.p2p_id and alert['to'] != Client.BROADCAST_MSG:
            return None
        
        # someone is alerting all neighbors that someone left their field of view
        if alert['type'] == Client.LEAVE_ALERT:
            print('looking out for obj %s (last seen at %s)' %(str(alert['obj']), str(alert['from'])))
            if alert['obj'] in self.expected_objects:
                # Alert server that someone showed up from multiple leave feeds //////////
                pass
            else:
                self.expected_objects[alert['obj']] = alert['from']

        # someone is responding to a LEAVE_ALERT, stating they found someone.
        # notify all neighbors that the person was found.
        elif alert['type'] == Client.FOUND_NOTIFY:
            self.send_alert(self.buildAlert(Client.BROADCAST_MSG, Client.FOUND_BROADCAST, alert['obj']))
            self.missing_objects_mutex.acquire()
            if alert['obj'] in self.missing_objects:
                # Check that it the server wasn't notified
                if self.missing_objects[alert['obj']]['alerted']:
                    server_alert = self.buildAlert(self.alert_server_id, Client.DISREGARD_MISSING_ALERT, alert['obj'], self.missing_objects[alert['obj']])
                    self.send_server_alert(server_alert)
 
                del self.missing_objects[alert['obj']]
            self.missing_objects_mutex.release()
            

        # If a found broadcast is received, someone who was previously expected has been found.
        # This means, the person can be removed.
        elif alert['type'] == Client.FOUND_BROADCAST:
            if alert['obj'] not in self.expected_objects:
                # Alert server that someone has been unaccounted for
                pass
            elif alert['from'] != self.expected_objects[alert['obj']]:
                # Alert server that an object was missing from multiple cameras
                pass
            else:
                # Object was expected and from the correct broadcaster
                # Remove the object from the expected objects
                del self.expected_objects[alert['obj']]
         
        # received if a camera is closing, so connections can be closed.
        elif alert['type'] == Client.QUITTING_ALERT:
            return Client.CLOSE_CONNECTION
                
        return None

    def socket_thread(self, conn, peer_id):
        while not self.should_shutdown:
            # see if there is anything outbound for this peer
            self.peer_alerts_mutex.acquire()
            data=None
            try:
                data=self.peer_alerts[peer_id].get(block=False)
            except queue.Empty as e:
                pass
            self.peer_alerts_mutex.release()
            if data is not None:
                conn.send(pickle.dumps(data))

            # Try reading incoming messages
            try:
                msg = pickle.loads(conn.recv(2048))
                if msg == '':
                    continue
                if self.handleAlert(msg) == Client.CLOSE_CONNECTION:
                    print('Closing connection...', end='')
                    break

            except socket.timeout:
                pass
            except EOFError as e:
                print('Lost connection to peer')
                break
            except BaseException as e:
                print(type(e), e)


        print('closed')
        conn.close()

    def shutdown(self):
        print('starting shutdown...')
        self.send_alert(self.buildAlert(Client.BROADCAST_MSG, Client.QUITTING_ALERT, None))
        self.should_shutdown = True




if __name__=='__main__':
    print('Starting camera...')
    cc = Client()
    while True:
        inpt = input()
        if (inpt == 'l'):
            cc.left_screen_alert(123)
        elif(inpt == 'k'):
            cc.send_found_alert(123)
        elif (inpt == 'r'):
            cc.left_screen_alert(234)
        elif(inpt == 'e'):
            cc.send_found_alert(234)
 
        elif (inpt == 'q'):
            cc.shutdown()
            break



#!/usr/bin/python3
import socket
import threading
import sys
import pickle
import time
import queue


class CameraClient():
    CONFIG_FILE = 'camera.cfg'
    SOCKET_BLOCKING_TIMEOUT = 0.25 # seconds
    LEFT = 0
    RIGHT = 1
    MISSING_TIMEOUT = 3 # seconds
    LEAVE_ALERT = 0
    FOUND_ALERT = 1
    MISSING_ALERT = 2
    QUITTING_ALERT = 3

    def __init__(self, cfg=CONFIG_FILE, basics=None):
        if basics is not None:
            self.server_ip = '0.0.0.0'
            self.server_port = int(sys.argv[1])
            self.name = basics['name']
            self.left = basics['left']
            self.right = basics['right']
            self.left_endpoint = basics['left_endpoint']
            self.right_endpoint = basics['right_endpoint']
        else:
            self.initialize_with_file(cfg)

        self.expected_from_left = queue.Queue() # list of alerts from the left side
        self.expected_from_right = queue.Queue() # list of alerts from the right side
        self.should_shutdown = False

        self.send_queue = queue.Queue()

        self.expected_from_right_mutex = threading.Lock()
        self.expected_from_left_mutex = threading.Lock()
        
        self.socket = socket.socket()
        self.socket.settimeout(CameraClient.SOCKET_BLOCKING_TIMEOUT)
        self.open_connection()

    def entered_screen_alert(self, side):
        pass

    def left_screen_alert(self, side):
        '''
        When an object leaves the screen, it should call this method.
        '''
        print('Someone just left')
        data = {
            'type': CameraClient.LEAVE_ALERT,
            'time': time.time(),
            'cam': self.name,
            'side': side,
        }
        self.send_queue.put(data)


    def initialize_with_file(self, filepath=CONFIG_FILE):
        try:
            cfg = open(filepath, 'r')
        except OSError:
            print('Config file, %s, does not exist'%filepath)
        config = self.read_config_file(filepath)
        print(config)
        try:
            self.server_ip = config['server_ip']
            self.server_port = int(config['server_port'])
            self.name = config['name']
            self.left = config['left'].split(',')
            self.right = config['right'].split(',')
            self.left_endpoint = bool(config['left_endpoint'])
            self.right_endpoint = bool(config['right_endpoint'])
        except BaseException as e:
            print(type(e), e)
            print("INCOMPLETE CONFIG FILE")
        print(dir(self))
        print(self)

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

    def socket_thread(self):
        info = {
            'name': self.name,
            'left': self.left,
            'right': self.right,
        }
        # Inform server about this camera
        self.socket.send(pickle.dumps(info))
        while not self.should_shutdown:
            if not self.send_queue.empty():
                data = self.send_queue.get()
                self.socket.send(pickle.dumps(data))
                print('just let the server know: ',data)
            try:
                msg = pickle.loads(self.socket.recv(2048))
                if (msg != ''):
                    print(msg)
            except socket.timeout:
                pass
            except EOFError as e:
                print('Lost connection to server')
                break
            except BaseException as e:
                print(type(e), e)

        self.socket.close()

    def open_connection(self):
        print('Attempting to connect to %s on port %s' % (self.server_ip, self.server_port))
        self.socket.connect((self.server_ip, self.server_port))
        print('Connected to %s on port %s' % (self.server_ip, self.server_port))
        threading.Thread(target=self.socket_thread).start()

    def shutdown(self):
        self.should_shutdown = True



if __name__=='__main__':
    print('Starting camera...')
    #cc = CameraClient(basics={'name':'C1','left':'c2','right':'c3,c4'})
    cc = CameraClient()
    while True:
        inpt = input()
        if (inpt == 'l'):
            cc.left_screen_alert(CameraClient.LEFT)
        elif (inpt == 'r'):
            cc.left_screen_alert(CameraClient.RIGHT)
        elif (inpt == 'q'):
            cc.shutdown()
            break



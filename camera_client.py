#!/usr/bin/python3
import socket
import threading
import sys
import pickle


class CameraClient():
    CONFIG_FILE = 'camera.cfg'

    def __init__(self, cfg=CONFIG_FILE, basics=None):
        if basics is not None:
            self.server_ip = '0.0.0.0'
            self.server_port = int(sys.argv[1])
            self.name = basics['name']
            self.left = basics['left']
            self.right = basics['right']
        else:
            self.initialize_with_file(cfg)

        self.socket = socket.socket()
        self.open_connection()

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
        self.socket.send(pickle.dumps(info))
        print(str(self.socket.recv(2048), 'utf-8'))
        while True:
            msg = pickle.loads(self.socket.recv(2048))
            if (msg != ''):
                print(msg)
        self.socket.close()

    def open_connection(self):
        print('Attempting to connect to %s on port %s' % (self.server_ip, self.server_port))
        self.socket.connect((self.server_ip, self.server_port))
        print('Connected to %s on port %s' % (self.server_ip, self.server_port))
        threading.Thread(target=self.socket_thread).start()



if __name__=='__main__':
    print('Starting camera...')
    cc = CameraClient(basics={'name':'C1','left':'c2','right':'c3,c4'})
    '''
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
    '''
    

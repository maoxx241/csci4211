#auther: Qi Mao
#X.500: maoxx241
#ID: 5306940
#Date: 4/21/2019
#this file is using for P2P server, please run this file using command: python3 server.py 900x
#x can be any number during 1 to 9.
from socket import *
from _thread import *
import sys
import os

# lock for
# socket_lock = threading.Lock()

meta_server_ip = '127.0.0.1'
my_ip = '127.0.0.1'
meta_server_port = 12000
serverPort = int(sys.argv[1])
serverSocket = socket(AF_INET, SOCK_STREAM)
# create server
serverSocket.bind((meta_server_ip, serverPort))
serverSocket.listen(5)
print("The server is ready to receive")

connections = []

assign_ip = None
id = None


def register_to_server():
    global assign_ip
    global id
    # global serverSocket
    print('Try to connect to meta-server')
    meta_socket = socket(AF_INET, SOCK_STREAM)
    meta_socket.connect((meta_server_ip, meta_server_port))
    meta_socket.send(str([meta_server_ip, serverPort]).encode())
    print('Connect successfully')
    if id is None:
        id = input('Please input ID of server: ')
        if len(id) == 0:
            print('You can not use empty string as id')
            exit()
        try:
            os.makedirs(id)
        except:
            os.chdir(id)

    topo = input('To(Not to) view the P2P network topology, type TOPO(any other string): ')
    if topo == 'TOPO':
        # ask the server to print the network topology
        print('Input ' + topo)
        meta_socket.send('TOPO'.encode())
        while True:
            data = meta_socket.recv(1024).decode()
            if not data:
                continue
            print(str(''.join(data)))
            break

    flag = input('Please input flag to connect P2P network(use \'EXIT\' to quit): ')
    while True:
        print('FLAG ' + flag)
        if flag == 'TOPO':
            print('Invalid flag')
            flag = input('Please re-input flag to connect P2P network: ')
            continue
        elif flag == 'EXIT':
            meta_socket.send('EXIT'.encode())
            meta_socket.close()
            return

        meta_socket.send(flag.encode())
        data = ''.join(meta_socket.recv(1024).decode())
        if data.startswith('***'):
            print(data)
            flag = input('Please re-input flag to connect P2P network: ')
        elif data == 'Register already':
            print(data)
            meta_socket.close()
            return
        else:
            data = list(eval(data))
            meta_socket.close()
            break
    assign_ip = data[0]
    if data[1] == meta_server_ip and int(data[2]) == serverPort:
        # first one, finish
        print('Join to the P2P network successfully(FIRST)')
        return

    while True:
        print('Try to connect to network')
        meta_socket = socket(AF_INET, SOCK_STREAM)
        remote_port = int(data[2])
        meta_socket.connect((data[1], remote_port))
        # meta_socket.send(str([meta_server_ip, serverPort]).encode())
        # meta_socket.recv(1024).decode()
        meta_socket.send(str({
            'opt': 'CONNECT',
            'data': [assign_ip, meta_server_ip, serverPort]
        }).encode())
        data = ''.join(meta_socket.recv(1024).decode())
        if data.startswith('SUCCESS'):
            connections.append([data.replace('SUCCESS', ''), meta_server_ip, remote_port])
            break
        data = list(eval(data))
    print('Join to the P2P network successfully')
    meta_socket.close()


def download_file():
    if len(connections) == 0:
        print('You are not connect to the p2p network!')
        return

    filename = input('Please input the filename you want:')
    # second node is special
    if assign_ip == '192.168.0.3':
        right_socket = socket(AF_INET, SOCK_STREAM)
        right_socket.connect((connections[0][1], connections[0][2]))
        right_socket.send(str({
            'opt': 'FILE',
            'data': filename,
            'request_ip': my_ip,
            'request_port': serverPort,
            'from_server': id,
            'is_left': False
        }).encode())
    else:
        left_socket = socket(AF_INET, SOCK_STREAM)
        left_socket.connect((connections[0][1], connections[0][2]))
        left_socket.send(str({
            'opt': 'FILE',
            'data': filename,
            'request_ip': my_ip,
            'request_port': serverPort,
            'from_server': id,
            'is_left': True
        }).encode())

        if len(connections) > 1:
            right_socket = socket(AF_INET, SOCK_STREAM)
            right_socket.connect((connections[1][1], connections[1][2]))
            right_socket.send(str({
                'opt': 'FILE',
                'data': filename,
                'request_ip': my_ip,
                'request_port': serverPort,
                'from_server': id,
                'is_left': False
            }).encode())


def run_server_thread():
    global assign_ip
    global id
    while True:
        connectionSocket, addr = serverSocket.accept()
        print('Connection establish: ' + str(addr))
        data = dict(eval(''.join(connectionSocket.recv(1024).decode())))
        print('Receive Data: ' + data.get('opt'))
        if data.get('opt') == 'CONNECT':
            addr = data.get('data')
            print(addr)
            if len(connections) == 2:
                connectionSocket.send(str(connections[1]).encode())
            else:
                # check the first node
                if assign_ip == '192.168.0.1' and len(connections) == 1:
                    connections.insert(0, addr)
                else:
                    connections.append(addr)
                connectionSocket.send(('SUCCESS' + assign_ip).encode())
            print('Connection List: ' + str(connections))
        elif data.get('opt') == 'TOPO':
            print('Connection List: ' + str(connections))
            connectionSocket.send(str({'info': assign_ip, 'details': connections}).encode())
        elif data.get('opt') == 'FILE':
            # print
            print('***Received Request Server ' + str(data['request_ip']) + ':' + str(
                data['request_port']) + ':' + data['data'] + ' from ' + data['from_server'] + '***')

            if os.path.exists(data.get('data')):
                return_socket = socket(AF_INET, SOCK_STREAM)
                return_socket.connect((data['request_ip'], data['request_port']))
                transfer_file(return_socket, data.get('data'))
            else:
                # go left
                if data.get('is_left'):
                    if assign_ip == '192.168.0.3':
                        return_socket = socket(AF_INET, SOCK_STREAM)
                        return_socket.connect((data['request_ip'], data['request_port']))
                        return_socket.send(str({
                            'opt': 'FILE_RESULT',
                            'data': 'Failed to find File from left'
                        }).encode())
                        return_socket.close()
                    else:
                        left_socket = socket(AF_INET, SOCK_STREAM)
                        left_socket.connect((connections[0][1], connections[0][2]))
                        left_socket.send(str({
                            'opt': 'FILE',
                            'data': data['data'],
                            'request_ip': data['request_ip'],
                            'request_port': data['request_port'],
                            'from_server': id,
                            'is_left': True
                        }).encode())
                        left_socket.close()
                # go right
                else:
                    if len(connections) <= 1:
                        return_socket = socket(AF_INET, SOCK_STREAM)
                        return_socket.connect((data['request_ip'], data['request_port']))
                        return_socket.send(str({
                            'opt': 'FILE_RESULT',
                            'data': 'Failed to find File from right'
                        }).encode())
                        return_socket.close()
                    else:
                        right_socket = socket(AF_INET, SOCK_STREAM)
                        right_socket.connect((connections[1][1], connections[1][2]))
                        right_socket.send(str({
                            'opt': 'FILE',
                            'data': data['data'],
                            'request_ip': data['request_ip'],
                            'request_port': data['request_port'],
                            'from_server': id,
                            'is_left': False
                        }).encode())
                        right_socket.close()
        elif data.get('opt') == 'FILE_RESULT':
            print(data['data'])
        elif data.get('opt') == 'TRANSFER':
            print('Find file at ' + data['id'])
            if not os.path.exists(data['filename']):
                with open(data['filename'], 'w') as f:
                    f.write(data.get('data'))
                print('file transfer complete')
            else:
                print('filename exist')

        connectionSocket.close()


def transfer_file(socket, filename):
    with open(filename, 'r') as f:
        part = f.read()
        result = str({
            'opt': 'TRANSFER',
            'data': part,
            'filename': filename,
            'id': id
        })
    socket.send(result.encode())
    socket.close()


start_new_thread(run_server_thread, ())

while True:
    opt = input('Choose operation: \r\n 1: Register into P2P network \r\n 2: Download a file\r\n 3: Exit\r\n')
    opt = int(opt)
    if opt == 1:
        register_to_server()
    elif opt == 2:
        download_file()
    elif opt == 3:
        break
    else:
        print('Invalid input')
print('***Server Terminal***')

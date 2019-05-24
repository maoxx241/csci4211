#auther: Qi Mao
#X.500: maoxx241
#ID: 5306940
#Date: 4/21/2019
#this file is using for meta_server, please run this file first

from socket import *
from _thread import *
import threading

VALID_FLAG = "P2P"
TOPO_FLAG = "TOPO"
EXIT_FLAG = "EXIT"
FILE_FLAG = "FILE"
# create lock to support multi_thread
# # socket_lock = threading.Lock()

ip_table = []
"""
record the index of ip
// if the topology of network is record, it will be much easier
// and its child to find the next target
"""
ip_map = dict()

# by default we allow 254 machines to register on meta-server
assign_ip_prefix = "192.168.0."
begin_ip = 0

assign_ip_map = dict()


def socket_thread(connect, addr):
    global begin_ip
    addr = list(eval(''.join(connect.recv(1024).decode())))
    print('Addr ', addr)
    full_addr = addr[0] + ":" + str(addr[1])
    print("***Connected to " + full_addr + "***")

    # cur_try_connect_ip = None
    while True:
        data = connect.recv(1024).decode()
        # lock when transaction begin
        # socket_lock.acquire()
        if not data:
            # release lock & exit
            # socket_lock.release()
            continue
        data = ''.join(data)
        print('Receive data', data)
        # check flag
        if data == VALID_FLAG:
            if full_addr in ip_map.keys():
                connect.send('Register already'.encode())
                connect.close()
                continue
            # check already allocate referred ip, if so, skip this
            # if full_addr not in referred_ip_map.keys():
            # allocate referred ip
            begin_ip = begin_ip + 1
            if begin_ip > 254:
                connect.send('*****Connection Overflow*****'.encode())
                break
            # update ip
            assign_ip = assign_ip_prefix + str(begin_ip)
            assign_ip_map.setdefault(assign_ip, full_addr)
            print('Request ', full_addr, ': ', '***Valid Flag*** ')
            # if is the first machine, add to map and return itself
            # connection established
            ip_map.setdefault(full_addr, len(ip_table))
            ip_table.append(full_addr)
            # send back to server with the first-try server ip
            #  <IP, Referred IP, Port Number>
            first = ip_table[0].split(':')
            connect.send(str([assign_ip, first[0], first[1]]).encode())
            break
        elif data == TOPO_FLAG:
            print('Received TOPO Request')
            topo = 'EMPTY'
            print(ip_table, ' ', len(ip_table))
            if len(ip_table) > 0:
                # the first node is special.
                first_ip = ip_table[0].split(':')
                topo_socket = socket(AF_INET, SOCK_STREAM)
                topo_socket.connect((first_ip[0], int(first_ip[1])))
                topo_socket.send(str({
                    'opt': TOPO_FLAG
                }).encode())
                first_data = dict(eval(''.join(topo_socket.recv(1024).decode())))
                print(first_data)
                topo = first_data.get('info')
                # connection nodes of first node.
                children = first_data.get('details')
                topo_socket.close()
                print(children)
                if len(children) == 0:
                    connect.send(topo.encode())
                    # socket_lock.release()
                    continue
                # in fact if the first node only has one node, no need to iterate
                topo = children[0][0] + '<->' + topo
                if len(children) == 1:
                    connect.send(topo.encode())
                    continue
                next_node = children[1][0]
                while next_node is not None:
                    # append current node
                    topo += '<->' + next_node
                    # get the real ip
                    print(next_node)
                    next_node_addr = assign_ip_map.get(next_node)
                    next_node_ip = next_node_addr.split(':')
                    # try to get its details
                    topo_socket = socket(AF_INET, SOCK_STREAM)
                    topo_socket.connect((next_node_ip[0], int(next_node_ip[1])))
                    topo_socket.send(str({
                        'opt': TOPO_FLAG
                    }).encode())
                    first_data = dict(eval(''.join(topo_socket.recv(1024).decode())))
                    # connection nodes of first node.
                    children = first_data.get('details')
                    # check any need to go on
                    if len(children) == 2:
                        next_node = children[1][0]
                    else:
                        next_node = None
                        topo_socket.close()
            connect.send(topo.encode())
        elif data == EXIT_FLAG:
            break
        else:
            print('Request ', full_addr, ': ', '*****Invalid Flag*****')
            connect.send('*****Invalid Flag*****'.encode())
        # socket_lock.release()
    # if # socket_lock.locked():
    # socket_lock.release()
    connect.close()


# create server
serverPort = 12000
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('127.0.0.1', serverPort))
serverSocket.listen(5)
print("The server is ready to receive")
while True:
    connectionSocket, addr = serverSocket.accept()
    print('Connection establish: ' + str(addr))
    # # socket_lock.acquire()
    start_new_thread(socket_thread, (connectionSocket, addr,))

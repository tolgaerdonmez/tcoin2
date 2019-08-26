from .blockchain import Blockchain, Block
from .transaction import Transaction
from .wallet import Wallet, WALLET_CHAIN, NEW_TX
import socket
import select
import threading
from multiprocessing import Process
import time
import json
import pickle
from queue import LifoQueue

JOIN_MSG = 'JOIN_TCOIN_BLOCKCHAIN'
JOIN_INTERVAL = 5
NEW_BLOCK = 'NEW_TCOIN_BLOCK'
GET_CHAIN = 'GET_CHAIN'
SEND_CHAIN_INTERVAL = 25
HEADER_LENGTH = 1000

class NodeClient(socket.socket):

    def __init__(self):
        super().__init__(socket.AF_INET,socket.SOCK_STREAM)

    def connect_node(self, conn_addr, node_addr):
        try:
            super().connect(conn_addr)
            # self.setblocking(True)
            
            join_msg = [JOIN_MSG,node_addr]
            join_msg = pickle.dumps(join_msg)
            msg = f"{len(join_msg):<{HEADER_LENGTH}}".encode() + join_msg
            self.send(msg)
            return True
        except:
            return False
            
    def send_chain(self, node_addr, conn_addr, chain):
        try:
            super().connect(conn_addr)

            pickled_chain = pickle.dumps(chain)
            chain_msg = [GET_CHAIN,node_addr,pickled_chain]
            chain_msg = pickle.dumps(chain_msg)
            msg = f"{len(chain_msg):<{HEADER_LENGTH}}".encode() + chain_msg
            self.send(msg)
            return True
        except:
            return False
    
    def send_block(self, node_addr, conn_addr, block):
        try:
            super().connect(conn_addr)

            pickled_block = pickle.dumps(block)
            chain_msg = [NEW_BLOCK, node_addr, pickled_block]
            chain_msg = pickle.dumps(chain_msg)
            msg = f"{len(chain_msg):<{HEADER_LENGTH}}".encode() + chain_msg
            self.send(msg)
        except:
            pass

class Node(socket.socket):

    def __init__(self, ip, port, is_miner = False):
        # __init__ Socket
        self.IP = ip
        self.PORT = port

        super().__init__(socket.AF_INET,socket.SOCK_STREAM)
        self.bind((self.IP, self.PORT))
        self.listen()
        
        # __init__ Node
        self.threads = {}
        self.sending_chain = False
        self.incoming_clients = LifoQueue()

        # loading if already a blockchain exists
        loaded_chain = Blockchain.load_blockchain((self.IP,self.PORT))
        if loaded_chain:
            self.blockchain = loaded_chain
        else:
            # creating new blockchain
            self.blockchain = Blockchain(self)

        self.is_miner = is_miner
        if self.is_miner:
            self.wallet = Wallet.optioned_create_wallet()

        # INIT METHODS
        if self.blockchain.loaded:
            self.__connect_nodes()

        # Starting threads
        self.new_job(target=self.get_clients)
        self.new_job(target=self.communucate_nodes)
        self.new_job(target=self.send_chain)
        if self.is_miner:
            self.new_job(target=self.mine_block)

    def mine_block(self):
        while True:
            if len(self.blockchain.current_transactions) <= 5:
                continue
            self.blockchain.create_block(self.wallet.pu_ser)
            for node in self.blockchain.current_nodes:
                client = NodeClient()
                client.send_block(node_addr = (self.IP,self.PORT), conn_addr = node, block = self.blockchain.last_block())
        
    def get_data(self, socket):
        msg_list = []
        while True:
            header = socket.recv(HEADER_LENGTH)
            if not header:
                break
            node_msg = socket.recv(int(header))
            node_msg = pickle.loads(node_msg)
            if type(node_msg) == type([]):
                msg_list.append(node_msg)
            if node_msg[0] == WALLET_CHAIN or node_msg[0] == NEW_TX:
                break
        if len(msg_list) > 0:
            return msg_list
        else:
            return False
    
    def get_clients(self):
        time.sleep(2)
        while True:
            node_client_socket,addr = self.accept()
            print(addr)
            self.incoming_clients.put(node_client_socket)
    
    def communucate_nodes(self):
        ram_chains = {}
        while True:
            if self.incoming_clients.empty():
                continue
            # for node_client in self.incoming_clients:
            node_client = self.incoming_clients.get()
            # receiving join message and node addr
            node_msg = self.get_data(node_client)
            if not node_msg:
                continue

            msg_header = node_msg[0][0]
            print('communicating nodes'.capitalize(), msg_header)
            if msg_header == JOIN_MSG:
                for msg in node_msg:
                    node_addr = msg[1]
                    # if node is online => add to node list
                    self.blockchain.current_nodes.add(tuple(node_addr))
                    print(f"New node connected to blockchain!\n Node Address: {node_addr[0]}:{node_addr[1]}")
            elif msg_header == NEW_BLOCK:
                for msg in node_msg:
                    new_block = msg[2]
                    new_block = pickle.loads(new_block)
                    chain = self.blockchain.chain.copy()
                    chain.append(new_block)
                    check = Blockchain.check_chain(chain)
                    if check:
                        print('New Block received!')
                        self.blockchain.chain.append(new_block)
            # GET_CHAIN gets chain around a period of time from other nodes for replacing
            elif msg_header == GET_CHAIN:
                for msg in node_msg:
                    loaded_chain = pickle.loads(msg[2])
                    if not msg[1] in ram_chains:
                        ram_chains[msg[1]] = loaded_chain
                    print('chain got from: ', msg[1])
                    print('ram chain length ', len(ram_chains.values()))
                    if len(ram_chains) == (len(self.blockchain.current_nodes) - 1):
                        self.blockchain.replace_chain(ram_chains.values())
                        ram_chains = {} 

            elif msg_header == WALLET_CHAIN:
                pickled_chain = pickle.dumps(self.blockchain.chain)
                data = f"{len(pickled_chain):<{HEADER_LENGTH}}".encode() + pickled_chain
                node_client.send(data)
                if self.blockchain.last_block() != None : print(self.blockchain.last_block().hash)

            elif msg_header == NEW_TX:
                for msg in node_msg:
                    new_tx = pickle.loads(msg[1])
                    tx = Transaction.from_dict(new_tx)
                    verify = Wallet.verify(tx)
                    if verify:
                        self.blockchain.current_transactions.append(new_tx)
                        print('New TX !')
                    else:
                        print('Invalid transaction !')
                    
            node_client.close()
            
    def pop_nodes(self,nodes):
        for node in nodes:
            self.blockchain.current_nodes.remove(node)

    def send_chain(self):
        while True:
            time.sleep(SEND_CHAIN_INTERVAL)
            if len(self.blockchain.current_nodes) - 1 == 0:
                continue
            excep_nodes = []
            all_nodes = self.blockchain.current_nodes
            for (ip,port) in all_nodes:
                if (ip,port) != (self.IP,self.PORT):
                    try:
                        client = NodeClient()
                        client.send_chain(node_addr = (self.IP,self.PORT), conn_addr = (ip,port),chain = self.blockchain.chain)
                        print('sending chain to: ', ip, port)
                        client.close()
                    except:
                        excep_nodes.append((ip,port)) # this is gonna stay for a while, but actually it is smthg we do not need to happen (losing nodes)
            self.pop_nodes(excep_nodes)

    def __connect_nodes(self):
        excep_nodes = []
    
        for (ip,port) in self.blockchain.current_nodes:
            if (ip,port) != (self.IP,self.PORT):
                try:
                    client = NodeClient()
                    client.connect_node((ip,port),(self.IP,self.PORT))
                except:
                    excep_nodes.append((ip,port))
        self.pop_nodes(excep_nodes)
        self.blockchain.current_nodes.add((self.IP,self.PORT))

    def new_job(self, target, args = (), daemon = False):
        t = threading.Thread(target=target, args = args)
        self.threads[target] = t
        t.daemon = daemon
        t.start()

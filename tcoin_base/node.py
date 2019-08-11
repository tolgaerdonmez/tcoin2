from .blockchain import Blockchain, Block
import socket
import select
import threading
import time
import json
import pickle

JOIN_MSG = 'JOIN_TCOIN_BLOCKCHAIN'
JOIN_INTERVAL = 5
NEW_BLOCK_MSG = 'NEW_TCOIN_BLOCK'
GET_CHAIN = 'GET_CHAIN'
SEND_CHAIN_INTERVAL = 10

class NodeClient(socket.socket):

    def __init__(self):
        super().__init__(socket.AF_INET,socket.SOCK_STREAM)

    def connect_node(self, conn_addr, node_addr):
        super().connect(conn_addr)
        self.setblocking(False)
        try:
            join_msg = [JOIN_MSG,node_addr]
            join_msg = pickle.dumps(join_msg)
            self.send(join_msg)
            return True
        except:
            return False
            
    def send_chain(self, conn_addr, chain):
        print(f"sending chain to {conn_addr}")
        super().connect(conn_addr)

        try:
            pickled_chain = pickle.dumps(chain)
            chain_msg = [GET_CHAIN,conn_addr,pickled_chain]
            chain_msg = pickle.dumps(chain_msg)
            self.send(chain_msg)
            return True
        except:
            return False
    
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
        self.is_miner = is_miner
        self.sending_chain = False

        # loading if already a blockchain exists
        loaded_chain = False#Blockchain.load_blockchain((self.IP,self.PORT))
        if loaded_chain:
            self.blockchain = loaded_chain
        else:
            # creating new blockchain
            self.blockchain = Blockchain(self)

        # INIT METHODS
        if self.blockchain.loaded:
            self.__connect_nodes()

        # Starting threads
        self.new_job(target=self.communucate_nodes)
        self.new_job(target=self.send_chain)
        # if self.is_miner:
        #     self.new_job(target=self.mine_block)

    def mine_block(self):
        while True:
            self.blockchain.create_block((self.IP,self.PORT))
            print('\n\nNew Block Created')
            # print(self.blockchain.last_block(),'\n\n')
            time.sleep(1)

    def get_data(self, socket):
        node_msg = socket.recv(1024 * 1024)
        node_msg = pickle.loads(node_msg)
        return node_msg
    
    def communucate_nodes(self):
        ram_chains = {}
        while True:
            # r,_,_ = select.select([self], [], [self])
            # for node in r:
            #     if node == self:
            node_client_socket,_ = self.accept()
            # receiving join message and node addr
            node_msg = self.get_data(node_client_socket)
            if node_msg[0] == JOIN_MSG:
                node_addr = node_msg[1]
                # if node is online => add to node list
                self.blockchain.current_nodes.add(tuple(node_addr))
                print(f"New node connected to blockchain!\n Node Address: {node_addr[0]}:{node_addr[1]}")

            elif node_msg[0] == GET_CHAIN:
                loaded_chain = pickle.loads(node_msg[2])
                if not node_msg[1] in ram_chains:
                    ram_chains[node_msg[1]] = loaded_chain
                if len(ram_chains) == (len(self.blockchain.current_nodes) - 1):
                    self.blockchain.replace_chain(ram_chains.values())
                    ram_chains = {}

    def pop_nodes(self,nodes):
        for node in nodes:
            self.blockchain.current_nodes.remove(node)

    def send_chain(self):
        while True:
            time.sleep(SEND_CHAIN_INTERVAL)

            excep_nodes = []
            print("Sending Chain...")
            self.sending_chain = True
            all_nodes = self.blockchain.current_nodes
            for (ip,port) in all_nodes:
                if (ip,port) != (self.IP,self.PORT):
                    try:
                        client = NodeClient()
                        client.send_chain((ip,port),self.blockchain.chain)
                    except:
                        excep_nodes.append((ip,port))
            self.sending_chain = False
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

    def new_job(self, target, args = None, daemon = False):
        t = threading.Thread(target=target)
        self.threads[target] = t
        if args != None:
            t.args = args
        t.daemon = daemon
        t.start()
    
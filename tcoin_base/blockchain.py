import hashlib
import datetime
import time
import pickle
import json

def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print (f'{(te - ts)} ms')
        return result
    return timed

class Block():

    def __init__(self, index = 0, previous_hash = 0, transactions = [], nodes = [], miner = None):
        self.index = index
        self.prev_hash = previous_hash
        self.transactions = transactions
        self.timestamp = None#str(datetime.datetime.now())
        self.nodes = nodes
        self.miner = miner
        self.proof = None
        self.hash = None#self.calc_hash()

    def calc_hash(self):
        self.timestamp = str(datetime.datetime.now())
        encoded_block = (str(self.index) + self.timestamp + self.prev_hash + str(self.transactions) + str(self.nodes)).encode()
        hash = hashlib.sha256(encoded_block).hexdigest()
        self.hash = hash
        return hash

    def __str__(self):
        string = f"index: {self.index}\n hash: {self.hash}\n previous_hash: {self.prev_hash}\n transactions: {str(self.transactions)}\n nodes: {str(self.nodes)}\n proof: {self.proof}\n miner: {self.miner}"
        return string

    def dict(self):
        dict = {'index':self.index, 'timestamp':self.timestamp, 'miner':self.miner, 'hash':self.hash, 'prev_hash': self.prev_hash, 'proof':self.proof, 'nodes':list(self.nodes), 'transactions':self.transactions}
        return dict

DIFFICULTY = '0000'

class Blockchain():

    def __init__(self, node):
        # if node is not in the network then it is loaded
        self.loaded = False
        self.chain = []
        self.current_transactions = []
        # dict of node_socket:node_addr 
        self.current_nodes = {(node.IP,node.PORT)}
    
    @staticmethod
    def load_blockchain(cur_node):
        def is_loaded(cur_node, nodes):
            for node in nodes:
                if cur_node == node:
                    return False
            return True
        # loads a blockchain, if already exists
        try:
            with open('blockchain','rb') as file:
                loaded_chain = pickle.load(file)
                loaded_chain.loaded = is_loaded(cur_node, loaded_chain.current_nodes)
                return loaded_chain
        except:
            return False
        # self.loaded = True
    
    def save_blockchain(self):
        with open('blockchain','wb') as file:
            pickle.dump(self, file)

    def create_block(self, miner):
        # if creating genesis block
        if len(self.chain) == 0:
            prev_hash = ''
        else:
            prev_hash = self.last_block().hash

        new_block = Block(
            index = len(self.chain) + 1,
            previous_hash = prev_hash,
            transactions = self.current_transactions,
            nodes = self.current_nodes,
            miner = miner
        )
        
        # clearing current transcation pool
        self.current_transactions = []
        
        # doing proof of work (a.k.a mining)
        new_block.hash, new_block.proof = self.proof_of_work(new_block)
        
        self.chain.append(new_block)
        print(new_block)
        self.save_blockchain()

    def last_block(self):
        if len(self.chain) == 0:
            return None
        return self.chain[-1]
    
    # @timeit
    def proof_of_work(self, block):
        proof = 0
        proofed = False
        while not proofed:
            block.calc_hash()
            hash = hashlib.sha256((block.hash + str(block.miner) + str(proof)).encode()).hexdigest()
            if hash[:len(DIFFICULTY)] == DIFFICULTY:
                proofed = True
                return block.hash, proof
            else:
                proof += 1
    
    @staticmethod
    def check_chain(chain):
        # checking chain integrity
        index = 1
        while index<len(chain):
            block = chain[index]
            prev_block = chain[index-1]
            # 1. checking proof of work
            fresh_hash = (str(block.index) + block.timestamp + block.prev_hash + str(block.transactions) + str(block.nodes)).encode()
            fresh_hash = hashlib.sha256(fresh_hash).hexdigest()
            proof_hash = hashlib.sha256((fresh_hash + str(block.miner) + str(block.proof)).encode()).hexdigest()
            if proof_hash[:len(DIFFICULTY)] != DIFFICULTY:
                return False
            # 2. checking hash bonds
            if block.prev_hash != prev_block.hash:
                return False
            index += 1

        # if no inconsistency 
        return True
    
    def replace_chain(self, chains):
        longest_chain = None
        max_length = len(self.chain)
        for cur_chain in chains:
            length = len(cur_chain)
            if length > max_length and Blockchain.check_chain(cur_chain):
                max_length = length
                longest_chain = cur_chain
        # if the longest_chain is not none
        if longest_chain:
            self.chain = longest_chain
            print("Chain Replaced with the longest chain !")
        else:
            print("No need for replacing")
    
    def __str__(self):
        string = ''
        for block in self.chain:
            string += str(block) + '\n'
        return string

    def dict(self):
        dict = {'chain':[],'length':len(self.chain)}
        for block in self.chain:
            dict_tx = []
            for tx in block.transactions:
                print(tx)
                dict_tx.append(tx.dict())
            block.transactions = dict_tx
            dict['chain'].append(block.dict())
        print(dict)
        return dict
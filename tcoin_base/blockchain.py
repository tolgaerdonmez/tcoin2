import hashlib
import datetime
import time
import pickle

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
        self.timestamp = str(datetime.datetime.now())
        self.nodes = nodes
        self.miner = miner
        self.proof = None
        self.hash = self.calc_hash()

    def calc_hash(self):
        encoded_block = (str(self.index) + self.timestamp + self.prev_hash + str(self.transactions) + str(self.nodes)).encode()
        hash = hashlib.sha256(encoded_block).hexdigest()
        return hash

    def __str__(self):
        string = f"index: {self.index}\n hash: {self.hash}\n previous_hash: {self.prev_hash}\n transactions: {str(self.transactions)}\n nodes: {str(self.nodes)}\n proof: {self.proof}\n miner: {self.miner}"
        return string

class Blockchain():

    def __init__(self, node):
        # if node is not in the network then it is loaded
        self.loaded = False
        self.chain = []
        self.current_transactions = []
        # dict of node_socket:node_addr 
        self.current_nodes = {(node.IP,node.PORT)}
        self.difficulty = '0000'
    
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
        new_block.proof = self.proof_of_work(new_block)
        
        self.chain.append(new_block)

        # self.save_blockchain()

    def last_block(self):
        return self.chain[-1]
    
    # @timeit
    def proof_of_work(self, block):
        proof = 0
        proofed = False
        while not proofed:
            hash = hashlib.sha256((block.hash + str(block.miner) + str(proof)).encode()).hexdigest()
            if hash[:len(self.difficulty)] == self.difficulty:
                proofed = True
                return proof
            else:
                proof += 1

    def check_chain(self,chain):
        # checking chain integrity
        index = 1
        while index<len(chain):
            block = chain[index]
            prev_block = chain[index-1]
            # 1. checking proof of work
            fresh_hash = block.calc_hash()
            proof_hash = hashlib.sha256((fresh_hash + str(block.miner) + str(block.proof)).encode()).hexdigest()
            if proof_hash[:len(self.difficulty)] != self.difficulty:
                return False
            # 2. checking hash bonds
            if block.prev_hash != prev_block.hash:
                return False
            index += 1

        # if no inconsistency 
        return True
    
    def replace_chain(self,chains):
        longest = self.chain
        for cur_chain in chains:
            if len(cur_chain) > len(longest) and self.check_chain(cur_chain):
                longest = cur_chain
        if len(longest) > len(self.chain):
            self.chain = longest
            print("Chain Replaced with the longest chain !")
        else:
            print("No need for replacing")
           

            
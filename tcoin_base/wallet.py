from .transaction import Transaction
from .blockchain import Blockchain
from functools import wraps
import rsa
import hashlib
import socket
import pickle
import threading
import time
import sys
import errno, json
# rsa.key.PrivateKey._save_pkcs1_pem() => saves key like -----BEGIN RSA PRIVATE KEY-----
# rsa.key.PrivateKey._load_pkcs1_pem(data) => loads key from like -----BEGIN RSA PRIVATE KEY-----
WALLET_CHAIN = 'WALLET_CHAIN'
NEW_TX = 'NEW_TX'
HEADER_LENGTH = 1000

class WClient(socket.socket):

    def __init__(self, conn_addr):
        super().__init__(socket.AF_INET,socket.SOCK_STREAM)
        super().connect(conn_addr)
        self.setblocking(False)

    def connect_blockchain(self):
        
        message = [WALLET_CHAIN]
        message = pickle.dumps(message)
        message = f"{len(message):<{HEADER_LENGTH}}".encode() + message
        self.send(message)
        while True:
            try:
                while True:
                    # receive things
                    header = self.recv(HEADER_LENGTH)
                    if not len(header):
                        print("Connection closed by the blockchain node")
                        sys.exit()
                    length = int(header.decode())
                    data = self.recv(length)
                    chain = pickle.loads(data)
                    # with open('s.json','w') as f:
                    #     json.dump(chain.dict(),f,indent=4)
                    check = Blockchain.check_chain(chain)
                    if len(chain) == 0:
                        pass
                    else:
                        for block in chain:
                            print(block.hash)
                        print(len(chain))
                    if check:
                        return chain
                    else:
                        return False               
            except IOError as e:
                if e.errno != errno.EAGAIN or e.errno != errno.EWOULDBLOCK:
                    print('Read Error !',str(e))
                    self.close()
                    return False
                else:
                    continue
        self.close()

    @staticmethod
    def connect(node_addr):
        one_client = WClient(node_addr)
        is_connected = one_client.connect_blockchain()

        if is_connected != False and type(is_connected) == type(list()):
            print('Connected to Blockchain ! Ready to go !')
            chain = is_connected
            return chain
        else:
            print('Try to connect another blockchain node...')
            sys.exit()

    @staticmethod
    def send_tx(node_addr, tx_data):
        one_client = WClient(node_addr)
        one_client.send(tx_data)
        one_client.close()

class Wallet():

    def __init__(self, node_addr = tuple(), pr = None, pu = None):
        # __init__ Wallet
        self.__BITS = 2048
        self.node_addr = node_addr
        print('Connecting to TCOIN BLOCKCHAIN...')
        # if loaded
        if pr != None:
            self.public, self.private = pu, pr
            print('Your Wallet has been loaded')
        else: # if not loaded creating new keys
            self.public, self.private = rsa.newkeys(self.__BITS)
            print('Your Wallet has been created')

        self.pu_ser = (rsa.pem.save_pem(self.public._save_pkcs1_pem(),'RSA PUBLIC KEY')).decode()
        
        # connect to blockchain if node_addr is given
        if len(self.node_addr) != 0:
            self.connect_blockchain()

    def connect_blockchain(self):
        self.chain = WClient.connect(self.node_addr)
        
    def calculate_coins(self):
        total = 0
        plus = 0
        minus = 0
        for block in self.chain:
            for tx_dict in block.transactions:
                tx = Transaction.from_dict(tx_dict)
                if tx.sender == self.pu_ser:
                    minus += tx.input
                if tx.receiver == self.pu_ser:
                    plus += tx.output
        total = plus - minus
        print(plus,minus)
        return total

    def sign(self, tx):
        # if self.calculate_coins(self.chain) - tx[0][1] < 0:
        #     return None, False
        # else:
        tx = str(tx)
        sig = rsa.sign(tx.encode(), self.private, 'SHA-256')
        return sig, True

    def send_tx(self, receiver_pu, amount, tx_fee):
        new_tx = Transaction(
            sender = self.pu_ser,
            receiver = receiver_pu,
            input = amount + tx_fee,
            output = amount
        )
        sig, signed = self.sign(new_tx.gather())
        if signed:
            new_tx.sig = sig
            new_tx = new_tx.dict()
            pickled_tx = pickle.dumps(new_tx)
            tx_data = [NEW_TX, pickled_tx]
            tx_data = pickle.dumps(tx_data)
            data = f"{len(tx_data):<{HEADER_LENGTH}}".encode() + tx_data
            try:
                # creating a new WClient and sending new tx
                WClient.send_tx(self.node_addr, data)
                print('sending tx...')
                return True
            except:
                return False
        else:
            return False

    # saves private key to .pem file
    def save_wallet_pem(self, file_path = './'):
        try:
            with open(file_path + 'pr_key.pem','wb') as pem_file:
                pr_key = rsa.pem.save_pem(self.private._save_pkcs1_pem(),'RSA PRIVATE KEY')
                pem_file.write(pr_key)
            with open(file_path + 'pu_key.pem','wb') as file:
                pu_key = rsa.pem.save_pem(self.public._save_pkcs1_pem(),'RSA PUBLIC KEY')
                file.write(pu_key)
        except:
            return False

    def new_job(self, target, args = (), daemon = False):
        t = threading.Thread(target=target, args = args)
        t.daemon = daemon
        t.start()

    @staticmethod
    def verify(tx):
        # tx obj of class Transaction
        public_key = rsa.pem.load_pem(tx.sender,'RSA PUBLIC KEY')
        public_key = rsa.PublicKey.load_pkcs1(public_key)
        sig = tx.sig
        data = str(tx.gather()).encode()
        # rsa.verify returns the data encryption type it's sha256 for us
        try:
            rsa.verify(data, sig, public_key)
            return True
        except rsa.VerificationError:
            return False
    
    # loads private key from .pem file
    @staticmethod
    def load_wallet_pem(node_addr = tuple(), file_path = './'):
        try:
            with open(file_path + 'pr_key.pem','rb') as pem_key:
                private_key = rsa.pem.load_pem(pem_key.read(),'RSA PRIVATE KEY')
                private_key = rsa.key.PrivateKey._load_pkcs1_pem(private_key)
        except:
            return False
        public_key = rsa.key.PublicKey(private_key.n, private_key.e)
        return Wallet(node_addr = node_addr,pr = private_key, pu = public_key)

    @staticmethod
    def optioned_create_wallet(node_addr = tuple()):
        path = input('Path to create or load wallet: ')
        if path == '':
            path = './'
        try_load = Wallet.load_wallet_pem(file_path=path)
        if try_load: # if a wallet is loaded, return it
            if node_addr:
                try_load.node_addr = node_addr
                try_load.connect_blockchain()
            return try_load
        else:
            new_wallet = Wallet(node_addr = node_addr)
            new_wallet.save_wallet_pem(file_path=path)
            return new_wallet
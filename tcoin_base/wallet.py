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
import errno
# rsa.key.PrivateKey._save_pkcs1_pem() => saves key like -----BEGIN RSA PRIVATE KEY-----
# rsa.key.PrivateKey._load_pkcs1_pem(data) => loads key from like -----BEGIN RSA PRIVATE KEY-----
WALLET_CHAIN = 'WALLET_CHAIN'
NEW_TX = 'NEW_TX'
HEADER_LENGTH = 100

class OneClient(socket.socket):

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
                    check = Blockchain.check_chain(chain)
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

class Wallet(socket.socket):

    def __init__(self, node_addr = tuple(), pr = None, pu = None):
        # __init__ Wallet
        self.__BITS = 2048
        # if loaded
        if pr != None:
            self.public, self.private = pu, pr
            print('Your Wallet has been loaded')
        else: # if not loaded creating new keys
            self.public, self.private = rsa.newkeys(self.__BITS)
            print('Your Wallet has been created')

        self.pu_ser = rsa.pem.save_pem(self.public._save_pkcs1_pem(),'RSA PUBLIC KEY')
        
        self.chain = None
        one_client = OneClient(node_addr)
        is_connected = one_client.connect_blockchain()

        if is_connected:
            self.chain = is_connected
            print('Connected to Blockchain ! Ready to go !')
        else:
            print('Try to connect another blockchain node...')
            sys.exit()

        # __init__ socket
        print('Connecting to TCOIN BLOCKCHAIN...')
        # creating a client for connecting blockchain
        super().__init__(socket.AF_INET,socket.SOCK_STREAM)
        if len(node_addr) > 0:
            self.connect(node_addr)
            print('connected')
        self.setblocking(False)

    def calculate_coins(self):
        total = 0
        plus = []
        minus = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == self.pu_ser:
                    minus.append(tx.input)
                if tx.receiver == self.pu_ser:
                    plus.append(tx.output)
                if tx.miner == self.pu_ser:
                    plus.append(tx.tx_fee)
        total = sum(plus) - sum(minus)
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
            pickled_tx = pickle.dumps(new_tx)
            tx_data = [NEW_TX, pickled_tx]
            tx_data = pickle.dumps(tx_data)
            data = f"{len(tx_data):<{HEADER_LENGTH}}".encode() + tx_data
            try:
                self.send(data)
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

    def communucate_blockchain(self):
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
                        check = Blockchain.check_chain(chain)
                        if check:
                            self.chain = chain
                            return True
                        else:
                            return False               
                except IOError as e:
                    if e.errno != errno.EAGAIN or e.errno != errno.EWOULDBLOCK:
                        print('Read Error !',str(e))
                        return False
                    else:
                        continue

    def new_job(self, target, args = None, daemon = False):
        t = threading.Thread(target=target)
        if args != None:
            t.args = args
        t.daemon = daemon
        t.start()

    @staticmethod
    def verify(data, sig, public_key):
        # rsa.verify returns the data encryption type it's sha256 for us
        try:
            rsa.verify(data, sig, public_key)
            return True
        except rsa.VerificationError:
            return False
    
    # loads private key from .pem file
    @staticmethod
    def load_wallet_pem(node_addr, file_path = './'):
        try:
            with open(file_path + 'pr_key.pem','rb') as pem_key:
                private_key = rsa.pem.load_pem(pem_key.read(),'RSA PRIVATE KEY')
                private_key = rsa.key.PrivateKey._load_pkcs1_pem(private_key)
        except:
            return False
        public_key = rsa.key.PublicKey(private_key.n, private_key.e)
        return Wallet(node_addr = node_addr,pr = private_key, pu = public_key)

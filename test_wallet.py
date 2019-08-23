import rsa
from tcoin_base.wallet import Wallet
import time
import threading
import sys
IP = "127.0.0.1"
PORT = int(input('Port: '))
# w = input('wallet: ')
w = None

# def open_wallet():
#     global w
w = Wallet.load_wallet_pem(node_addr=(IP, PORT), file_path='./')

w2 = Wallet.load_wallet_pem(file_path='./2')

def new_job(target, args = (), daemon = False):
    t = threading.Thread(target=target, args = args)
    t.daemon = daemon
    t.start()

def cmd():
    global w
    while True:
        cmd = input('command:')
        if cmd == 'quit':
            sys.exit()
        if cmd == 'tx':
            # new_job(target=w.send_tx,args=(w2.pu_ser,50,0),daemon=True)
            w.send_tx(w2.pu_ser,50,0)
        if cmd == 'calc':
            print(w.calculate_coins())
        if cmd == 'my_tx':
            for block in w.chain:
                for tx in block.transactions:
                    if tx['receiver'] == w.pu_ser.decode():
                        print(tx['input'],tx['output'])
        if cmd == 'reconn':
            w.connect_blockchain()

new_job(cmd)
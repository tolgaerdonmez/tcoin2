import rsa
from tcoin_base.wallet import Wallet
import time
import threading
import sys
IP = "127.0.0.1"
PORT = int(input('Port: '))
# w = input('wallet: ')

# w = Wallet.load_wallet_pem(node_addr=(IP, PORT), file_path='./' + w)
# w = Wallet(node_addr=(IP, PORT))
w = Wallet.optioned_create_wallet((IP, PORT))
# w2 = Wallet.load_wallet_pem(file_path='./2')
cur_recv = None
def new_job(target, args = (), daemon = False):
    t = threading.Thread(target=target, args = args)
    t.daemon = daemon
    t.start()

def cmd():
    global w
    global cur_recv
    
    while True:
        cmd = input('command:')
        if cmd == 'quit':
            sys.exit()
        if cmd == 'tx':
            # new_job(target=w.send_tx,args=(w2.pu_ser,50,0),daemon=True)
            pu = cur_recv.pu_ser
            w.send_tx(pu,50,7)
        if cmd == 'calc':
            print(w.calculate_coins())
        if cmd == 'my_tx':
            for block in w.chain:
                for tx in block.transactions:
                    if tx['receiver'] == w.pu_ser:
                        print(tx['input'],tx['output'])
        if cmd == 'reconn':
            w.connect_blockchain()
        if cmd == 'pu':
            print(w.pu_ser)
        if cmd == 'save':
            p = input('Save to: ')
            w.save_wallet_pem(file_path='./' + p)            
        if cmd == 'load_recv':
            p = input('load from: ')
            cur_recv = Wallet.load_wallet_pem(file_path='./' + p)
new_job(cmd)
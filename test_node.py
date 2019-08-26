from tcoin_base.node import Node
from tcoin_base.wallet import Wallet
from tcoin_base.blockchain import Blockchain
import threading
import time
import errno
import sys

IP = "127.0.0.1"
PORT = int(input('Port: '))
n1 = Node(IP,PORT, True)

def new_job(target, args = None, daemon = False):
    t = threading.Thread(target=target)
    if args != None:
        t.args = args
    t.daemon = daemon
    t.start()

def cmd():
    while True:
        cmd = input('command:')
        if cmd == 'quit':
            n1.aborting = True
            for t in n1.threads.values():
                t.join()
            # break
        if cmd == 'check':
            print(Blockchain.check_chain(n1.blockchain.chain))
        if cmd == 'mine':
            n1.blockchain.create_block(n1.wallet.pu_ser)
        if cmd == 'chain':
            print(len(n1.blockchain.chain))
        if cmd == 'nodes':
            print(n1.blockchain.current_nodes)
        if cmd == 'block':
            i = int(input('input index: '))
            print(n1.blockchain.chain[i])
        if cmd == 'send':
            n1.send_chain()
        if cmd == 'tx':
            print(len(n1.blockchain.current_transactions))
        if cmd == 'calc':
            n1.wallet.chain = n1.blockchain.chain
            print(n1.wallet.calculate_coins())
# for i in range(10):
#     n1.blockchain.create_block(n1.wallet.pu_ser.decode())

# print(Blockchain.check_chain(n1.blockchain.chain))
new_job(cmd)

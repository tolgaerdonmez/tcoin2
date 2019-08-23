# TCOIN
### Blockchain, Cyrpto Currency, Wallet Tools, Miner Tools

___
> Tested in Python 3.7.3 64-bit
## tcoin_base module
Base of the TCOIN Blockchain/Cyrpto Currency

## Installing Dependencies
	pip install -r req.txt
	
## Using test files
These test files just covers localhost implementation, but you can create different nodes in different ports
Make sure that after creating the first node, mine a block, then start another node in the same directory, that will inherit the ongoing blockchain and broadcast itself to other nodes, which found in inherited blockchain.

The `blockchain` file is written everytime when new block created
#### Starting test node:
	python test_node.py
output:
>PORT: (give your port)
#### Starting test wallet:
	python test_wallet.py
output:
>PORT: (give the port for the node that you want to connect)

You can learn the commands for test files by looking in them, easly understandable


class Transaction():

    def __init__(self, sender, input, receiver, output, miner = None, tx_fee = 0, sig = None):
        self.input = (sender,input)
        self.output = (receiver,output)

        self.tx_fee = tx_fee
        self.miner = miner
        # calculates fee
        tx_fee = input - output
        if tx_fee > 0:
            self.tx_fee = tx_fee

        self.sender = sender
        self.receiver = receiver

        # default is None
        self.sig = sig

    def sign(self, wallet):
        pass

    def __gather(self):
        if self.tx_fee > 0:
            return [self.input,self.output,(self.miner,self.tx_fee)]
        return [self.input,self.output]
class Transaction():

    def __init__(self, sender, receiver, input, output):
        self.sender = sender
        self.receiver = receiver
        self.input = input
        self.output = output

        self.tx_fee = 0
        # calculates fee
        tx_fee = input - output
        if tx_fee > 0:
            self.tx_fee = tx_fee

        # default is None
        self.sig = None

    def gather(self):
        if self.tx_fee > 0:
            return [(self.sender, self.input), (self.receiver, self.output), self.tx_fee]
        return [self.input,self.output]

    def __str__(self):
        return f"Sender: {self.sender[30:40]}... \n Receiver: {self.receiver[30:40]}... \n Amount: {self.output} Tx fee: {self.tx_fee}"

    def dict(self):
        dict = {'sender':self.sender,'receiver':self.receiver,'input':self.input,'output':self.output,'tx_fee':self.tx_fee,'sig':self.sig}
        return dict

    @staticmethod
    def from_dict(dict):
        tx = Transaction(sender = dict['sender'],receiver = dict['receiver'], input = dict['input'], output = dict['output'])
        tx.sig = dict['sig']
        return tx
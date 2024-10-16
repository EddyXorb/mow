import logging


class VerbosePrinterClass:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def printv(self, *args):
        if self.verbose:
            logging.info(*args)

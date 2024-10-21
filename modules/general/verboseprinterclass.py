import logging


class VerbosePrinterClass:
    """
    The idea behind the class is to be able to easily deactivate output completely and to have a stable interface for logging.
    The deactivation possibility is not in use currently.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = logging.getLogger("MOW")

    def print_debug(self, *args):
        if self.verbose:
            self.logger.debug(*args)

    def print_info(self, *args):
        if self.verbose:
            self.logger.info(*args)

    def print_warning(self, *args):
        if self.verbose:
            self.logger.warning(*args)

    def print_error(self, *args):
        if self.verbose:
            self.logger.error(*args)

    def print_critical(self, *args):
        if self.verbose:
            self.logger.critical(*args)

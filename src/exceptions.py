"""Custom exceptions."""


class BitcoinConfigException(Exception):
    """Custom exception class related to configuration of Bitcoin Core RPC."""

    def __init__(self, message: str):
        """
        Initialize the BitcoinConfigException instance.

        :param message: The error message associated with the exception.
        :type message: str
        """
        super().__init__(message)


class DailyPriceException(Exception):
    """Custom exception class related to daily price calculations."""

    def __init__(self, message: str):
        """
        Initialize the DailyPriceException instance.

        :param message: The error message associated with the exception.
        :type message: str
        """
        super().__init__(message)


class RPCException(Exception):
    """Custom exception class related to Bitcoin Core RPC."""

    def __init__(self, message: str):
        """
        Initialize the RPCException instance.

        :param message: The error message associated with the exception.
        :type message: str
        """
        super().__init__(message)

"""Set up for logger."""
from logging import INFO, Logger, basicConfig, getLogger


def init_logger(name: str) -> Logger:
    """
    Initialize a logger with the specified name and basic configuration.

    This function creates and configures a logger object with the specified name.
    It sets the logging level to INFO and the logging format to
    "%(asctime)s %(levelname)s %(message)s".

    :param name: The name of the logger.
    :type name: str

    :return: The initialized logger object.
    :rtype: Logger
    """
    basicConfig(level=INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger = getLogger(name)
    return logger

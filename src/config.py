"""BitcoinConfig Class."""
import re
from os import getenv, path
from pathlib import Path
from typing import List

from src.exceptions import BitcoinConfigException
from src.logger import init_logger

logger = init_logger("bitcoin_price_oracle")


class BitcoinConfig:
    """
    A class for reading Bitcoin Core config settings from a bitcoin.conf file.

    This class parses the bitcoin.conf file and extracts relevant RPC-related
    configuration options. It generates the appropriate options to be used
    with bitcoin-cli commands.
    """

    def __init__(self, conf_path: str = None):
        """
        Initialize the BitcoinConfig instance.

        :param conf_path: The path where the bitcoin.conf file is located
            (default is None - "~/.bitcoin/bitcoin.conf").
        :type conf_path: str
        """
        if not conf_path:
            self.conf_path = Path.home() / ".bitcoin/bitcoin.conf"
        else:
            self.conf_path = conf_path
        self.rpc_options = [
            "datadir",
            "rpcuser",
            "rpcpassword",
            "rpcookiefile",
            "rpcconnect",
            "rpcport",
            "conf",
        ]

        self.config = {}

    def generate_options(self) -> List[str]:
        """
        Generate RPC-related options for bitcoin-cli commands.

        This method reads the bitcoin.conf file and extracts relevant RPC-related
        options to be used with bitcoin-cli commands.

        :return: A list of RPC-related options for bitcoin-cli commands.
        :rtype: List[str]

        :Example:
            >>> config = BitcoinConfig()
            >>> rpc_options = config.generate_options()
            >>> print(rpc_options)
        """
        options = []

        if path.exists(self.conf_path):
            try:
                # Read the file and parse key-value pairs
                with open(self.conf_path, "r", encoding="utf-8") as file:
                    for line in file:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue  # Skip empty lines and comments

                        # Use regular expression to extract key-value pairs
                        match = re.match(r"^\s*([^#\s=]+)\s*=\s*([^#]+)\s*$", line)
                        if match:
                            key = match.group(1).lower()
                            value = match.group(2).strip()
                            self.config[key] = value

            except FileNotFoundError as error:
                logger.error(
                    "Config file not found at path: %s", self.conf_path, exc_info=True
                )
                logger.info("Please check the location of your bitcoin.conf file...")
                raise error

            options.extend(
                f"-{key}={value}"
                for key in self.rpc_options
                if (value := self.config.get(key)) is not None
            )
        else:
            logger.info("Checking for RPC credentials in environment variables...")
            rpc_creds = {
                "datadir": getenv("datadir"),
                "rpcuser": getenv("rpcuser"),
                "rpcpassword": getenv("rpcpassword"),
            }

            missing_vars = [1 for _, value in rpc_creds.items() if value is None]

            if missing_vars:
                raise BitcoinConfigException(
                    "Credentials not found. Please set credentials or path for bitcoin.conf file..."
                )

            options.extend(
                [
                    f"datadir={rpc_creds['datadir']}",
                    f"rpcuser={rpc_creds['rpcuser']}",
                    f"rpcpassword={rpc_creds['rpcpassword']}",
                ]
            )

        return options

"""Bitcoin Core RPC Client."""
import json
from asyncio import create_subprocess_exec, create_task, gather, subprocess
from typing import Dict, List

import backoff

from src.config import BitcoinConfig
from src.exceptions import RPCException
from src.logger import init_logger

logger = init_logger("bitcoin_price_oracle")


class BitcoinRPCClient:
    """
    A client for interacting with a Bitcoin Core node using RPC calls.

    This class provides methods for making various RPC calls to a Bitcoin Core
    node using bitcoin-cli commands. It utilizes the BitcoinConfig class to
    generate the necessary options for bitcoin-cli commands.

    :Example:
        >>> client = BitcoinRPCClient()
        >>> block_count = await client.get_block_count()
        >>> print(f"Current block count: {block_count}")
    """

    def __init__(self, config: BitcoinConfig):
        """
        Initialize the BitcoinRPCClient.

        This constructor initializes the BitcoinRPCClient by setting up
        necessary configurations and bitcoin-cli options.

        :param config: Bitcoin RPC configuration
        :type config: BitcoinConfig

        :Example:
            >>> client = BitcoinRPCClient(config)
        """
        self.conf = config
        self.bitcoin_cli_options = self.conf.generate_options()
        self.bitcoin_cli = ["bitcoin-cli"] + self.bitcoin_cli_options

    async def __aenter__(self):
        """
        Enter the asynchronous context.

        This method is called when entering an asynchronous context using
        the 'async with' statement.

        :return: The BitcoinRPCClient instance
        :rtype: BitcoinRPCClient
        """
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        Exit the asynchronous context.

        This method is called when exiting an asynchronous context using
        the 'async with' statement. It performs any necessary cleanup actions.

        :param exc_type: The type of the exception that occurred
            (or None if no exception)
        :type exc_type: type or None
        :param exc_value: The exception instance that was raised
            (or None if no exception)
        :type exc_value: Exception or None
        :param traceback: The traceback object (or None if no exception)
        :type traceback: traceback or None
        """
        if exc_type:
            raise RPCException(f"RPC call failed...")

    @backoff.on_exception(
        backoff.expo, RPCException(f"RPC call failed..."), max_tries=5
    )
    async def _get_rpc_response(self, *args: List[str]) -> bytes:
        """
        Execute a bitcoin-cli command and return the response.

        This method executes a bitcoin-cli command asynchronously and
        returns the response in bytes.

        :param args: A list of arguments for the bitcoin-cli command.
        :type args: List[str]

        :return: The response from the bitcoin-cli command in bytes.
        :rtype: bytes

        :Example:
            >>> response = await self._get_rpc_response("getblockcount")
        """
        command = self.bitcoin_cli + list(args)
        process = await create_subprocess_exec(*command, stdout=subprocess.PIPE)
        response_bytes = await process.stdout.read()
        return response_bytes

    async def get_block_count(self) -> int:
        """
        Get the current block count.

        This method retrieves the current block count from the
        Bitcoin Core node.

        :return: The current block count.
        :rtype: int

        :Example:
            >>> block_count = await self.get_block_count()
        """
        return int(await self._get_rpc_response("getblockcount"))

    async def get_block_hash(self, block_height: int) -> str:
        """
        Get the block hash for a given block height.

        This method retrieves the block hash for a given block height from
        the Bitcoin Core node.

        :param block_height: The block height.
        :type block_height: int

        :return: The block hash for the specified block height.
        :rtype: str

        :Example:
            >>> block_hash = await self.get_block_hash(600000)
        """
        return (await self._get_rpc_response("getblockhash", str(block_height))).decode(
            "utf-8"
        )[:64]

    async def get_block_hashes(self, block_heights: List[int]) -> List[str]:
        """
        Get block hashes for a list of block heights asynchronously.

        :param block_heights: List of block heights for which to retrieve
            block hashes.
        :type block_heights: List[int]
        :return: List of block hashes corresponding to the provided block
            heights.
        :rtype: List[str]
        """
        return await gather(
            *[create_task(self.get_block_hash(height)) for height in block_heights]
        )

    async def get_block_header(self, block_hash: str) -> Dict:
        """
        Get the block header for a given block hash.

        This method retrieves the block header for a given block hash from
        the Bitcoin Core node.

        :param block_hash: The block hash.
        :type block_hash: str

        :return: The block header as a dictionary.
        :rtype: Dict

        :Example:
            >>> block_header = await self.get_block_header("block_hash")
        """
        return json.loads(
            (await self._get_rpc_response("getblockheader", block_hash, "true")).decode(
                "utf-8"
            )
        )

    async def get_block(self, block_hash: str) -> Dict:
        """
        Get the block information for a given block hash.

        This method retrieves detailed block information for a given block
        hash from the Bitcoin Core node. 2 is verbosity.

        :param block_hash: The block hash.
        :type block_hash: str

        :return: Detailed block information as a dictionary.
        :rtype: Dict

        :Example:
            >>> block_info = await self.get_block("block_hash")
        """
        return json.loads(
            (await self._get_rpc_response("getblock", block_hash, "2")).decode("utf-8")
        )

    async def get_blocks(self, block_hashes: List[str]) -> List[Dict]:
        return await gather(
            *[create_task(self.get_block(bhash)) for bhash in block_hashes]
        )

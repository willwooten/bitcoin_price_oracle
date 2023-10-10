"""Class for block oscillator."""
from typing import Dict, Tuple

from src.rpc import BitcoinRPCClient


class BlockOscillator:
    """
    BlockOscillator class for determining the price day block.

    This class implements the block oscillator algorithm to determine
    the block on the price day based on specified parameters.
    """

    blocks_per_day: int = 144
    seconds_in_day: int = 86400

    def __init__(self, rpc: BitcoinRPCClient, pass_values: Dict):
        """
        Initialize the BlockOscillator instance.

        :param rpc: Bitcoin RPC Client
        :type rpc: BitcoinRPCClient
        :param pass_values: Initial values passed from BitcoinDailyPrice.
        :type pass_values: dict
        """
        self.rpc = rpc
        self.price_day_timestamp = pass_values["price_day_timestamp"]
        self.latest_block_timestamp = pass_values["latest_block_timestamp"]
        self.block_count = pass_values["block_count"]

    async def run_block_oscillator(self) -> int:
        """
        Run the block oscillator to determine the price day block.

        This method executes the block oscillator algorithm to determine
        the block on the price day.

        :return: Block on the price day
        :rtype: int
        """
        return await self._block_oscillator()

    async def _set_oscillator_block(
        self, block_height_estimate: int
    ) -> Tuple[int, int]:
        """
        Set the oscillator block and related information.

        This asynchronous method sets the block timestamp and the
        block jump estimate based on the provided block height estimate.

        :param block_height_estimate: The estimated block height for
            the oscillator.
        :type block_height_estimate: int
        :return: A tuple containing the block timestamp and the block
            jump estimate.
        :rtype: Tuple[int, int]
        """
        block_hash = await self.rpc.get_block_hash(block_height_estimate)
        block_timestamp = (await self.rpc.get_block_header(block_hash))["time"]

        block_jump_estimate = self._block_estimate(
            block_timestamp - self.price_day_timestamp
        )

        return block_timestamp, block_jump_estimate

    async def _block_oscillator(self) -> int:
        """
        Calculate the oscillator block and related information.

        This asynchronous method calculates the price day block estimate.

        Bitcoin Core organizes blocks by height, not by time. As a result, it's not
        possible to query Bitcoin Core for a block at a specific time. This method
        works around this limitation by iteratively estimating the block heights
        to approximate the desired time.
        """
        block_height_estimate = self.block_count - self._block_estimate(
            self.latest_block_timestamp - self.price_day_timestamp
        )
        block_timestamp, block_jump_estimate = await self._set_oscillator_block(
            block_height_estimate
        )

        last_estimate = 0
        last_last_estimate = 0
        while block_jump_estimate > 6 and block_jump_estimate != last_last_estimate:
            last_last_estimate = last_estimate
            last_estimate = block_jump_estimate

            # get block header or new estimate
            block_height_estimate = block_height_estimate - block_jump_estimate
            block_timestamp, block_jump_estimate = await self._set_oscillator_block(
                block_height_estimate
            )

        if block_timestamp > self.price_day_timestamp:
            # if the estimate was after price day look at earlier blocks
            while block_timestamp > self.price_day_timestamp:
                block_height_estimate -= 1
                block_timestamp, block_jump_estimate = await self._set_oscillator_block(
                    block_height_estimate
                )
            block_height_estimate += 1

        elif block_timestamp < self.price_day_timestamp:
            while block_timestamp < self.price_day_timestamp:
                # increment the block by one, read new block header, check time
                block_height_estimate += 1
                if block_height_estimate >= self.block_count:
                    break
                block_timestamp, block_jump_estimate = await self._set_oscillator_block(
                    block_height_estimate
                )

        return block_height_estimate

    def _block_estimate(self, timestamp: int) -> int:
        """
        Estimate the block number for a given timestamp.

        This estimation is based on the assumption that the Bitcoin network generates
        around 144 blocks in a day. It calculates the block number corresponding to
        the provided UNIX timestamp using the specified number of seconds in a day.

        :param timestamp: The UNIX timestamp for which the block number is to
            be estimated.
        :type timestamp: int

        :return: The estimated block number corresponding to
            the given timestamp.
        :rtype: int
        """
        return round(self.blocks_per_day * float(timestamp) / self.seconds_in_day)

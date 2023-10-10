"""Class for working with price bins."""
from itertools import chain
from math import log10
from typing import Dict, List

from src.helpers import get_day_of_month
from src.logger import init_logger
from src.rpc import BitcoinRPCClient

logger = init_logger("bitcoin_price_oracle")


class PriceBins:
    """PriceBins class for organizing price bins and related calculations."""

    # set bin values
    first_bin_value: int = -6
    last_bin_value: int = 6
    range_bin_values: int = last_bin_value - first_bin_value

    # set bounds for curve
    lower_bound: int = 201
    upper_bound: int = 1601

    # create a list of round btc bin numbers
    round_btc_bins: List[int] = [
        201,  # 1k sats
        401,  # 10k
        461,  # 20k
        496,  # 30k
        540,  # 50k
        601,  # 100k
        661,  # 200k
        696,  # 300k
        740,  # 500k
        801,  # 0.01 btc
        861,  # 0.02
        896,  # 0.03
        940,  # 0.04
        1001,  # 0.1
        1061,  # 0.2
        1096,  # 0.3
        1140,  # 0.5
        1201,  # 1 btc
    ]

    def __init__(self, rpc: BitcoinRPCClient, price_day_block: int):
        """
        Initialize the PriceBins object.

        :param price_day_block: The first block on day to get price estimate.
        :type pass_values: int
        """

        # inherit from BitcoinDailyPrice
        self.rpc = rpc
        self.price_day_block = price_day_block

        logger.info("Generating bins...")

        # Generate bin values and initialize bin counts
        self.output_bell_curve_bins = self._generate_bin_values()
        self.output_bell_curve_bin_counts = self._initialize_bin_counts(
            self.output_bell_curve_bins
        )
        self.number_of_bins = len(self.output_bell_curve_bins)

    async def run_price_bins(self):
        """
        Run the price bin calculations.
        """
        await self._get_target_day_blocks()
        self._remove_outlier_amounts()
        self._smooth_round_btc_bins()
        self._normalize_curve()

    def _generate_bin_values(self, num_bins_per_10x: int = 200) -> List[float]:
        """
        Generate a list of bin values.

        This method generates a list of bin values that follow a logarithmic
        scale based on the provided number of bins per 10x range. It
        calculates values spanning from the first to the last bin value,
        with a specified number of bins per 10x.

        :param num_bins_per_10x: The number of bins per 10x range.
        :type num_bins_per_10x: int, optional

        :return: A list of bin values following a logarithmic scale.
        :rtype: List[float]
        """
        bin_values = [
            10 ** (exponent + b / num_bins_per_10x)
            for exponent in range(self.first_bin_value, self.last_bin_value)
            for b in range(num_bins_per_10x)
        ]
        return [0.0] + bin_values  # Add zero sats as the first bin

    def _initialize_bin_counts(self, bin_values: List[float]) -> float:
        """
        Initialize bin counts to zero for each bin value.

        This method takes a list of bin values and initializes the bin
        counts for each bin value to zero. The resulting list contains
        zero counts corresponding to each bin value.

        :param bin_values: List of bin values.
        :type bin_values: List[float]

        :return: A list of zero counts corresponding to each bin value.
        :rtype: List[float]
        """
        return [0.0] * len(bin_values)

    async def _get_target_day_blocks(self) -> None:
        """
        Retrieve and process blocks from a specified day.

        This function retrieves blocks for a given day centered around the
        price_day_block set by oscillator, parses the outputs, and processes
        them for further analysis.

        Note:
            Gets 50 blocks before and 175 blocks after price_day_block
            set by oscillator to make sure all blocks on that day are
            retrieved and parsed for vout amounts.
        """

        blocks_heights = [
            n for n in range(self.price_day_block - 50, self.price_day_block + 175, 1)
        ]

        block_hashes = await self.rpc.get_block_hashes(blocks_heights)

        block_responses = await self.rpc.get_blocks(block_hashes)

        target_day_of_month = get_day_of_month(block_responses[50]["time"])

        # filters to only blocks on day of price_day_block target
        block_responses = [
            block
            for block in block_responses
            if get_day_of_month(block["time"]) == target_day_of_month
        ]

        for vout in chain.from_iterable(
            (output for tx in block["tx"] for output in tx["vout"])
            for block in block_responses
        ):
            self._parse_outputs(vout)

    def _parse_outputs(self, vout: Dict) -> None:
        """
        Parse and process a transaction output to update bin counts.

        This method extracts the amount from a transaction output and calculates the
        corresponding bin number. It then increments the bin count for that bin number
        in the output bin counts.

        :param vout: The output of a transaction.
        :type vout: Dict
        """
        amount = float(vout["value"])

        # tiny and huge amounts aren't used by the USD price finder
        if 1e-6 < amount < 1e6:
            # take the log
            amount_log = log10(amount)

            # find the right output amount bin to increment
            bin_number_est = self._calculate_bin_number_est(amount_log)

            # search for the exact right bin (won't be less than)
            while self.output_bell_curve_bins[bin_number_est] <= amount:
                bin_number_est += 1
            bin_number = bin_number_est - 1

            # increment the output bin
            self._increment_bin_count(bin_number)

    def _calculate_bin_number_est(self, amount_log: float) -> int:
        """
        Calculate the estimated bin number based on the log of the amount.

        :param amount_log: The logarithm of the amount.
        :type amount_log: float

        :return: The estimated bin number.
        :rtype: int
        """
        bin_percentage = (amount_log - self.first_bin_value) / self.range_bin_values
        return int(bin_percentage * self.number_of_bins)

    def _increment_bin_count(self, bin_number: int) -> None:
        """
        Increment the count of a specific bin.

        This method increments the count of the specified bin in
        the output bin counts.

        :param bin_number: The bin number to increment.
        :type bin_number: int
        """
        self.output_bell_curve_bin_counts[bin_number] += 1.0

    def _remove_outlier_amounts(self) -> None:
        """
        Remove outlier amounts from the output bin counts.

        This method removes outlier amounts from the output bin
        counts based on defined lower (.00001 btc) and
        upper (10.0 btc) bounds.
        """
        # remove ouputs below 1k sats
        self.output_bell_curve_bin_counts[: self.lower_bound] = [0.0] * self.lower_bound
        # remove outputs above ten btc
        self.output_bell_curve_bin_counts[self.upper_bound :] = [0.0] * (
            self.number_of_bins - self.upper_bound
        )

    def _smooth_round_btc_bins(self) -> None:
        """
        Smooth the output bell curve by averaging round BTC amounts.

        This method smoothes the output bell curve by averaging the bin
        counts for round BTC amounts.
        """
        for r in self.round_btc_bins:
            amount_above = self.output_bell_curve_bin_counts[r + 1]
            amount_below = self.output_bell_curve_bin_counts[r - 1]
            self.output_bell_curve_bin_counts[r] = 0.5 * (amount_above + amount_below)

    def _set_curve_sum(self) -> None:
        """
        Set the sum of the curve for normalization.

        This method calculates and sets the sum of the
        curve within the specified range for normalization.
        """
        return sum(
            self.output_bell_curve_bin_counts[self.lower_bound : self.upper_bound]
        )

    def _normalize_curve(self) -> None:
        """
        Normalize the output bell curve.

        This method normalizes the output bell curve by dividing each
        count by the curve's sum and removes extreme values.
        """
        self.output_bell_curve_bin_counts[self.lower_bound : self.upper_bound] = [
            min(0.008, count / self._set_curve_sum())
            for count in self.output_bell_curve_bin_counts[
                self.lower_bound : self.upper_bound
            ]
        ]

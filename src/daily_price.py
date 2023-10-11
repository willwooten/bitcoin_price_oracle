"""Main class for calculating estimated daily price."""
from datetime import datetime, timedelta, timezone

from src.bins import PriceBins
from src.exceptions import DailyPriceException
from src.logger import init_logger
from src.oscillator import BlockOscillator
from src.rpc import BitcoinRPCClient
from src.stencil import Stencil

logger = init_logger("bitcoin_price_oracle")


class BitcoinDailyPrice:
    """
    Main class for calculating estimated daily Bitcoin price.

    This class provides methods to estimate the Bitcoin price for a given
    date based on transaction data and a stencil process. It calculates the
    best slide, processes neighboring slides, and computes the price estimate
    using weighted averages.
    """

    def __init__(
        self,
        rpc: BitcoinRPCClient,
        date_entered: str,
    ):
        """
        Initialize the BitcoinDailyPrice instance.

        :param rpc: Bitcoin RPC client
        :type rpc: BitcoinRPCClient
        :param date_entered: The date to query in the format "YYYY-MM-DD".
        :type date_entered: str
        """
        logger.info("Initializing...")

        # initalize RPC client
        self.rpc = rpc

        # initialize dates
        self.datetime_entered = datetime(
            int(date_entered.split("-")[0]),
            int(date_entered.split("-")[1]),
            int(date_entered.split("-")[2]),
            0,
            0,
            0,
            tzinfo=timezone.utc,
        )

        self.prior_day = self.datetime_entered - timedelta(days=1)

        self.pass_values = {
            "price_day_timestamp": int(self.datetime_entered.timestamp()),
        }

        # raise exception if using too early of a block
        if (
            self.datetime_entered.timestamp()
            # minumum block where results are meaningful & accurate, default 2020-07-26
            < datetime(2020, 7, 26, 0, 0, 0, tzinfo=timezone.utc).timestamp()
        ):
            raise DailyPriceException(
                f"The date entered ({date_entered}) \
                    is before the earliest recommended date of 2020-07-26..."
            )

    async def run_estimate_price(self) -> None:
        """
        Run the estimation process for BTC price.

        This asynchronous method executes the steps for estimating the BTC price,
        including setting the current block, calculating the block
        oscillator, getting target day blocks, removing outlier amounts, smoothing
        BTC bins, setting the curve sum, normalizing the curve, initiating the
        stencil, and running the stencil.
        """
        logger.info(
            "Running daily price estimate for %s...",
            self.datetime_entered.strftime("%Y-%m-%d"),
        )

        await self._set_current_block()

        logger.info("Running block oscillator...")
        price_day_block = await BlockOscillator(
            self.rpc, self.pass_values
        ).run_block_oscillator()

        bins = PriceBins(self.rpc, price_day_block)

        await bins.run_price_bins()

        price_estimate = await Stencil(bins).run_stencil()

        logger.info("Price estimate: %s", price_estimate)

    async def _set_current_block(self) -> None:
        """
        Set the current block and related time information.

        This asynchronous method sets the current block and related time
        information such as the latest time in seconds. It also validates
        whether the entered datetime is before the current date and
        raises an exception if not.

        :raises Exception: If the entered datetime is not before the
            current date.
        """
        logger.info("Setting current block...")
        self.pass_values["block_count"] = await self.rpc.get_block_count()
        self.pass_values["latest_block_timestamp"] = (
            await self.rpc.get_block_header(
                await self.rpc.get_block_hash(self.pass_values["block_count"])
            )
        )["time"]

        time_datetime = datetime.fromtimestamp(
            self.pass_values["latest_block_timestamp"], tz=timezone.utc
        )

        if (
            self.datetime_entered.timestamp()
            >= datetime(
                time_datetime.year,
                time_datetime.month,
                time_datetime.day,
                0,
                0,
                0,
                tzinfo=timezone.utc,
            ).timestamp()
        ):
            raise DailyPriceException(
                "The date entered is not before the current date, please try again..."
            )

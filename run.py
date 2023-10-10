import argparse
from asyncio import run
from datetime import datetime, timedelta
from time import time

from src.config import BitcoinConfig
from src.daily_price import BitcoinDailyPrice
from src.helpers import format_date, is_valid_date
from src.logger import init_logger
from src.rpc import BitcoinRPCClient

logger = init_logger("bitcoin_price_oracle")


async def main():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()

    # Add an argument flag
    parser.add_argument(
        "-s", "--start", type=str, help="start date for price estimate (YYYY-MM-DD)"
    )
    parser.add_argument(
        "-e", "--end", type=str, help="end date for price estimate (YYYY-MM-DD)"
    )
    parser.add_argument(
        "-d", "--date", type=str, help="specific date for price estimate (YYYY-MM-DD)"
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # if only want a single date
    if args.date:
        if is_valid_date(args.date):
            logger.info("Price estimate date set: %s", args.date)
            date_index = [args.date]
        else:
            logger.error("Please provide date in the format YYYY-MM-DD.")

    # Check if the flag was provided for range of dates
    elif args.start and args.end:
        if is_valid_date(args.start) and is_valid_date(args.end):
            start = format_date(args.start)
            end = format_date(args.end)

            logger.info("Price estimate dates set: %s to %s", args.start, args.end)

            # Generate a list of dates between start and end (inclusive)
            date_index = [
                (start + timedelta(days=x)).strftime("%Y-%m-%d")
                for x in range((end - start).days + 1)
            ]

        else:
            logger.error("Please provide dates in the format YYYY-MM-DD.")
    else:
        logger.info("No dates provided. Getting prior day...")
        date_index = [(datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")]

    config = BitcoinConfig()
    async with BitcoinRPCClient(config) as rpc:
        for date in date_index:
            await BitcoinDailyPrice(rpc, date).run_estimate_price()

        # TODO: node can't handle too many requests at once.
        # should figure out way to get around this limitation.
        """await gather(
            *[
                create_task(BitcoinDailyPrice(rpc, date).run_estimate_price())
                for date in date_index
            ]
        )"""


if __name__ == "__main__":
    start_time = time()

    run(main())

    print(
        f"Execution Time For Data Collection: {str(time() - start_time)} seconds!",
    )

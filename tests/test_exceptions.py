import sys
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from src.exceptions import BitcoinConfigException, DailyPriceException, RPCException


def test_bitcoin_config_exception():
    try:
        raise BitcoinConfigException("Bitcoin config error")
    except BitcoinConfigException as e:
        assert str(e) == "Bitcoin config error"


def test_daily_price_exception():
    try:
        raise DailyPriceException("Daily price calculation error")
    except DailyPriceException as e:
        assert str(e) == "Daily price calculation error"


def test_rpc_exception():
    try:
        raise RPCException("RPC call failed")
    except RPCException as e:
        assert str(e) == "RPC call failed"

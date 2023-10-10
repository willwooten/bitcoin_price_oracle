import sys
import unittest
from os import path
from pathlib import Path
from unittest.mock import patch

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from src.config import BitcoinConfig
from src.exceptions import BitcoinConfigException


class TestBitcoinConfig(unittest.TestCase):
    def setUp(self):
        self.config = BitcoinConfig("tests/example.conf")

    def test_init(self):
        result = BitcoinConfig()
        self.assertEqual(result.conf_path, Path.home() / ".bitcoin/bitcoin.conf")

    def test_generate_options(self):
        expected_options = [
            "-datadir=/path/to/datadir",
            "-rpcuser=myrpcuser",
            "-rpcpassword=myrpcpassword",
        ]

        result = self.config.generate_options()

        self.assertEqual(result, expected_options)

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_generate_options_file_not_found(self, mock_file_open):
        with self.assertRaises(FileNotFoundError):
            self.config.generate_options()


def test_generate_options_no_conf_file():
    # Simulate the scenario where the bitcoin.conf file does not exist
    with unittest.mock.patch(
        "src.config.path.exists", return_value=False
    ), unittest.mock.patch("src.config.getenv", return_value="envvalues"):
        config = BitcoinConfig()
        options = config.generate_options()

    assert options == [
        "datadir=envvalues",
        "rpcuser=envvalues",
        "rpcpassword=envvalues",
    ]


def test_generate_options_no_environment_vars():
    # Simulate the scenario where environment variables are not set
    with unittest.mock.patch(
        "src.config.path.exists", return_value=False
    ), unittest.mock.patch("src.config.getenv", return_value=None):
        try:
            config = BitcoinConfig()
            config.generate_options()
        except BitcoinConfigException as e:
            assert (
                str(e)
                == "Credentials not found. Please set credentials or path for bitcoin.conf file..."
            )
            return

    # If the exception was not raised, fail the test
    assert False, "Expected BitcoinConfigException, but it was not raised"

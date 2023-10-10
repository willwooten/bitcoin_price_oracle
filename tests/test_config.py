import sys
import unittest
from os import path
from pathlib import Path
from unittest.mock import mock_open, patch

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from src.config import BitcoinConfig


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

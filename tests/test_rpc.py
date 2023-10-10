import sys
from os import path
from typing import List
from unittest.mock import MagicMock, patch

from pytest import mark

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from src.config import BitcoinConfig
from src.exceptions import RPCException
from src.rpc import BitcoinRPCClient


class MockBitcoinConfig:
    def __init__(self, conf_path: str = None):
        # Mock the initialization behavior
        self.conf_path = conf_path
        self.rpc_options = []
        self.config = {}

    def generate_options(self) -> List[str]:
        # Mock the generation of RPC-related options
        return ["mock_option1", "mock_option2"]


class TestRPCCalls:
    rpc: BitcoinRPCClient = BitcoinRPCClient(MockBitcoinConfig())

    @mark.asyncio
    @patch("src.rpc.BitcoinRPCClient._get_rpc_response", return_value=b"1234")
    async def test_get_block_count(self, mock_get_rpc_response):
        block_count = await self.rpc.get_block_count()
        assert block_count == 1234

    @mark.asyncio
    @patch(
        "src.rpc.BitcoinRPCClient._get_rpc_response",
        return_value=b"00000000000nevergoingtogiveyouup",
    )
    async def test_get_block_hash(self, mock_get_rpc_response):
        result = await self.rpc.get_block_hash(600000)
        assert result == "00000000000nevergoingtogiveyouup"

    @mark.asyncio
    @patch(
        "src.rpc.BitcoinRPCClient._get_rpc_response",
        return_value=b"00000000000nevergoingtoletyoudown",
    )
    async def test_get_block_hashes(self, mock_get_rpc_response):
        result = await self.rpc.get_block_hashes([1, 2])
        assert result == ["00000000000nevergoingtoletyoudown"] * 2

    @mark.asyncio
    @patch(
        "src.rpc.BitcoinRPCClient._get_rpc_response", return_value=b'{"block": 90210}'
    )
    async def test_get_block_header(self, mock_get_rpc_response):
        result = await self.rpc.get_block_header("hash")
        assert result["block"] == 90210

    @mark.asyncio
    @patch(
        "src.rpc.BitcoinRPCClient._get_rpc_response",
        return_value=b'{"hash": "nevergoingtorunaround"}',
    )
    async def test_get_block(self, mock_get_rpc_response):
        result = await self.rpc.get_block("hash")
        assert result["hash"] == "nevergoingtorunaround"

    @mark.asyncio
    @patch(
        "src.rpc.BitcoinRPCClient._get_rpc_response",
        return_value=b'{"hash": "anddesertyou"}',
    )
    async def test_get_blocks(self, mock_get_rpc_response):
        result = await self.rpc.get_blocks(["hash", "hash"])
        assert [r["hash"] for r in result] == ["anddesertyou"] * 2

    @mark.asyncio
    async def test_rpc_client_async_context(self):
        # Create a mock BitcoinConfig instance
        mock_config = MagicMock(spec=BitcoinConfig)
        mock_config.generate_options.return_value = []

        # Create a mock RPC exception
        mock_exception = RPCException("RPC call failed...")

        async with BitcoinRPCClient(mock_config) as client:
            # Test __aenter__ method
            assert client is not None

            # Test __aexit__ method with no exception
            await client.__aexit__(None, None, None)  # Should not raise an exception

            # Test __aexit__ method with an exception
            with patch("src.exceptions.RPCException", side_effect=mock_exception):
                try:
                    await client.__aexit__(Exception, Exception("Test exception"), None)
                except RPCException as e:
                    assert str(e) == "RPC call failed..."

    @mark.asyncio
    async def test_rpc_client_async_context_noop(self):
        # Create a mock BitcoinConfig instance
        mock_config = MagicMock(spec=BitcoinConfig)
        mock_config.generate_options.return_value = []

        async with BitcoinRPCClient(mock_config) as client:
            # Test __aexit__ method with no exception
            await client.__aexit__(None, None, None)

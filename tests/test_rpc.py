import sys
import unittest
from asyncio import subprocess
from os import path
from unittest.mock import AsyncMock, patch

from pytest import mark

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from src.exceptions import RPCException
from src.rpc import BitcoinRPCClient


@mark.asyncio
async def test__get_rpc_response():
    rpc = BitcoinRPCClient()

    with patch(
        "src.rpc.create_subprocess_exec",
        new_callable=AsyncMock,
        return_value=AsyncMock(
            stdout=AsyncMock(
                read=AsyncMock(return_value=b"Mocked response from subprocess")
            )
        ),
    ):
        # Call the method you want to test
        response_bytes = await rpc._get_rpc_response()

        # Check if the response matches the mock response
        assert response_bytes == b"Mocked response from subprocess"


@mark.asyncio
async def test__get_rpc_response_subprocess_error():
    # Replace with your actual initialization logic for YourClass
    rpc = BitcoinRPCClient()

    # Patch the subprocess call and raise the mock subprocess error
    with patch(
        "src.rpc.create_subprocess_exec",
        new_callable=AsyncMock,
        side_effect=RPCException("Mock subprocess error"),
    ):
        try:
            # Call the method that is expected to raise subprocess error
            await rpc._get_rpc_response("getblockcount")
        except RPCException as error:
            # Check if the subprocess error is raised correctly
            assert str(error) == "Mock subprocess error"
        else:
            # If no exception is raised, fail the test
            unittest.IsolatedAsyncioTestCase.fail(
                "Expected subprocess.SubprocessError, but no exception was raised"
            )

# Bitcoin Price Oracle

This Python program estimates the daily USD price of Bitcoin using nothing except a Bitcoin Core node.

It is an adaptation of the script written by [SteveSimple](https://twitter.com/SteveSimple) at [utxo.live](https://utxo.live/oracle/).

## Enhancements
* About ~2x faster than original script (in test comparisons). 
  * For 2023-10-08:
    * original: 62.7 seconds
    * this version: 30.9 seconds
* Uses asynchronous RPC calls when possible.
* Gets RPC config from bitcoin.conf file if available in default ~/.bitcoin folder. Accepts environment variables as alternative. 
* Args allow for getting a range of dates.
* Creates RPC class for async requests to the node.
* Creates Oscillator class
* Creates Stencil class

## bitcoin.conf
In order to run the script successfully your bitcoin.conf file will need additional settings to handle the amount of async requests on the node.

```python
# Accept command line and JSON-RPC commands.
server=1

# Set the number of threads to service RPC calls
rpcthreads=10

# Set the depth of the work queue to service RPC calls
rpcworkqueue=512
```

## Run
Prior to running the program, you must have [Bitcoin Core](https://github.com/bitcoin/bitcoin) installed and running. If you attempt to run the script while the node is syncing, you may run into errors. Best to wait until the node is finished syncing.

- Install requirements `pip install -r requirements.txt`
- Run the script:
  - `python run.py` will provide estimate for previous day.
  - If you want a range of dates: `python run.py --start 2023-01-01 --end 2023-01-07`

## config.py
The config.py module attempts to read the node configuration directly from the bitcoin.conf file itself. If not available (i.e. not in the default ~/.bitcoin folder or path is not provided in code), it checks for the necessary configs in environment variables.

These must be set for the script to work: `datadir`, `rpcuser`, and `rpcpassword`

## Further Improvements
* Instead of using oscillator to find the first block of a day, possibly load all block responses to a PostgreSQL database to further speed up the script.
* Beyond increasing the `rpcworkqueue`, should figure out a way to increase the async abilites of the script. Right now, each day is done consecutively. 
* Dockerize
* More unit testing
# speedtest-cli

Command line interface for testing internet bandwidth using speedtest.net

## Versions

speedtest-cli is written for use with Python 2.4-2.7

speedtest-cli-3 is written for use with Python 3

## Usage

    $ speedtest-cli -h
    usage: speedtest-cli [-h] [--share] [--simple] [--list] [--server SERVER]
    
    Command line interface for testing internet bandwidth using speedtest.net.
    --------------------------------------------------------------------------
    https://github.com/sivel/speedtest-cli
    
    optional arguments:
      -h, --help       show this help message and exit
      --share          Generate and provide a URL to the speedtest.net share
                       results image
      --simple         Suppress verbose output, only show basic information
      --list           Display a list of speedtest.net servers sorted by distance
      --server SERVER  Specify a server ID to test against
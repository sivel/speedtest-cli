# speedtest-cli

Command line interface for testing internet bandwidth using speedtest.net

## Versions

speedtest-cli works with Python 2.4-3.3

## Installation

### pip / easy_install

`pip install speedtest-cli`

or

`easy_install speedtest-cli`

### Github

`pip install git+https://github.com/sivel/speedtest-cli.git`

or

```shell
git clone https://github.com/sivel/speedtest-cli.git
python speedtest-cli/setup.py
```

### Just download (just like the way it was)

```shell
wget -O speedtest-cli https://github.com/sivel/speedtest-cli/raw/master/speedtest_cli.py
chmod +x speedtest-cli
```

or

```shell
curl -o speedtest-cli https://github.com/sivel/speedtest-cli/raw/master/speedtest_cli.py
chmod +x speedtest-cli
```

## Usage

    $ speedtest-cli -h
    usage: speedtest-cli [-h] [--share] [--simple] [--list] [--server SERVER]
                         [--mini MINI]

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
      --mini MINI      URL of the Speedtest Mini server
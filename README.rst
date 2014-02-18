speedtest-cli
=============

Command line interface for testing internet bandwidth using
speedtest.net

.. image:: https://pypip.in/v/speedtest-cli/badge.png
        :target: https://pypi.python.org/pypi/speedtest-cli/
        :alt: Latest Version
.. image:: https://pypip.in/d/speedtest-cli/badge.png
        :target: https://pypi.python.org/pypi//speedtest-cli/
        :alt: Downloads
.. image:: https://pypip.in/license/speedtest-cli/badge.png
        :target: https://pypi.python.org/pypi/speedtest-cli/
        :alt: License

Versions
--------

speedtest-cli works with Python 2.4-3.4

Installation
------------

pip / easy\_install
~~~~~~~~~~~~~~~~~~~

::

    pip install speedtest-cli

or

::

    easy_install speedtest-cli

Github
~~~~~~

::

    pip install git+https://github.com/sivel/speedtest-cli.git

or

::

    git clone https://github.com/sivel/speedtest-cli.git
    python speedtest-cli/setup.py install

Just download (Like the way it used to be)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    wget -O speedtest-cli https://raw.github.com/sivel/speedtest-cli/master/speedtest_cli.py
    chmod +x speedtest-cli

or

::

    curl -o speedtest-cli https://raw.github.com/sivel/speedtest-cli/master/speedtest_cli.py
    chmod +x speedtest-cli

Usage
-----

::

    $ speedtest-cli -h
    usage: speedtest-cli [-h] [--share] [--simple] [--list] [--server SERVER]
                         [--mini MINI] [--source SOURCE] [--version]

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
      --source SOURCE  Source IP address to bind to
      --version        Show the version number and exit


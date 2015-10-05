#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012-2015 Matt Martz
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import re
import sys
import math
import signal
import socket
import timeit
import platform
import threading

__version__ = '0.3.4-e'

# Some global variables we use
user_agent = None
source = None
shutdown_event = None
scheme = 'http'
outfmt = 2

# Messages format
msgsfmts = []
msgsfmts.append(['STCE0010',
                '{"CODE":"STCE0010","VALUE":{"DESCRIPTION":"Could not retrieve speedtest.net configuration: %s"}}',
                'Could not retrieve speedtest.net configuration: %s'])
msgsfmts.append(['STCE0020',
                '{"CODE":"STCE0020","VALUE":{"DESCRIPTION":"Failed to parse speedtest.net configuration"}}',
                'Could not retrieve speedtest.net configuration: %s'])
msgsfmts.append(['STCE0030',
                '{"CODE":"STCE0030","VALUE":{"DESCRIPTION":"Failed to retrieve list of speedtest.net servers: %s"}}',
                'Failed to retrieve list of speedtest.net servers:\n\n %s'])
msgsfmts.append(['STCI0010',
                '{"CODE":"STCI0010","VALUE":{"DESCRIPTION":"Retrieving speedtest.net configuration"}}',
                'Retrieving speedtest.net configuration...'])
msgsfmts.append(['STCE0050',
                '{"CODE":"STCE0050","VALUE":{"DESCRIPTION":"Cannot retrieve speedtest configuration"}}',
                'Cannot retrieve speedtest configuration'])
msgsfmts.append(['STCI0020',
                '{"CODE":"STCI0020","VALUE":{"DESCRIPTION":"Retrieving speedtest.net server list"}}',
                'Retrieving speedtest.net server list...'])
msgsfmts.append(['STCI0030',
                '{"CODE":"STCI0030","VALUE":{"DESCRIPTION":"Testing from", "ISP":"%(isp)s","IP":"%(ip)s"}}',
                'Testing from %(isp)s (%(ip)s)...'])
msgsfmts.append(['STCE0060',
                '{"CODE":"STCE0060","VALUE":{"DESCRIPTION":"Invalid server ID"}}',
                'Invalid server ID'])
msgsfmts.append(['STCE0070',
                '{"CODE":"STCE0070","VALUE":{"DESCRIPTION":"Invalid Speedtest Mini URL"}}',
                'Invalid Speedtest Mini URL'])
msgsfmts.append(['STCI0040',
                '{"CODE":"STCI0040","VALUE":{"DESCRIPTION":"Please provide the full URL of your Speedtest Mini server"}}',
                'Please provide the full URL of your Speedtest Mini server'])
msgsfmts.append(['STCI0050',
                '{"CODE":"STCI0050","VALUE":{"DESCRIPTION":"Selecting best server based on latency"}}',
                'Selecting best server based on latency...'])
msgsfmts.append(['STCI0060',
                '{"CODE":"STCI0060","VALUE":{"DESCRIPTION":"Hosted by", "NAME":"%(sponsor)s","LOCATION":"%(name)s","DISTANCE":"%(d)0.2f km","LATENCY":"%(latency)s ms"}}',
                'Hosted by %(sponsor)s (%(name)s) [%(d)0.2f km]: %(latency)s ms'])
msgsfmts.append(['STCI0070',
                '{"CODE":"STCI0070","VALUE":{"DESCRIPTION":"Ping","LATENCY":"%(latency)s ms"}}',
                'Ping: %(latency)s ms'])
msgsfmts.append(['STCI0080',
                '{"CODE":"STCI0080","VALUE":{"DESCRIPTION":"Testing download speed"}}',
                'Testing download speed...'])
msgsfmts.append(['STCI0090',
                '{"CODE":"STCI0090","VALUE":{"DESCRIPTION":"Download Speed","SPEED":"%0.2f M%s/s"}}',
                'Download: %0.2f M%s/s'])
msgsfmts.append(['STCI0100',
                '{"CODE":"STCI0100","VALUE":{"DESCRIPTION":"Testing upload speed"}}',
                'Testing upload speed...'])
msgsfmts.append(['STCI0110',
                '{"CODE":"STCI0110","VALUE":{"DESCRIPTION":"Upload Speed","SPEED":"%0.2f M%s/s"}}',
                'Upload: %0.2f M%s/s'])
msgsfmts.append(['STCE0080',
                '{"CODE":"STCE0080","VALUE":{"DESCRIPTION":"Cannot generate a speedtest.net share results image while testing against a Speedtest Mini server"}}',
                'Cannot generate a speedtest.net share results image while testing against a Speedtest Mini server'])
msgsfmts.append(['STCE0090',
                '{"CODE":"STCE0090","VALUE":{"DESCRIPTION":"Could not submit results to speedtest.net: %s"}}',
                'Could not submit results to speedtest.net: %s'])
msgsfmts.append(['STCE0100',
                '{"CODE":"STCE0100","VALUE":{"DESCRIPTION":"Could not submit results to speedtest.net"}}',
                'Could not submit results to speedtest.net'])
msgsfmts.append(['STCE0110',
                '{"CODE":"STCE0110","VALUE":{"DESCRIPTION":"Could not submit results to speedtest.net"}}',
                'Could not submit results to speedtest.net'])
msgsfmts.append(['STCI0120',
                '{"CODE":"STCI0120","VALUE":{"DESCRIPTION":"Share results","LINK":"%s://www.speedtest.net/result/%s.png"}}',
                'Share results: %s://www.speedtest.net/result/%s.png'])
msgsfmts.append(['STCI0130',
                '{"CODE":"STCI0130","VALUE":{"DESCRIPTION":"Cancelling"}}',
                'Cancelling...'])
msgsfmts.append(['STCI0140',
                '{"CODE":"STCI0140","VALUE":{"DESCRIPTION":"Entry","ID":"%(id)4s","SPONSOR":"%(sponsor)s","NAME":"%(name)s","COUNTRY":"%(country)s", "DISTANCE":"%(d)0.2f km"}}',
                '%(id)4s) %(sponsor)s (%(name)s, %(country)s) [%(d)0.2f km]'])

# Used for bound_interface
socket_socket = socket.socket

try:
    import xml.etree.cElementTree as ET
except ImportError:
    try:
        import xml.etree.ElementTree as ET
    except ImportError:
        from xml.dom import minidom as DOM
        ET = None

# Begin import game to handle Python 2 and Python 3
try:
    from urllib2 import urlopen, Request, HTTPError, URLError
except ImportError:
    from urllib.request import urlopen, Request, HTTPError, URLError

try:
    from httplib import HTTPConnection, HTTPSConnection
except ImportError:
    e_http_py2 = sys.exc_info()
    try:
        from http.client import HTTPConnection, HTTPSConnection
    except ImportError:
        e_http_py3 = sys.exc_info()
        raise SystemExit('Your python installation is missing required HTTP '
                         'client classes:\n\n'
                         'Python 2: %s\n'
                         'Python 3: %s' % (e_http_py2[1], e_http_py3[1]))

try:
    from Queue import Queue
except ImportError:
    from queue import Queue

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    from urlparse import parse_qs
except ImportError:
    try:
        from urllib.parse import parse_qs
    except ImportError:
        from cgi import parse_qs

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

try:
    from argparse import ArgumentParser as ArgParser
except ImportError:
    from optparse import OptionParser as ArgParser

try:
    import builtins
except ImportError:
    def print_(*args, **kwargs):
        """The new-style print function taken from
        https://pypi.python.org/pypi/six/

        """
        fp = kwargs.pop("file", sys.stdout)
        if fp is None:
            return

        def write(data):
            if not isinstance(data, basestring):
                data = str(data)
            fp.write(data)

        want_unicode = False
        sep = kwargs.pop("sep", None)
        if sep is not None:
            if isinstance(sep, unicode):
                want_unicode = True
            elif not isinstance(sep, str):
                raise TypeError("sep must be None or a string")
        end = kwargs.pop("end", None)
        if end is not None:
            if isinstance(end, unicode):
                want_unicode = True
            elif not isinstance(end, str):
                raise TypeError("end must be None or a string")
        if kwargs:
            raise TypeError("invalid keyword arguments to print()")
        if not want_unicode:
            for arg in args:
                if isinstance(arg, unicode):
                    want_unicode = True
                    break
        if want_unicode:
            newline = unicode("\n")
            space = unicode(" ")
        else:
            newline = "\n"
            space = " "
        if sep is None:
            sep = space
        if end is None:
            end = newline
        for i, arg in enumerate(args):
            if i:
                write(sep)
            write(arg)
        write(end)
else:
    print_ = getattr(builtins, 'print')
    del builtins


class SpeedtestCliServerListError(Exception):
    """Internal Exception class used to indicate to move on to the next
    URL for retrieving speedtest.net server details

    """

def msgfmt(code):
    for i in range(len(msgsfmts)):
        current = msgsfmts[i];
        if current[0] == code:
            return current[outfmt]
    return "<NOMSGFMT>"


def endln():
    if outfmt == 1:
        return ','
    else:
        return '\n'


def endmsg():
    if outfmt == 1:
        return ']'
    else:
        return '\n'

def bound_socket(*args, **kwargs):
    """Bind socket to a specified source IP address"""

    global source
    sock = socket_socket(*args, **kwargs)
    sock.bind((source, 0))
    return sock


def distance(origin, destination):
    """Determine distance between 2 sets of [lat,lon] in km"""

    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) * math.sin(dlon / 2) *
         math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d


def build_user_agent():
    """Build a Mozilla/5.0 compatible User-Agent string"""

    global user_agent
    if user_agent:
        return user_agent

    ua_tuple = (
        'Mozilla/5.0',
        '(%s; U; %s; en-us)' % (platform.system(), platform.architecture()[0]),
        'Python/%s' % platform.python_version(),
        '(KHTML, like Gecko)',
        'speedtest-cli/%s' % __version__
    )
    user_agent = ' '.join(ua_tuple)
    return user_agent


def build_request(url, data=None, headers={}):
    """Build a urllib2 request object

    This function automatically adds a User-Agent header to all requests

    """

    if url[0] == ':':
        schemed_url = '%s%s' % (scheme, url)
    else:
        schemed_url = url

    headers['User-Agent'] = user_agent
    return Request(schemed_url, data=data, headers=headers)


def catch_request(request):
    """Helper function to catch common exceptions encountered when
    establishing a connection with a HTTP/HTTPS request

    """

    try:
        uh = urlopen(request)
        return uh, False
    except (HTTPError, URLError, socket.error):
        e = sys.exc_info()[1]
        return None, e


class FileGetter(threading.Thread):
    """Thread class for retrieving a URL"""

    def __init__(self, url, start):
        self.url = url
        self.result = None
        self.starttime = start
        threading.Thread.__init__(self)

    def run(self):
        self.result = [0]
        try:
            if (timeit.default_timer() - self.starttime) <= 10:
                request = build_request(self.url)
                f = urlopen(request)
                while 1 and not shutdown_event.isSet():
                    self.result.append(len(f.read(10240)))
                    if self.result[-1] == 0:
                        break
                f.close()
        except IOError:
            pass


def downloadSpeed(files, quiet=False):
    """Function to launch FileGetter threads and calculate download speeds"""

    start = timeit.default_timer()

    def producer(q, files):
        for file in files:
            thread = FileGetter(file, start)
            thread.start()
            q.put(thread, True)
            if outfmt == 2 and not quiet and not shutdown_event.isSet():
                sys.stdout.write('.')
                sys.stdout.flush()

    finished = []

    def consumer(q, total_files):
        while len(finished) < total_files:
            thread = q.get(True)
            while thread.isAlive():
                thread.join(timeout=0.1)
            finished.append(sum(thread.result))
            del thread

    q = Queue(6)
    prod_thread = threading.Thread(target=producer, args=(q, files))
    cons_thread = threading.Thread(target=consumer, args=(q, len(files)))
    start = timeit.default_timer()
    prod_thread.start()
    cons_thread.start()
    while prod_thread.isAlive():
        prod_thread.join(timeout=0.1)
    while cons_thread.isAlive():
        cons_thread.join(timeout=0.1)
    return (sum(finished) / (timeit.default_timer() - start))


class FilePutter(threading.Thread):
    """Thread class for putting a URL"""

    def __init__(self, url, start, size):
        self.url = url
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        data = chars * (int(round(int(size) / 36.0)))
        self.data = ('content1=%s' % data[0:int(size) - 9]).encode()
        del data
        self.result = None
        self.starttime = start
        threading.Thread.__init__(self)

    def run(self):
        try:
            if ((timeit.default_timer() - self.starttime) <= 10 and
                    not shutdown_event.isSet()):
                request = build_request(self.url, data=self.data)
                f = urlopen(request)
                f.read(11)
                f.close()
                self.result = len(self.data)
            else:
                self.result = 0
        except IOError:
            self.result = 0


def uploadSpeed(url, sizes, quiet=False):
    """Function to launch FilePutter threads and calculate upload speeds"""

    start = timeit.default_timer()

    def producer(q, sizes):
        for size in sizes:
            thread = FilePutter(url, start, size)
            thread.start()
            q.put(thread, True)
            if outfmt == 2 and not quiet and not shutdown_event.isSet():
                sys.stdout.write('.')
                sys.stdout.flush()
    finished = []

    def consumer(q, total_sizes):
        while len(finished) < total_sizes:
            thread = q.get(True)
            while thread.isAlive():
                thread.join(timeout=0.1)
            finished.append(thread.result)
            del thread

    q = Queue(6)
    prod_thread = threading.Thread(target=producer, args=(q, sizes))
    cons_thread = threading.Thread(target=consumer, args=(q, len(sizes)))
    start = timeit.default_timer()
    prod_thread.start()
    cons_thread.start()
    while prod_thread.isAlive():
        prod_thread.join(timeout=0.1)
    while cons_thread.isAlive():
        cons_thread.join(timeout=0.1)
    return (sum(finished) / (timeit.default_timer() - start))


def getAttributesByTagName(dom, tagName):
    """Retrieve an attribute from an XML document and return it in a
    consistent format

    Only used with xml.dom.minidom, which is likely only to be used
    with python versions older than 2.5
    """
    elem = dom.getElementsByTagName(tagName)[0]
    return dict(list(elem.attributes.items()))


def getConfig():
    """Download the speedtest.net configuration and return only the data
    we are interested in
    """

    request = build_request('://www.speedtest.net/speedtest-config.php')
    uh, e = catch_request(request)
    if e:
        print_(msgfmt('STCE0010') % e, end=endmsg())
        sys.exit(1)
    configxml = []
    while 1:
        configxml.append(uh.read(10240))
        if len(configxml[-1]) == 0:
            break
    if int(uh.code) != 200:
        return None
    uh.close()
    try:
        try:
            root = ET.fromstring(''.encode().join(configxml))
            config = {
                'client': root.find('client').attrib,
                'times': root.find('times').attrib,
                'download': root.find('download').attrib,
                'upload': root.find('upload').attrib}
        except AttributeError:  # Python3 branch
            root = DOM.parseString(''.join(configxml))
            config = {
                'client': getAttributesByTagName(root, 'client'),
                'times': getAttributesByTagName(root, 'times'),
                'download': getAttributesByTagName(root, 'download'),
                'upload': getAttributesByTagName(root, 'upload')}
    except SyntaxError:
        print_(msgfmt('STCE0020'), end=endmsg())
        sys.exit(1)
    del root
    del configxml
    return config

def html_escape(text):
    html_escape_table = { '"': "&quot;" }
    return "".join(html_escape_table.get(c,c) for c in text)

def closestServers(client, all=False):
    """Determine the 5 closest speedtest.net servers based on geographic
    distance
    """

    urls = [
        '://www.speedtest.net/speedtest-servers-static.php',
        '://c.speedtest.net/speedtest-servers-static.php',
        '://www.speedtest.net/speedtest-servers.php',
        '://c.speedtest.net/speedtest-servers.php',
    ]
    errors = []
    servers = {}
    for url in urls:
        try:
            request = build_request(url)
            uh, e = catch_request(request)
            if e:
                errors.append('%s' % e)
                raise SpeedtestCliServerListError
            serversxml = []
            while 1:
                serversxml.append(uh.read(10240))
                if len(serversxml[-1]) == 0:
                    break
            if int(uh.code) != 200:
                uh.close()
                raise SpeedtestCliServerListError
            uh.close()
            try:
                try:
                    root = ET.fromstring(''.encode().join(serversxml))
                    elements = root.getiterator('server')
                except AttributeError:  # Python3 branch
                    root = DOM.parseString(''.join(serversxml))
                    elements = root.getElementsByTagName('server')
            except SyntaxError:
                raise SpeedtestCliServerListError
            for server in elements:
                try:
                    attrib = server.attrib
                except AttributeError:
                    attrib = dict(list(server.attributes.items()))
                d = distance([float(client['lat']),
                              float(client['lon'])],
                             [float(attrib.get('lat')),
                              float(attrib.get('lon'))])
                attrib['d'] = d
                if d not in servers:
                    servers[d] = [attrib]
                else:
                    servers[d].append(attrib)
                if outfmt == 1:
                    attrib['sponsor'] = html_escape(attrib['sponsor'])
            del root
            del serversxml
            del elements
        except SpeedtestCliServerListError:
            continue

        # We were able to fetch and parse the list of speedtest.net servers
        if servers:
            break

    if not servers:
        print_(msgfmt('STCE0030') % '\n'.join(errors), end=endmsg())
        sys.exit(1)

    closest = []
    for d in sorted(servers.keys()):
        for s in servers[d]:
            closest.append(s)
            if len(closest) == 5 and not all:
                break
        else:
            continue
        break

    del servers
    return closest


def getBestServer(servers):
    """Perform a speedtest.net latency request to determine which
    speedtest.net server has the lowest latency
    """

    results = {}
    for server in servers:
        cum = []
        url = '%s/latency.txt' % os.path.dirname(server['url'])
        urlparts = urlparse(url)
        for i in range(0, 3):
            try:
                if urlparts[0] == 'https':
                    h = HTTPSConnection(urlparts[1])
                else:
                    h = HTTPConnection(urlparts[1])
                headers = {'User-Agent': user_agent}
                start = timeit.default_timer()
                h.request("GET", urlparts[2], headers=headers)
                r = h.getresponse()
                total = (timeit.default_timer() - start)
            except (HTTPError, URLError, socket.error):
                cum.append(3600)
                continue
            text = r.read(9)
            if int(r.status) == 200 and text == 'test=test'.encode():
                cum.append(total)
            else:
                cum.append(3600)
            h.close()
        avg = round((sum(cum) / 6) * 1000, 3)
        results[avg] = server
    fastest = sorted(results.keys())[0]
    best = results[fastest]
    best['latency'] = fastest

    return best


def ctrl_c(signum, frame):
    """Catch Ctrl-C key sequence and set a shutdown_event for our threaded
    operations
    """

    global shutdown_event
    shutdown_event.set()
    raise SystemExit(msgfmt('STCI0130'))


def version():
    """Print the version"""

    raise SystemExit(__version__)


def speedtest():
    """Run the full speedtest.net test"""

    global shutdown_event, source, scheme, outfmt
    shutdown_event = threading.Event()

    signal.signal(signal.SIGINT, ctrl_c)

    description = (
        'Command line interface for testing internet bandwidth using '
        'speedtest.net.\n'
        '------------------------------------------------------------'
        '--------------\n'
        'https://github.com/sivel/speedtest-cli')

    parser = ArgParser(description=description)
    # Give optparse.OptionParser an `add_argument` method for
    # compatibility with argparse.ArgumentParser
    try:
        parser.add_argument = parser.add_option
    except AttributeError:
        pass
    parser.add_argument('--bytes', dest='units', action='store_const',
                        const=('byte', 1), default=('bit', 8),
                        help='Display values in bytes instead of bits. Does '
                             'not affect the image generated by --share')
    parser.add_argument('--share', action='store_true',
                        help='Generate and provide a URL to the speedtest.net '
                             'share results image')
    parser.add_argument('--simple', action='store_true',
                        help='Suppress verbose output, only show basic '
                             'information')
    parser.add_argument('--json', dest='outfmt', action='store_const', 
                        const=('json', 1), default=('text', 2), 
                        help='Display info in JSON format')
    parser.add_argument('--list', action='store_true',
                        help='Display a list of speedtest.net servers '
                             'sorted by distance')
    parser.add_argument('--server', help='Specify a server ID to test against')
    parser.add_argument('--mini', help='URL of the Speedtest Mini server')
    parser.add_argument('--source', help='Source IP address to bind to')
    parser.add_argument('--timeout', default=10, type=int,
                        help='HTTP timeout in seconds. Default 10')
    parser.add_argument('--secure', action='store_true',
                        help='Use HTTPS instead of HTTP when communicating '
                             'with speedtest.net operated servers')
    parser.add_argument('--version', action='store_true',
                        help='Show the version number and exit')

    options = parser.parse_args()
    if isinstance(options, tuple):
        args = options[0]
    else:
        args = options
    del options
    outfmt = args.outfmt[1]

    if outfmt == 1:
        print_('[',end='')

    # Print the version and exit
    if args.version:
        version()

    socket.setdefaulttimeout(args.timeout)

    # Pre-cache the user agent string
    build_user_agent()

    # If specified bind to a specific IP address
    if args.source:
        source = args.source
        socket.socket = bound_socket

    if args.secure:
        scheme = 'https'

    if not args.simple:
        print_(msgfmt('STCI0010'), end=endln())
    try:
        config = getConfig()
    except URLError:
        print_(msgfmt('STCE0050'), end=endmsg())
        sys.exit(1)

    if not args.simple:
        print_(msgfmt('STCI0020'), end=endln())
    if args.list or args.server:
        servers = closestServers(config['client'], True)
        if args.list:
            serverList = []
            for server in servers:
                serverList.append(msgfmt('STCI0140') % server)
                if (not server is servers[-1]):
                    serverList.append(endln())
            if outfmt == 2:
                print_(''.join(serverList).encode('utf-8', 'ignore'), end=endmsg())
            else:
                print_(''.join(serverList).encode('utf-8', 'ignore'), end=endmsg())
            sys.exit(0)
    else:
        servers = closestServers(config['client'])

    if not args.simple:
        print_(msgfmt('STCI0030') % config['client'], end=endln())

    if args.server:
        try:
            best = getBestServer(filter(lambda x: x['id'] == args.server, 
                                        servers))
        except IndexError:
            print_(msgfmt('STCE0060'), end=endmsg())
            sys.exit(1)
    elif args.mini:
        name, ext = os.path.splitext(args.mini)
        if ext:
            url = os.path.dirname(args.mini)
        else:
            url = args.mini
        urlparts = urlparse(url)
        try:
            request = build_request(args.mini)
            f = urlopen(request)
        except:
            print_(msgfmt('STCE0070'),end=endmsg())
            sys.exit(1)
        else:
            text = f.read()
            f.close()
        extension = re.findall('upload_extension: "([^"]+)"', text.decode())
        if not extension:
            for ext in ['php', 'asp', 'aspx', 'jsp']:
                try:
                    request = build_request('%s/speedtest/upload.%s' %
                                            (args.mini, ext))
                    f = urlopen(request)
                except:
                    pass
                else:
                    data = f.read().strip()
                    if (f.code == 200 and
                            len(data.splitlines()) == 1 and
                            re.match('size=[0-9]', data)):
                        extension = [ext]
                        break
        if not urlparts or not extension:
            print_(msgfmt('STCI0040'),end=endmsg())
            sys.exit(1)
        servers = [{
            'sponsor': 'Speedtest Mini',
            'name': urlparts[1],
            'd': 0,
            'url': '%s/speedtest/upload.%s' % (url.rstrip('/'), extension[0]),
            'latency': 0,
            'id': 0
        }]
        try:
            best = getBestServer(servers)
        except:
            best = servers[0]
    else:
        if not args.simple:
            print_(msgfmt('STCI0050'),end=endln())
        best = getBestServer(servers)

    if not args.simple:
        print_((msgfmt('STCI0060') % best).encode('utf-8', 'ignore'),end=endln())
    else:
        print_(msgfmt('STCI0070') % best,end=endln())

    sizes = [350, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
    urls = []
    for size in sizes:
        for i in range(0, 4):
            urls.append('%s/random%sx%s.jpg' %
                        (os.path.dirname(best['url']), size, size))
    if not args.simple:
        if outfmt == 2:
            print_(msgfmt('STCI0080'), end='')
        else:
            print_(msgfmt('STCI0080'), end=endln())
    dlspeed = downloadSpeed(urls, args.simple)
    if outfmt == 2 and not args.simple:
        print_()
    print_(msgfmt('STCI0090') %((dlspeed / 1000 / 1000) * args.units[1], args.units[0]),end=endln())

    sizesizes = [int(.25 * 1000 * 1000), int(.5 * 1000 * 1000)]
    sizes = []
    for size in sizesizes:
        for i in range(0, 25):
            sizes.append(size)
    if not args.simple:
        if outfmt == 2:
            print_(msgfmt('STCI0100'), end='')
        else:
            print_(msgfmt('STCI0100'), end=endln())
    ulspeed = uploadSpeed(best['url'], sizes, args.simple)
    if outfmt == 2 and not args.simple:
        print_()
    print_(msgfmt('STCI0110') % ((ulspeed / 1000 / 1000) * args.units[1], args.units[0]), end=endmsg())

    if args.share and args.mini:
        print_(msgfmt('STCE0080'), end=endln())
    elif args.share:
        dlspeedk = int(round((dlspeed / 1000) * 8, 0))
        ping = int(round(best['latency'], 0))
        ulspeedk = int(round((ulspeed / 1000) * 8, 0))

        # Build the request to send results back to speedtest.net
        # We use a list instead of a dict because the API expects parameters
        # in a certain order
        apiData = [
            'download=%s' % dlspeedk,
            'ping=%s' % ping,
            'upload=%s' % ulspeedk,
            'promo=',
            'startmode=%s' % 'pingselect',
            'recommendedserverid=%s' % best['id'],
            'accuracy=%s' % 1,
            'serverid=%s' % best['id'],
            'hash=%s' % md5(('%s-%s-%s-%s' %
                             (ping, ulspeedk, dlspeedk, '297aae72'))
                            .encode()).hexdigest()]

        headers = {'Referer': 'http://c.speedtest.net/flash/speedtest.swf'}
        request = build_request('://www.speedtest.net/api/api.php',
                                data='&'.join(apiData).encode(),
                                headers=headers)
        f, e = catch_request(request)
        if e:
            print_(msgfmt('STCE0090') % e, end=endmsg())
            sys.exit(1)
        response = f.read()
        code = f.code
        f.close()

        if int(code) != 200:
            print_(msgfmt('STCE0100'), end=endmsg())
            sys.exit(1)

        qsargs = parse_qs(response.decode())
        resultid = qsargs.get('resultid')
        if not resultid or len(resultid) != 1:
            print_(msgfmt('STCE0110'), end=endmsg())
            sys.exit(1)

        print_(msgfmt('STCI0120') % (scheme, resultid[0]), end=endmsg())


def main():
    try:
        speedtest()
    except KeyboardInterrupt:
        print_(msgfmt('STCI0130'), end=endmsg())


if __name__ == '__main__':
    main()

# vim:ts=4:sw=4:expandtab
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
import csv
import sys
import math
import signal
import socket
import timeit
import datetime
import platform
import threading

__version__ = '1.0.0'


class FakeShutdownEvent(object):
    """Class to fake a threading.Event.isSet so that users of this module
    are not required to register their own threading.Event()
    """

    @staticmethod
    def isSet():
        "Dummy method to always return false"""
        return False


# Some global variables we use
USER_AGENT = None
SOURCE = None
SHUTDOWN_EVENT = FakeShutdownEvent()
SCHEME = 'http'


# Used for bound_interface
SOCKET_SOCKET = socket.socket

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PY34 = sys.version_info[0:2] >= (3, 4)

# Begin import game to handle Python 2 and Python 3
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        json = None

import xml.parsers.expat
try:
    import xml.etree.cElementTree as ET
except ImportError:
    try:
        import xml.etree.ElementTree as ET
    except ImportError:
        from xml.dom import minidom as DOM
        ET = None

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
    PARSER_TYPE_INT = int
    PARSER_TYPE_STR = str
except ImportError:
    from optparse import OptionParser as ArgParser
    PARSER_TYPE_INT = 'int'
    PARSER_TYPE_STR = 'string'

try:
    from cStringIO import StringIO
except ImportError:
    try:
        from io import StringIO
    except ImportError:
        from StringIO import StringIO

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

# Exception "constants" to support Python 2 through Python 3
try:
    BROKEN_PIPE_ERROR = (BrokenPipeError,)
except NameError:
    BROKEN_PIPE_ERROR = (IOError,)

try:
    import ssl
    HTTP_ERRORS = (HTTPError, URLError, socket.error, ssl.SSLError)
except ImportError:
    HTTP_ERRORS = (HTTPError, URLError, socket.error)


class SpeedtestException(Exception):
    """Base exception for this module"""


class ConfigRetrievalError(SpeedtestException):
    """Could not retrieve config.php"""


class ServersRetrievalError(SpeedtestException):
    """Could not retrieve speedtest-servers.php"""


class InvalidServerIDType(SpeedtestException):
    """Server ID used for filtering was not an integer"""


class NoMatchedServers(SpeedtestException):
    """No servers matched when filtering"""


class SpeedtestMiniConnectFailure(SpeedtestException):
    """Could not connect to the provided speedtest mini server"""


class InvalidSpeedtestMiniServer(SpeedtestException):
    """Server provided as a speedtest mini server does not actually appear
    to be a speedtest mini server
    """


class ShareResultsConnectFailure(SpeedtestException):
    """Could not connect to speedtest.net API to POST results"""


class ShareResultsSubmitFailure(SpeedtestException):
    """Unable to successfully POST results to speedtest.net API after
    connection
    """


class SpeedtestUploadTimeout(SpeedtestException):
    """testlength configuration reached during upload
    Used to ensure the upload halts when no additional data should be sent
    """


def bound_socket(*args, **kwargs):
    """Bind socket to a specified source IP address"""

    sock = SOCKET_SOCKET(*args, **kwargs)
    sock.bind((SOURCE, 0))
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

    global USER_AGENT
    if USER_AGENT:
        return USER_AGENT

    ua_tuple = (
        'Mozilla/5.0',
        '(%s; U; %s; en-us)' % (platform.system(), platform.architecture()[0]),
        'Python/%s' % platform.python_version(),
        '(KHTML, like Gecko)',
        'speedtest-cli/%s' % __version__
    )
    USER_AGENT = ' '.join(ua_tuple)
    return USER_AGENT


def build_request(url, data=None, headers={}):
    """Build a urllib2 request object

    This function automatically adds a User-Agent header to all requests

    """

    if not USER_AGENT:
        build_user_agent()

    if url[0] == ':':
        schemed_url = '%s%s' % (SCHEME, url)
    else:
        schemed_url = url

    headers['User-Agent'] = USER_AGENT
    return Request(schemed_url, data=data, headers=headers)


def catch_request(request):
    """Helper function to catch common exceptions encountered when
    establishing a connection with a HTTP/HTTPS request

    """

    try:
        uh = urlopen(request)
        return uh, False
    except HTTP_ERRORS:
        e = sys.exc_info()[1]
        return None, e


def get_attributes_by_tag_name(dom, tag_name):
    """Retrieve an attribute from an XML document and return it in a
    consistent format

    Only used with xml.dom.minidom, which is likely only to be used
    with python versions older than 2.5
    """
    elem = dom.getElementsByTagName(tag_name)[0]
    return dict(list(elem.attributes.items()))


def print_dots(current, total, start=False, end=False):
    """Built in callback function used by Thread classes for printing
    status
    """

    sys.stdout.write('.')
    if current + 1 == total and end is True:
        sys.stdout.write('\n')
    sys.stdout.flush()


class HTTPDownloader(threading.Thread):
    """Thread class for retrieving a URL"""

    def __init__(self, i, url, start, timeout):
        self.url = url
        self.result = None
        self.starttime = start
        self.timeout = timeout
        self.i = i
        threading.Thread.__init__(self)

    def run(self):
        self.result = [0]
        try:
            if (timeit.default_timer() - self.starttime) <= self.timeout:
                request = build_request(self.url)
                f = urlopen(request)
                while (1 and not SHUTDOWN_EVENT.isSet() and
                        (timeit.default_timer() - self.starttime) <=
                        self.timeout):
                    self.result.append(len(f.read(1500)))
                    if self.result[-1] == 0:
                        break
                f.close()
        except IOError:
            pass


class HTTPUploaderData(object):
    """File like object to improve cutting off the upload once the timeout
    has been reached
    """

    def __init__(self, length, start, timeout):
        self.length = length
        self.start = start
        self.timeout = timeout

        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        multiplier = int(round(int(length) / 36.0))
        self.data = StringIO('content1=%s' %
                             (chars * multiplier)[0:int(length) - 9])

        self.total = [0]

    def read(self, n=1500):
        if ((timeit.default_timer() - self.start) <= self.timeout and
                not SHUTDOWN_EVENT.isSet()):
            chunk = self.data.read(n).encode()
            self.total.append(len(chunk))
            return chunk
        else:
            raise SpeedtestUploadTimeout

    def __len__(self):
        return self.length


class HTTPUploader(threading.Thread):
    """Thread class for putting a URL"""

    def __init__(self, i, url, start, size, timeout):
        self.url = url
        self.data = HTTPUploaderData(size, start, timeout)
        self.size = size
        self.result = None
        self.starttime = start
        self.timeout = timeout
        self.i = i
        threading.Thread.__init__(self)

    def run(self):
        try:
            if ((timeit.default_timer() - self.starttime) <= self.timeout and
                    not SHUTDOWN_EVENT.isSet()):
                try:
                    request = build_request(self.url, data=self.data)
                    f = urlopen(request)
                except TypeError:
                    # PY24 expects a string or buffer
                    # This also causes issues with Ctrl-C, but we will concede
                    # for the moment that Ctrl-C on PY24 isn't immediate
                    request = build_request(self.url,
                                            data=self.data.read(self.size))
                    f = urlopen(request)
                f.read(11)
                f.close()
                self.result = sum(self.data.total)
            else:
                self.result = 0
        except (IOError, SpeedtestUploadTimeout):
            self.result = sum(self.data.total)

        del self.data


class SpeedtestResults(object):
    """Class for holding the results of a speedtest, including:

    Download speed
    Upload speed
    Ping/Latency to test server
    Data about server that the test was run against

    Additionally this class can return a result data as a dictionary or CSV,
    as well as submit a POST of the result data to the speedtest.net API
    to get a share results image link.
    """

    def __init__(self, download=0, upload=0, ping=0, server=None):
        self.download = download
        self.upload = upload
        self.ping = ping
        if server is None:
            self.server = {}
        else:
            self.server = server
        self._share = None
        self.timestamp = datetime.datetime.utcnow().isoformat()

    def __repr__(self):
        return repr(self.dict())

    def share(self):
        """POST data to the speedtest.net API to obtain a share results
        link
        """

        if self._share:
            return self._share

        download = int(round((self.download / 1000) * 8, 0))
        ping = int(round(self.ping, 0))
        upload = int(round((self.upload / 1000) * 8, 0))

        # Build the request to send results back to speedtest.net
        # We use a list instead of a dict because the API expects parameters
        # in a certain order
        api_data = [
            'download=%s' % download,
            'ping=%s' % ping,
            'upload=%s' % upload,
            'promo=',
            'startmode=%s' % 'pingselect',
            'recommendedserverid=%s' % self.server['id'],
            'accuracy=%s' % 1,
            'serverid=%s' % self.server['id'],
            'hash=%s' % md5(('%s-%s-%s-%s' %
                             (ping, upload, download, '297aae72'))
                            .encode()).hexdigest()]

        headers = {'Referer': 'http://c.speedtest.net/flash/speedtest.swf'}
        request = build_request('://www.speedtest.net/api/api.php',
                                data='&'.join(api_data).encode(),
                                headers=headers)
        f, e = catch_request(request)
        if e:
            raise ShareResultsConnectFailure(e)

        response = f.read()
        code = f.code
        f.close()

        if int(code) != 200:
            raise ShareResultsSubmitFailure('Could not submit results to '
                                            'speedtest.net')

        qsargs = parse_qs(response.decode())
        resultid = qsargs.get('resultid')
        if not resultid or len(resultid) != 1:
            raise ShareResultsSubmitFailure('Could not submit results to '
                                            'speedtest.net')

        self._share = 'http://www.speedtest.net/result/%s.png' % resultid[0]

        return self._share

    def dict(self):
        """Return dictionary of result data"""

        return {
            'download': self.download,
            'upload': self.upload,
            'ping': self.ping,
            'server': self.server,
            'timestamp': self.timestamp
        }

    def csv(self, delimiter=','):
        """Return data in CSV format"""

        data = self.dict()
        out = StringIO()
        writer = csv.writer(out, delimiter=delimiter, lineterminator='')
        writer.writerow([data['server']['id'], data['server']['sponsor'],
                         data['server']['name'], data['timestamp'],
                         data['server']['d'], data['ping'], data['download'],
                         data['upload']])
        return out.getvalue()

    def json(self, pretty=False):
        """Return data in JSON format"""

        kwargs = {}
        if pretty:
            kwargs.update({
                'indent': 4,
                'sort_keys': True
            })
        return json.dumps(self.dict(), **kwargs)

    def simple(self, units=('bit', 8)):
        return """Ping: %s ms
Download: %0.2f M%s/s
Upload: %0.2f M%s/s""" % (self.ping,
                          (self.download / 1000 / 1000) * units[1],
                          units[0],
                          (self.upload / 1000 / 1000) * units[1],
                          units[0])


class Speedtest(object):
    """Class for performing standard speedtest.net testing operations"""

    def __init__(self, config=None):
        self.config = {}
        self.get_config()
        if config is not None:
            self.config.update(config)

        self.servers = {}
        self.closest = []
        self.best = {}

        self.results = SpeedtestResults()

    def get_config(self):
        """Download the speedtest.net configuration and return only the data
        we are interested in
        """

        request = build_request('://www.speedtest.net/speedtest-config.php')
        uh, e = catch_request(request)
        if e:
            raise ConfigRetrievalError(e)
        configxml = []

        while 1:
            configxml.append(uh.read(1500))
            if len(configxml[-1]) == 0:
                break
        if int(uh.code) != 200:
            return None

        uh.close()

        try:
            root = ET.fromstring(''.encode().join(configxml))
            server_config = root.find('server-config').attrib
            download = root.find('download').attrib
            upload = root.find('upload').attrib
            times = root.find('times').attrib
            client = root.find('client').attrib

        except AttributeError:
            root = DOM.parseString(''.join(configxml))
            server_config = get_attributes_by_tag_name(root, 'server-config')
            download = get_attributes_by_tag_name(root, 'download')
            upload = get_attributes_by_tag_name(root, 'upload')
            times = get_attributes_by_tag_name(root, 'times')
            client = get_attributes_by_tag_name(root, 'client')

        ignore_servers = map(int, server_config['ignoreids'].split(','))

        sizes = dict(upload=[], download=[])
        for desc, size in times.items():
            if desc.startswith('ul'):
                sizes['upload'].append(int(size))
            elif desc.startswith('dl'):
                sizes['download'].append(int(int(size) / 10000))

        sizes['upload'].sort()
        sizes['download'].sort()

        counts = dict(upload=int(upload['threadsperurl']),
                      download=int(download['threadsperurl']))

        threads = dict(upload=int(upload['threads']),
                       download=int(server_config['threadcount']))

        length = dict(upload=int(upload['testlength']),
                      download=int(download['testlength']))

        self.config.update({
            'client': client,
            'ignore_servers': ignore_servers,
            'sizes': sizes,
            'counts': counts,
            'threads': threads,
            'length': length,
        })

        self.lat_lon = (float(client['lat']), float(client['lon']))

        del root
        del configxml
        return self.config

    def get_servers(self, servers=[]):
        """Retrieve a the list of speedtest.net servers, optionally filtered
        to servers matching those specified in the ``servers`` argument
        """

        for i, s in enumerate(servers):
            try:
                servers[i] = int(s)
            except ValueError:
                raise InvalidServerIDType('%s is an invalid server type, must '
                                          'be int' % s)

        urls = [
            '://www.speedtest.net/speedtest-servers-static.php',
            '://c.speedtest.net/speedtest-servers-static.php',
            '://www.speedtest.net/speedtest-servers.php',
            '://c.speedtest.net/speedtest-servers.php',
        ]

        errors = []
        for url in urls:
            try:
                request = build_request(url)
                uh, e = catch_request(request)
                if e:
                    errors.append('%s' % e)
                    raise ServersRetrievalError

                serversxml = []
                while 1:
                    serversxml.append(uh.read(1500))
                    if len(serversxml[-1]) == 0:
                        break
                if int(uh.code) != 200:
                    uh.close()
                    raise ServersRetrievalError

                uh.close()

                try:
                    try:
                        root = ET.fromstring(''.encode().join(serversxml))
                        elements = root.getiterator('server')
                    except AttributeError:
                        root = DOM.parseString(''.join(serversxml))
                        elements = root.getElementsByTagName('server')
                except (SyntaxError, xml.parsers.expat.ExpatError):
                    raise ServersRetrievalError

                for server in elements:
                    try:
                        attrib = server.attrib
                    except AttributeError:
                        attrib = dict(list(server.attributes.items()))

                    if servers and int(attrib.get('id')) not in servers:
                        continue

                    if int(attrib.get('id')) in self.config['ignore_servers']:
                        continue

                    try:
                        d = distance(self.lat_lon,
                                     (float(attrib.get('lat')),
                                      float(attrib.get('lon'))))
                    except:
                        continue

                    attrib['d'] = d

                    try:
                        self.servers[d].append(attrib)
                    except KeyError:
                        self.servers[d] = [attrib]

                del root
                del serversxml
                del elements

            except ServersRetrievalError:
                continue

        if servers and not self.servers:
            raise NoMatchedServers

        return self.servers

    def set_mini_server(self, server):
        """Instead of querying for a list of servers, set a link to a
        speedtest mini server
        """

        name, ext = os.path.splitext(server)
        if ext:
            url = os.path.dirname(server)
        else:
            url = server

        urlparts = urlparse(url)

        request = build_request(url)
        uh, e = catch_request(request)
        if e:
            raise SpeedtestMiniConnectFailure('Failed to connect to %s' %
                                              server)
        else:
            text = uh.read()
            uh.close()

        extension = re.findall('upload_?[Ee]xtension: "([^"]+)"',
                               text.decode())
        if not extension:
            for ext in ['php', 'asp', 'aspx', 'jsp']:
                try:
                    f = urlopen('%s/speedtest/upload.%s' % (url, ext))
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
            raise InvalidSpeedtestMiniServer('Invalid Speedtest Mini Server: '
                                             '%s' % server)

        self.servers = [{
            'sponsor': 'Speedtest Mini',
            'name': urlparts[1],
            'd': 0,
            'url': '%s/speedtest/upload.%s' % (url.rstrip('/'), extension[0]),
            'latency': 0,
            'id': 0
        }]

        return self.servers

    def get_closest_servers(self, limit=5):
        """Limit servers to the closest speedtest.net servers based on
        geographic distance
        """

        if not self.servers:
            self.get_servers()

        for d in sorted(self.servers.keys()):
            for s in self.servers[d]:
                self.closest.append(s)
                if len(self.closest) == limit:
                    break
            else:
                continue
            break

        return self.closest

    def get_best_server(self, servers=[]):
        """Perform a speedtest.net "ping" to determine which speedtest.net
        server has the lowest latency
        """

        if not servers:
            if not self.closest:
                servers = self.get_closest_servers()
            servers = self.closest

        results = {}
        for server in servers:
            cum = []
            url = os.path.dirname(server['url'])
            urlparts = urlparse('%s/latency.txt' % url)
            for _ in range(0, 3):
                try:
                    if urlparts[0] == 'https':
                        h = HTTPSConnection(urlparts[1])
                    else:
                        h = HTTPConnection(urlparts[1])
                    headers = {'User-Agent': USER_AGENT}
                    start = timeit.default_timer()
                    h.request("GET", urlparts[2], headers=headers)
                    r = h.getresponse()
                    total = (timeit.default_timer() - start)
                except HTTP_ERRORS:
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

        self.results.ping = fastest
        self.results.server = best

        self.best.update(best)
        return best

    def download(self, callback=None):
        """Test download speed against speedtest.net"""

        urls = []
        for size in self.config['sizes']['download']:
            for _ in range(0, self.config['counts']['download']):
                urls.append('%s/random%sx%s.jpg' %
                            (os.path.dirname(self.best['url']), size, size))

        url_count = len(urls)

        start = timeit.default_timer()

        def producer(q, urls, url_count):
            for i, url in enumerate(urls):
                thread = HTTPDownloader(i, url, start,
                                        self.config['length']['download'])
                thread.start()
                q.put(thread, True)
                if not SHUTDOWN_EVENT.isSet() and callback:
                    callback(i, url_count, start=True)

        finished = []

        def consumer(q, url_count):
            while len(finished) < url_count:
                thread = q.get(True)
                while thread.isAlive():
                    thread.join(timeout=0.1)
                finished.append(sum(thread.result))
                if not SHUTDOWN_EVENT.isSet() and callback:
                    callback(thread.i, url_count, end=True)
                del thread

        q = Queue(self.config['threads']['download'])
        prod_thread = threading.Thread(target=producer,
                                       args=(q, urls, url_count))
        cons_thread = threading.Thread(target=consumer, args=(q, url_count))
        start = timeit.default_timer()
        prod_thread.start()
        cons_thread.start()
        while prod_thread.isAlive():
            prod_thread.join(timeout=0.1)
        while cons_thread.isAlive():
            cons_thread.join(timeout=0.1)

        self.results.download = (
            sum(finished) / (timeit.default_timer() - start)
        )
        if self.results.download > 100000:
            self.config['threads']['upload'] = 8
        return self.results.download

    def upload(self, callback=None):
        """Test upload speed against speedtest.net"""

        sizes = []

        for size in self.config['sizes']['upload']:
            for _ in range(0, self.config['counts']['upload']):
                sizes.append(size)

        size_count = len(sizes)

        start = timeit.default_timer()

        def producer(q, sizes, size_count):
            for i, size in enumerate(sizes):
                thread = HTTPUploader(i, self.best['url'], start, size,
                                      self.config['length']['upload'])
                thread.start()
                q.put(thread, True)
                if not SHUTDOWN_EVENT.isSet() and callback:
                    callback(i, size_count, start=True)

        finished = []

        def consumer(q, size_count):
            while len(finished) < size_count:
                thread = q.get(True)
                while thread.isAlive():
                    thread.join(timeout=0.1)
                finished.append(thread.result)
                if not SHUTDOWN_EVENT.isSet() and callback:
                    callback(thread.i, size_count, end=True)
                del thread

        q = Queue(self.config['threads']['upload'])
        prod_thread = threading.Thread(target=producer,
                                       args=(q, sizes, size_count))
        cons_thread = threading.Thread(target=consumer, args=(q, size_count))
        start = timeit.default_timer()
        prod_thread.start()
        cons_thread.start()
        while prod_thread.isAlive():
            prod_thread.join(timeout=0.1)
        while cons_thread.isAlive():
            cons_thread.join(timeout=0.1)

        self.results.upload = (
            sum(finished) / (timeit.default_timer() - start)
        )
        return self.results.upload


def ctrl_c(signum, frame):
    """Catch Ctrl-C key sequence and set a SHUTDOWN_EVENT for our threaded
    operations
    """

    SHUTDOWN_EVENT.set()
    print_('\nCancelling...')
    sys.exit(0)


def version():
    """Print the version"""

    print_(__version__)
    sys.exit(0)


def parse_args():
    """Function to handle building and parsing of command line arguments"""
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
    parser.add_argument('--simple', action='store_true', default=False,
                        help='Suppress verbose output, only show basic '
                             'information')
    parser.add_argument('--csv', action='store_true', default=False,
                        help='Suppress verbose output, only show basic '
                             'information in CSV format')
    parser.add_argument('--csv-delimiter', default=',', type=PARSER_TYPE_STR,
                        help='Single character delimiter to use in CSV '
                             'output. Default ","')
    parser.add_argument('--json', action='store_true', default=False,
                        help='Suppress verbose output, only show basic '
                             'information in JSON format')
    parser.add_argument('--list', action='store_true',
                        help='Display a list of speedtest.net servers '
                             'sorted by distance')
    parser.add_argument('--server', help='Specify a server ID to test against',
                        type=PARSER_TYPE_INT)
    parser.add_argument('--mini', help='URL of the Speedtest Mini server')
    parser.add_argument('--source', help='Source IP address to bind to')
    parser.add_argument('--timeout', default=10, type=PARSER_TYPE_INT,
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
    return args


def validate_optional_args(args):
    """Check if an argument was provided that depends on a module that may
    not be part of the Python standard library.

    If such an argument is supplied, and the module does not exist, exit
    with an error stating which module is missing.
    """
    optional_args = {
        'json': ('json/simplejson', json),
    }

    for arg, info in optional_args.items():
        if getattr(args, arg, False) and info[1] is None:
            raise SystemExit('%s python module is not installed. --%s is '
                             'unavailable' % (info[0], arg))


def printer(string, quiet=False, **kwargs):
    """Helper function to print a string only when not quiet"""

    if not quiet:
        print_(string, **kwargs)


def shell():
    """Run the full speedtest.net test"""

    global SHUTDOWN_EVENT, SOURCE, SCHEME
    SHUTDOWN_EVENT = threading.Event()

    signal.signal(signal.SIGINT, ctrl_c)

    args = parse_args()

    # Print the version and exit
    if args.version:
        version()

    if len(args.csv_delimiter) != 1:
        raise SystemExit('--csv-delimiter must be a single character')

    validate_optional_args(args)

    socket.setdefaulttimeout(args.timeout)

    # Pre-cache the user agent string
    build_user_agent()

    # If specified bind to a specific IP address
    if args.source:
        SOURCE = args.source
        socket.socket = bound_socket

    if args.secure:
        SCHEME = 'https'

    if args.simple or args.csv or args.json:
        quiet = True
    else:
        quiet = False

    # Don't set a callback if we are running quietly
    if quiet:
        callback = None
    else:
        callback = print_dots

    printer('Retrieving speedtest.net configuration...', quiet)
    try:
        speedtest = Speedtest()
    except ConfigRetrievalError:
        printer('Cannot retrieve speedtest configuration')
        sys.exit(1)

    if args.list:
        try:
            speedtest.get_servers()
        except ServersRetrievalError:
            print_('Cannot retrieve speedtest server list')
            sys.exit(1)

        server_list = []
        for _, servers in sorted(speedtest.servers.items()):
            for server in servers:
                line = ('%(id)5s) %(sponsor)s (%(name)s, %(country)s) '
                        '[%(d)0.2f km]' % server)
                try:
                    try:
                        unicode()
                        print_(line.encode('utf-8', 'ignore'))
                    except NameError:
                        print_(line)
                    server_list.append(line)
                except BROKEN_PIPE_ERROR:
                    pass
        sys.exit(0)

    # Set a filter of servers to retrieve
    servers = []
    if args.server:
        servers.append(args.server)

    printer('Testing from %(isp)s (%(ip)s)...' % speedtest.config['client'],
            quiet)

    if not args.mini:
        printer('Retrieving speedtest.net server list...', quiet)
        try:
            speedtest.get_servers(servers)
        except NoMatchedServers:
            print_('No matched servers: %s' % args.server)
            sys.exit(1)
        except ServersRetrievalError:
            print_('Cannot retrieve speedtest server list')
            sys.exit(1)
        except InvalidServerIDType:
            print_('%s is an invalid server type, must be int' % args.server)
            sys.exit(1)

        printer('Selecting best server based on ping...', quiet)
        speedtest.get_best_server()
    elif args.mini:
        speedtest.get_best_server(speedtest.set_mini_server(args.mini))

    results = speedtest.results

    # Python 2.7 and newer seem to be ok with the resultant encoding
    # from parsing the XML, but older versions have some issues.
    # This block should detect whether we need to encode or not
    try:
        unicode()
        printer(('Hosted by %(sponsor)s (%(name)s) [%(d)0.2f km]: '
                 '%(latency)s ms' %
                 results.server).encode('utf-8', 'ignore'), quiet)
    except NameError:
        printer('Hosted by %(sponsor)s (%(name)s) [%(d)0.2f km]: '
                '%(latency)s ms' % results.server, quiet)

    printer('Testing download speed', quiet, end='')
    speedtest.download(callback=callback)
    printer('Download: %0.2f M%s/s' %
            ((results.download / 1000 / 1000) * args.units[1], args.units[0]),
            quiet)

    printer('Testing upload speed', quiet, end='')
    speedtest.upload(callback=callback)
    printer('Upload: %0.2f M%s/s' %
            ((results.upload / 1000 / 1000) * args.units[1], args.units[0]),
            quiet)

    if args.simple:
        print_(results.simple(args.units))
    elif args.csv:
        print_(results.csv(delimiter=args.csv_delimiter))
    elif args.json:
        print_(results.json())

    if args.share:
        printer('Share results: %s' % results.share(), quiet)


def main():
    try:
        shell()
    except KeyboardInterrupt:
        print_('\nCancelling...')
    except (SpeedtestException, SystemExit):
        e = sys.exc_info()[1]
        if getattr(e, 'code', 1) != 0:
            raise SystemExit('ERROR: %s' % e)


if __name__ == '__main__':
    main()

# vim:ts=4:sw=4:expandtab

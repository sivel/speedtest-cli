#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Matt Martz
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

import urllib2
import math
import time
import os
import sys
import threading
from Queue import Queue
from xml.dom import minidom as DOM
try:
    from urlparse import parse_qs
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


def distance(origin, destination):
    """Determine distance between 2 sets of [lat,lon] in km"""

    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2)) * math.sin(dlon / 2)
         * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d


class FileGetter(threading.Thread):
    def __init__(self, url, start):
        self.url = url
        self.result = None
        self.starttime = start
        threading.Thread.__init__(self)

    def get_result(self):
        return self.result

    def run(self):
        try:
            if (time.time() - self.starttime) <= 10:
                f = urllib2.urlopen(self.url)
                self.result = 0
                while 1:
                    contents = f.read(1024)
                    if contents:
                        self.result += len(contents)
                    else:
                        break
                f.close()
            else:
                self.result = 0
        except IOError:
            self.result = 0


def downloadSpeed(files, quiet=False):
    start = time.time()

    def producer(q, files):
        for file in files:
            thread = FileGetter(file, start)
            thread.start()
            q.put(thread, True)
            if not quiet:
                sys.stdout.write('.')
                sys.stdout.flush()

    finished = []

    def consumer(q, total_files):
        while len(finished) < total_files:
            thread = q.get(True)
            thread.join()
            finished.append(thread.result)
            thread.result = 0

    q = Queue(6)
    start = time.time()
    prod_thread = threading.Thread(target=producer, args=(q, files))
    cons_thread = threading.Thread(target=consumer, args=(q, len(files)))
    prod_thread.start()
    cons_thread.start()
    prod_thread.join()
    cons_thread.join()
    return (sum(finished)/(time.time()-start))


class FilePutter(threading.Thread):
    def __init__(self, url, start, size):
        self.url = url
        data = os.urandom(int(size)).encode('hex')
        self.data = 'content1=%s' % data[0:int(size)-9]
        del data
        self.result = None
        self.starttime = start
        threading.Thread.__init__(self)

    def get_result(self):
        return self.result

    def run(self):
        try:
            if (time.time() - self.starttime) <= 10:
                f = urllib2.urlopen(self.url, self.data)
                contents = f.read()
                f.close()
                self.result = len(self.data)
            else:
                self.result = 0
        except IOError:
            self.result = 0


def uploadSpeed(url, sizes, quiet=False):
    start = time.time()

    def producer(q, sizes):
        for size in sizes:
            thread = FilePutter(url, start, size)
            thread.start()
            q.put(thread, True)
            if not quiet:
                sys.stdout.write('.')
                sys.stdout.flush()

    finished = []

    def consumer(q, total_sizes):
        while len(finished) < total_sizes:
            thread = q.get(True)
            thread.join()
            finished.append(thread.result)
            thread.result = 0

    q = Queue(6)
    start = time.time()
    prod_thread = threading.Thread(target=producer, args=(q, sizes))
    cons_thread = threading.Thread(target=consumer, args=(q, len(sizes)))
    prod_thread.start()
    cons_thread.start()
    prod_thread.join()
    cons_thread.join()
    return (sum(finished)/(time.time()-start))


def getAttributesByTagName(dom, tagName):
    elem = dom.getElementsByTagName(tagName)[0]
    return dict(elem.attributes.items())


def getConfig():
    """Download the speedtest.net configuration and return only the data
    we are interested in
    """

    uh = urllib2.urlopen('http://www.speedtest.net/speedtest-config.php')
    configxml = uh.read()
    if int(uh.code) != 200:
        return None
    uh.close()
    root = DOM.parseString(configxml)
    config = {
        'client': getAttributesByTagName(root, 'client'),
        'times': getAttributesByTagName(root, 'times'),
        'download': getAttributesByTagName(root, 'download'),
        'upload': getAttributesByTagName(root, 'upload')}

    del root
    return config


def closestServers(client, all=False):
    """Determine the 5 closest speedtest.net servers based on geographic
    distance
    """

    uh = urllib2.urlopen('http://speedtest.net/speedtest-servers.php')
    serversxml = uh.read()
    if int(uh.code) != 200:
        return None
    uh.close()
    root = DOM.parseString(serversxml)
    servers = {}
    for server in root.getElementsByTagName('server'):
        attrib = dict(server.attributes.items())
        d = distance([float(client['lat']), float(client['lon'])],
                     [float(attrib.get('lat')), float(attrib.get('lon'))])
        attrib['d'] = d
        if d not in servers:
            servers[d] = [attrib]
        else:
            servers[d].append(attrib)

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
    del root
    return closest


def getBestServer(servers):
    """Perform a speedtest.net "ping" to determine which speedtest.net
    server has the lowest latency
    """

    results = {}
    for server in servers:
        cum = 0
        url = os.path.dirname(server['url'])
        for i in xrange(0, 3):
            uh = urllib2.urlopen('%s/latency.txt' % url)
            start = time.time()
            text = uh.read().strip()
            total = time.time() - start
            if int(uh.code) == 200 and text == 'test=test':
                cum += total
            else:
                cum += 3600
            uh.close()
        avg = round((cum / 3) * 1000000, 3)
        results[avg] = server

    fastest = sorted(results.keys())[0]
    best = results[fastest]
    best['latency'] = fastest

    return best


def speedtest():
    """Run the full speedtest.net test"""

    description = (
        'Command line interface for testing internet bandwidth using '
        'speedtest.net.\n'
        '------------------------------------------------------------'
        '--------------\n'
        'https://github.com/sivel/speedtest-cli')

    parser = ArgParser(description=description)
    try:
        parser.add_argument = parser.add_option
    except AttributeError:
        pass
    parser.add_argument('--share', action='store_true',
                        help='Generate and provide a URL to the speedtest.net '
                             'share results image')
    parser.add_argument('--simple', action='store_true',
                        help='Suppress verbose output, only show basic '
                             'information')
    parser.add_argument('--list', action='store_true',
                        help='Display a list of speedtest.net servers '
                             'sorted by distance')
    parser.add_argument('--server', help='Specify a server ID to test against')

    options = parser.parse_args()
    if isinstance(options, tuple):
        args = options[0]
    else:
        args = options
    del options

    if not args.simple:
        print 'Retrieving speedtest.net configuration...'
    config = getConfig()

    if not args.simple:
        print 'Retrieving speedtest.net server list...'
    if args.list or args.server:
        servers = closestServers(config['client'], True)
        if args.list:
            serverList = []
            for server in servers:
                line = ('%(id)4s) %(sponsor)s (%(name)s, %(country)s) '
                        '[%(d)0.2f km]' % server)
                serverList.append(line)
            try:
                print '\n'.join(serverList).encode('utf-8', 'ignore')
            except IOError:
                pass
            sys.exit(0)
    else:
        servers = closestServers(config['client'])

    if not args.simple:
        print 'Testing from %(isp)s (%(ip)s)...' % config['client']

    if args.server:
        try:
            best = getBestServer(filter(lambda x: x['id'] == args.server,
                                        servers))
        except IndexError:
            print 'Invalid server ID'
            sys.exit(1)
    else:
        if not args.simple:
            print 'Selecting best server based on ping...'
        best = getBestServer(servers)

    if not args.simple:
        print ('Hosted by %(sponsor)s (%(name)s) [%(d)0.2f km]: '
               '%(latency)s ms' % best)
    else:
        print 'Ping: %(latency)s ms' % best

    sizes = [350, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
    urls = []
    for size in sizes:
        for i in xrange(0, 4):
            urls.append('%s/random%sx%s.jpg' %
                        (os.path.dirname(best['url']), size, size))
    if not args.simple:
        print 'Testing download speed',
    dlspeed = downloadSpeed(urls, args.simple)
    if not args.simple:
        print
    print 'Download: %0.2f Mbit/s' % ((dlspeed / 1024 / 1024) * 8)

    sizesizes = [int(.25 * 1024 * 1024), int(.5 * 1024 * 1024)]
    sizes = []
    for size in sizesizes:
        for i in xrange(0, 25):
            sizes.append(size)
    if not args.simple:
        print 'Testing upload speed',
    ulspeed = uploadSpeed(best['url'], sizes, args.simple)
    if not args.simple:
        print
    print 'Upload: %0.2f Mbit/s' % ((ulspeed / 1024 / 1024) * 8)

    if args.share:
        dlspeedk = int(round((dlspeed / 1024) * 8, 0))
        ping = int(round(best['latency'], 0))
        ulspeedk = int(round((ulspeed / 1024) * 8, 0))

        apiData = [
            'download=%s' % dlspeedk,
            'ping=%s' % ping,
            'upload=%s' % ulspeedk,
            'promo=',
            'startmode=%s' % 'pingselect',
            'recommendedserverid=%s' % best['id'],
            'accuracy=%s' % 1,
            'serverid=%s' % best['id'],
            'hash=%s' % md5('%s-%s-%s-%s' %
                            (ping, ulspeedk, dlspeedk, '297aae72')
                            ).hexdigest()]

        req = urllib2.Request('http://www.speedtest.net/api/api.php',
                              data='&'.join(apiData))
        req.add_header('Referer', 'http://c.speedtest.net/flash/speedtest.swf')
        f = urllib2.urlopen(req)
        response = f.read()
        code = f.code
        f.close()

        if int(code) != 200:
            print 'Could not submit results to speedtest.net'
            sys.exit(1)

        qsargs = parse_qs(response)
        resultid = qsargs.get('resultid')
        if not resultid or len(resultid) != 1:
            print 'Could not submit results to speedtest.net'
            sys.exit(1)

        print ('Share results: http://www.speedtest.net/result/%s.png' %
               resultid[0])

if __name__ == '__main__':
    try:
        speedtest()
    except KeyboardInterrupt:
        print '\nCancelling...'

# vim:ts=4:sw=4:expandtab

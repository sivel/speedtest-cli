import socket 
import sys
from IN import SO_BINDTODEVICE

class CustomSocket(object):
    def __init__(self, 
                 network_interface=None, 
                 ipv4_source=None, ipv6_source=None, 
                 network_timeout=None):

        if network_interface is not None:
            network_interface = network_interface.strip()[:15] + '\0'
        self.network_interface = network_interface

        if network_timeout is not None:
            network_timeout = float(network_timeout)
        self.network_timeout = network_timeout

        if ipv6_source is not None:
            parsed_ipv6_source = self.parse_source_address(ipv6_source)
            ipv6_source = self.extract_source_address_from_ipv6(parsed_ipv6_source)
        self.ipv6_source = ipv6_source

        if ipv4_source is not None:
            ipv4_source = self.parse_source_address(ipv4_source)
        self.ipv4_source = ipv4_source

    @staticmethod
    def parse_source_address(source_addr):
        source_addr = source_addr.split(',')
        if len(source_addr) == 1:
            return (source_addr[0], 0)
        return (source_addr[0], int(source_addr[1]))

    @staticmethod
    def extract_source_address_from_ipv6(ipv6_source):
        source_ip, source_port = ipv6_source
        source_address = [addr for addr in socket.getaddrinfo(source_ip, source_port, socket.AF_INET6, socket.SOCK_STREAM, socket.SOL_TCP)] 
        if not source_address:
            raise ValueError("Couldn't find ipv6 address for source %s" % source_ip)
        return source_address[0][-1]

    def get_source_address(self, host):
        if ':' in host:
            return self.ipv6_source

        return self.ipv4_source

    def create_connection_with_custom_network_interface(
        self, address, timeout, source_address=None):
        """
        Patched the standard library (v2.7.3) socket.create_connection to 
        connect to a network interface.

        https://github.com/enthought/Python-2.7.3/blob/master/Lib/socket.py#L537
        """
        host, port = address

        for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            sock = None
            try:
                sock = socket.socket(af, socktype, proto)

                if source_address is None:
                    source_address = self.get_source_address(host)

                if self.network_interface:
                    try:
                        sock.setsockopt(socket.SOL_SOCKET, 
                                        SO_BINDTODEVICE, 
                                        self.network_interface)
                    except Exception as e:
                        err_msg = "No device exists: {}".format(self.network_interface)
                        sys.exit(err_msg)
                elif source_address:
                    sock.bind(source_address)

                if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                    sock.settimeout(timeout)
                elif self.network_timeout:
                    sock.settimeout(self.network_timeout)

                sock.connect(sa)

                return sock
            except socket.error as err:
                if sock:
                    sock.close()
                raise err

        raise error("getaddrinfo returns an empty list")
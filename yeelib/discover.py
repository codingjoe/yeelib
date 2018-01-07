import asyncio
import fcntl
import logging
import os
import re
import socket
import struct
import time
from contextlib import contextmanager

from yeelib.bulbs import Bulb
from yeelib.upnp import SSDPRequest, SimpleServiceDiscoveryProtocol
from .exceptions import YeelightError

__all__ = ('search_bulbs', 'YeelightProtocol')

logger = logging.getLogger('yeelib')

MCAST_PORT = 1982
MCAST_ADDR = SimpleServiceDiscoveryProtocol.MULTICAST_ADDRESS, MCAST_PORT


class MutableBoolean:
    __state = True

    def __bool__(self):
        return self.__state

    def set(self, value):
        self.__state = bool(value)


@asyncio.coroutine
def send_search_broadcast(transport, search_interval=30, _running=True):
    request = SSDPRequest('M-SEARCH', headers=[
        ('HOST', '%s:%s' % MCAST_ADDR),
        ('MAN', '"ssdp:discover"'),
        ('ST', 'wifi_bulb'),
    ])
    while _running:
        request.sendto(transport, MCAST_ADDR)
        yield from asyncio.sleep(search_interval)


class YeelightProtocol(SimpleServiceDiscoveryProtocol):
    excluded_headers = ['DATE', 'EXT', 'SERVER', 'CACHE-CONTROL', 'LOCATION']
    location_patter = r'yeelight://(?P<ip>\d{1,3}(\.\d{1,3}){3}):(?P<port>\d+)'

    def __init__(self, bulbs, bulb_class=Bulb):
        self.bulbs = bulbs
        self.bulb_class = bulb_class

    @classmethod
    def header_to_kwargs(cls, headers):
        headers = dict(headers)
        location = headers.get('Location')
        cache_control = headers.get('Cache-Control', 'max-age=3600')
        headers = {
            k: v for k, v in headers.items()
            if k.upper() not in cls.excluded_headers
        }

        match = re.match(cls.location_patter, location)
        if match is None:
            raise YeelightError('Location does not match: %s' % location)
        ip = match.groupdict()['ip']
        port = match.groupdict()['port']

        max_age = int(cache_control.rsplit('=', 1)[-1])

        kwargs = dict(ip=ip, port=port, status_refresh_interv=max_age)
        kwargs.update(headers)
        return kwargs

    def request_received(self, request):
        if request.method == 'M-SEARCH':
            return
        self.register_bulb(**self.header_to_kwargs(request.headers))

    def response_received(self, response):
        self.register_bulb(**self.header_to_kwargs(response.headers))

    def register_bulb(self, **kwargs):
        idx = kwargs['id']
        if idx not in self.bulbs:
            self.bulbs[idx] = self.bulb_class(**kwargs)
        else:
            self.bulbs[idx].last_seen = time.time()


@contextmanager
def _unicast_socket():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as ucast_socket:
        ucast_socket.bind(('', MCAST_PORT))
        fcntl.fcntl(ucast_socket, fcntl.F_SETFL, os.O_NONBLOCK)
        group = socket.inet_aton(
            SimpleServiceDiscoveryProtocol.MULTICAST_ADDRESS)
        mreq = struct.pack("4sl", group, socket.INADDR_ANY)
        ucast_socket.setsockopt(
            socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        yield ucast_socket


@contextmanager
def search_bulbs(bulbs=None, bulb_class=Bulb, loop=None):
    if bulbs is None:
        bulbs = {}
    if loop is None:
        loop = asyncio.get_event_loop()
    multicast_connection = loop.create_datagram_endpoint(
        lambda: YeelightProtocol(bulbs, bulb_class),
        family=socket.AF_INET)
    mcast_transport, _ = loop.run_until_complete(multicast_connection)
    running = MutableBoolean()
    loop.create_task(send_search_broadcast(mcast_transport, _running=running))

    with _unicast_socket() as ucast_socket:
        unicast_connection = loop.create_datagram_endpoint(
            lambda: YeelightProtocol(bulbs, bulb_class),
            sock=ucast_socket)
        ucast_transport, _ = loop.run_until_complete(unicast_connection)
        yield bulbs
    running.set(False)
    ucast_transport.close()
    mcast_transport.close()

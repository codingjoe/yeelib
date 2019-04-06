import asyncio
import fcntl
import logging
import os
import re
import socket
import struct
import time

from ssdp import SSDPRequest, SimpleServiceDiscoveryProtocol

from .devices import Bulb
from .exceptions import YeelightError

__all__ = ('search_bulbs', 'YeelightProtocol', 'bulbs')

logger = logging.getLogger('yeelib')

bulbs = {}

MCAST_PORT = 1982
MCAST_ADDR = SimpleServiceDiscoveryProtocol.MULTICAST_ADDRESS, MCAST_PORT


async def send_search_broadcast(transport, search_interval=30):
    request = SSDPRequest('M-SEARCH', headers=[
        ('HOST', '%s:%s' % MCAST_ADDR),
        ('MAN', '"ssdp:discover"'),
        ('ST', 'wifi_bulb'),
    ])
    while True:
        try:
            request.sendto(transport, MCAST_ADDR)
        except OSError:
            logger.exception("Connection error")
        await asyncio.sleep(search_interval)


class YeelightProtocol(SimpleServiceDiscoveryProtocol):
    excluded_headers = ['DATE', 'EXT', 'SERVER', 'CACHE-CONTROL', 'LOCATION']
    location_patter = r'yeelight://(?P<ip>\d{1,3}(\.\d{1,3}){3}):(?P<port>\d+)'

    def __init__(self, bulb_class=Bulb, loop=None, **kwargs):
        self.bulb_class = bulb_class
        self.bulb_kwargs = kwargs
        self.loop = loop or asyncio.get_event_loop()

    def connection_made(self, transport):
        self.transport = transport
        ucast_socket = transport.get_extra_info('socket')
        try:
            ucast_socket.bind(('', MCAST_PORT))
            fcntl.fcntl(ucast_socket, fcntl.F_SETFL, os.O_NONBLOCK)
            group = socket.inet_aton(
                SimpleServiceDiscoveryProtocol.MULTICAST_ADDRESS)
            mreq = struct.pack("4sl", group, socket.INADDR_ANY)
            ucast_socket.setsockopt(
                socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except socket.error as e:
            ucast_socket.close()
            self.connection_lost(exc=e)
        else:
            self.bcast_msg_task = asyncio.Task(send_search_broadcast(transport))

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

    def request_received(self, request, addr):
        if request.method == 'M-SEARCH':
            return
        self.register_bulb(**self.header_to_kwargs(request.headers))

    def response_received(self, response, addr):
        self.register_bulb(**self.header_to_kwargs(response.headers))

    def register_bulb(self, **kwargs):
        idx = kwargs['id']
        if idx not in bulbs:
            bulbs[idx] = self.bulb_class(**kwargs, **self.bulb_kwargs, _registry=bulbs)
        else:
            bulbs[idx].last_seen = time.time()

    def connection_lost(self, exc):
        logger.exception("connection error")
        self.bcast_msg_task.cancel()
        self.transport.close()

        async def _restart():
            await asyncio.sleep(10)
            await search_bulbs(self.bulb_class, self.loop)

        asyncio.Task(_restart())


async def search_bulbs(bulb_class=Bulb, loop=None, kwargs=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    if kwargs is None:
        kwargs = {}
    unicast_connection = loop.create_datagram_endpoint(
        lambda: YeelightProtocol(bulb_class, **kwargs), family=socket.AF_INET)
    ucast_transport, _ = await unicast_connection
    return bulbs

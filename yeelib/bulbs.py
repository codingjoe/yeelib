import asyncio
import json
import logging
import socket
import time

__all__ = ('Bulb', )

logger = logging.getLogger('yeelib')


class Bulb:
    def __init__(self, ip, port=55443, status_refresh_interval=3600, **kwargs):
        self.ip = ip
        self.port = port
        self.status_refresh_interval = status_refresh_interval

        support = kwargs.pop('support', [])
        if isinstance(support, str):
            support = support.split()
        self.support = support

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.last_seen = time.time()
        self.__command_id = 0
        self.__socket = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket = None

    def __repr__(self):
        return "<%s: %s>" % (type(self).__name__, self.ip)

    @property
    @asyncio.coroutine
    def socket(self):
        if self.__socket is None:
            self.__socket = yield from asyncio.open_connection(
                self.ip, self.port)
        return self.__socket

    @socket.setter
    def socket(self, value):
        try:
            reader, writer = self.__socket
        except TypeError:
            pass
        else:
            writer.close()
        self.__socket = value

    @asyncio.coroutine
    def send_command(self, method, params):
        self.__command_id += 1
        data = {
            'id': self.__command_id,
            'method': method,
            'params': params,
        }
        msg = json.dumps(data) + '\r\n'
        reader, writer = yield from self.socket
        try:
            writer.write(msg.encode())
            logger.debug("%s: >>> %s", self.ip, msg.strip())
        except socket.error:
            logger.exception("Connection error")
            self.socket = None
        else:
            response = (yield from reader.readline()).decode()
            if response is not None:
                logger.debug("%s: ... %s",
                             self.ip, response.strip())
                try:
                    return json.loads(response)
                except ValueError:
                    logger.exception("Could not read message: %s", response)

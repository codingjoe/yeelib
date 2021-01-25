import asyncio
import dataclasses
import json
import logging
import socket
import time

from yeelib.exceptions import YeelightError

__all__ = ("Bulb",)

logger = logging.getLogger("yeelib")


@dataclasses.dataclass
class Bulb:
    ip: str
    port: int
    status_refresh_interv: int
    id: str
    model: str
    fw_ver: str
    power: str
    bright: int
    color_mode: int
    ct: int
    rgb: int
    hue: int
    sat: int
    name: str
    _registry: dict
    support: list = dataclasses.field(default_factory=list)

    manual_override = False
    connection_timeout = 0.1

    def __post_init__(self):
        self.last_seen = time.time()
        self.__command_id = 0
        self.__socket = None
        self.alive = True
        if isinstance(self.support, str):
            self.support = self.support.split()
        asyncio.Task(self.read_notifications())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __repr__(self):
        return "<%s: %s>" % (self.name or self.model, self.ip)

    @property
    async def socket(self):
        if self.__socket is None:
            self.__socket = await asyncio.open_connection(self.ip, self.port)
        return self.__socket

    def __del__(self):
        try:
            reader, writer = self.__socket
        except TypeError:
            pass
        else:
            writer.close()
        finally:
            if self._registry:
                del self._registry[self.ip]

    async def read_notifications(self):
        reader, writer = await self.socket
        while self.alive:
            try:
                response = await reader.readline()
            except ConnectionError:
                logger.warning("%r connection error", self)
                self.__del__()
            except (asyncio.TimeoutError, TimeoutError):
                logger.info("%r connection timeout", self)
                self.__del__()
            except OSError:
                logger.exception("%r unexpected OS error", self)
                self.__del__()
            else:
                try:
                    data = json.loads(response)
                except (json.decoder.JSONDecodeError, TypeError):
                    logger.exception("Could not read message: %s", response)
                    self.__del__()
                else:
                    if "method" in data:
                        logger.debug("%r NOTIFICATION: %s", self, data)
                        if data["method"] == "props":
                            for key, value in data["params"].items():
                                try:
                                    if getattr(self, key) != value:
                                        logger.info("%r was manually overridden", self)
                                        self.manual_override = True
                                except AttributeError:
                                    pass
                                setattr(self, key, value)
                    elif "id" in data:
                        logger.debug("%r RESULT: %s", self, data)

    async def send_command(self, method, params):
        if method not in self.support:
            msg = "The method '%s' is not supported by this bulb." % method
            raise YeelightError(msg)
        self.__command_id += 1
        data = {
            "id": self.__command_id,
            "method": method,
            "params": params,
        }
        msg = json.dumps(data) + "\r\n"
        reader, writer = await self.socket
        try:
            writer.write(msg.encode())
            logger.debug("%r COMMAND: %s", self, msg.strip())
        except socket.error:
            logger.exception("connection error")

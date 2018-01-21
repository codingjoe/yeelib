import asyncio

import pytest

from yeelib.discover import YeelightProtocol, search_bulbs
from yeelib.exceptions import YeelightError
from yeelib import bulbs

from . import fixtures


class TestYeelightProtocoll:
    def test_notify(self, ):
        p = YeelightProtocol()
        p.datagram_received(data=fixtures.request, addr=('192.168.1.239', 1982))
        assert len(bulbs) == 1
        assert bulbs['0x000000000015243f'].ip == '192.168.1.239'

    def test_mcast(self, ):
        p = YeelightProtocol()
        p.datagram_received(data=fixtures.response, addr=('192.168.1.239', 1982))
        assert len(bulbs) == 1
        assert bulbs['0x000000000015243f'].ip == '192.168.1.239'

    def test_duplicate(self):
        p = YeelightProtocol()
        p.datagram_received(data=fixtures.request, addr=('192.168.1.239', 1982))
        p.datagram_received(data=fixtures.request, addr=('192.168.1.239', 1982))
        assert len(bulbs) == 1
        assert bulbs['0x000000000015243f'].ip == '192.168.1.239'

    def test_wrong_location(self):
        p = YeelightProtocol()
        with pytest.raises(YeelightError) as e:
            p.datagram_received(data=fixtures.response_wrong_location,
                                addr=('192.168.1.239', 1982))
        assert 'Location does not match: yeelight://not.an.ip:55443' in str(e)


def test_search_bulbs():
    asyncio.Task(search_bulbs())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.sleep(1))

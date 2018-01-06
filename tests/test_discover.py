import asyncio

import pytest

from yeelib.discover import YeelightProtocol, search_bulbs
from yeelib.exceptions import YeelightError


notify = b"""NOTIFY * HTTP/1.1
Host: 239.255.255.250:1982
Cache-Control: max-age=3600
Location: yeelight://192.168.1.239:55443
NTS: ssdp:alive
Server: POSIX, UPnP/1.0 YGLC/1
id: 0x000000000015243f
model: color
fw_ver: 18
support: get_prop set_default set_power toggle set_bright start_cf stop_cf set_scene
cron_add cron_get cron_del set_ct_abx set_rgb
power: on
bright: 100
color_mode: 2
ct: 4000
rgb: 16711680
hue: 100
sat: 35
name: my_bulb"""

mcast = b"""HTTP/1.1 200 OK
Cache-Control: max-age=3600
Date:
Ext:
Location: yeelight://192.168.1.239:55443
Server: POSIX UPnP/1.0 YGLC/1
id: 0x000000000015243f
model: color
fw_ver: 18
support: get_prop set_default set_power toggle set_bright start_cf stop_cf set_scene
cron_add cron_get cron_del set_ct_abx set_rgb
power: on
bright: 100
color_mode: 2
ct: 4000
rgb: 16711680
hue: 100
sat: 35
name: my_bulb"""

wrong_location = b"""HTTP/1.1 200 OK
Cache-Control: max-age=3600
Date:
Ext:
Location: yeelight://not.an.ip:55443
Server: POSIX UPnP/1.0 YGLC/1"""


class TestYeelightProtocoll:
    def test_notify(self, ):
        bulbs = {}
        p = YeelightProtocol(bulbs=bulbs)
        p.datagram_received(data=notify, addr=('192.168.1.239', 1982))
        assert len(bulbs) == 1
        assert bulbs['0x000000000015243f'].ip == '192.168.1.239'

    def test_mcast(self, ):
        bulbs = {}
        p = YeelightProtocol(bulbs=bulbs)
        p.datagram_received(data=mcast, addr=('192.168.1.239', 1982))
        assert len(bulbs) == 1
        assert bulbs['0x000000000015243f'].ip == '192.168.1.239'

    def test_duplicate(self):
        bulbs = {}
        p = YeelightProtocol(bulbs=bulbs)
        p.datagram_received(data=notify, addr=('192.168.1.239', 1982))
        p.datagram_received(data=notify, addr=('192.168.1.239', 1982))
        assert len(bulbs) == 1
        assert bulbs['0x000000000015243f'].ip == '192.168.1.239'

    def test_wrong_location(self):
        bulbs = {}
        p = YeelightProtocol(bulbs=bulbs)
        with pytest.raises(YeelightError) as e:
            p.datagram_received(data=wrong_location, addr=('192.168.1.239', 1982))
        assert 'Location does not match: yeelight://not.an.ip:55443' in str(e)


def test_search_bulbs():
    loop = asyncio.get_event_loop()
    with search_bulbs():
        loop.run_until_complete(asyncio.sleep(1))

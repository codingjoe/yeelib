import asyncio

from mocket import Mocket, MocketEntry, mocketize

from yeelib import Bulb


class TestBulb:
    bulb_addr = ('192.168.1.239', 55443)

    @mocketize
    def test_send_command(self):
        Mocket.register(MocketEntry(self.bulb_addr, [b'{"id":1, "result":["ok"]}\r\n']))
        with Bulb(*self.bulb_addr, id=1, support=['set_ct_abx']) as b:
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(b.send_command('set_ct_abx', [3500, 'smooth', 500]))

        assert response == {'id': 1, 'result': ['ok']}

    def test_repr(self):
        with Bulb(*self.bulb_addr) as b:
            assert repr(b) == '<Bulb: 192.168.1.239>'

    def test_kwargs(self):
        kwargs = {
            'id': '0x000000000015243f',
            'model': 'color',
            'fw_ver': 18,
            'support': 'get_prop set_default set_power toggle set_bright'
                       ' start_cf stop_cf set_scene cron_add cron_get'
                       ' cron_del set_ct_abx set_rgb',
            'power': 'on',
            'bright': 100,
            'color_mode': 2,
            'ct': 4000,
            'rgb': 16711680,
            'hue': 100,
            'sat': 35,
            'name': 'my_bulb',
        }

        with Bulb(*self.bulb_addr, **kwargs) as b:
            assert b.fw_ver == 18
            assert b.support == ['get_prop', 'set_default', 'set_power', 'toggle', 'set_bright',
                                 'start_cf', 'stop_cf', 'set_scene', 'cron_add', 'cron_get',
                                 'cron_del', 'set_ct_abx', 'set_rgb']

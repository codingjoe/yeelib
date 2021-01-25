import asyncio

from mocket import Mocket, MocketEntry, mocketize

from yeelib import Bulb


class TestBulb:
    bulb_addr = ("192.168.1.239", 55443)

    kwargs = {
        "id": "0x000000000015243f",
        "model": "color",
        "fw_ver": 18,
        "support": "get_prop set_default set_power toggle set_bright"
        " start_cf stop_cf set_scene cron_add cron_get"
        " cron_del set_ct_abx set_rgb",
        "power": "on",
        "bright": 100,
        "color_mode": 2,
        "ct": 4000,
        "rgb": 16711680,
        "hue": 100,
        "sat": 35,
        "name": "my_bulb",
        "status_refresh_interv": 30,
        "_registry": {},
    }

    @mocketize
    def test_send_command(self):
        Mocket.register(MocketEntry(self.bulb_addr, [b'{"id":1, "result":["ok"]}\r\n']))
        with Bulb(
            *self.bulb_addr, **self.kwargs | {"id": 1, "support": ["set_ct_abx"]}
        ) as b:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(b.send_command("set_ct_abx", [3500, "smooth", 500]))

    def test_repr(self):
        with Bulb(*self.bulb_addr, **self.kwargs) as b:
            assert repr(b) == "<my_bulb: 192.168.1.239>"

    def test_kwargs(self):
        with Bulb(*self.bulb_addr, **self.kwargs) as b:
            assert b.fw_ver == 18
            assert b.support == [
                "get_prop",
                "set_default",
                "set_power",
                "toggle",
                "set_bright",
                "start_cf",
                "stop_cf",
                "set_scene",
                "cron_add",
                "cron_get",
                "cron_del",
                "set_ct_abx",
                "set_rgb",
            ]

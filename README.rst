|version| |ci| |coverage| |license|

yeelib
======

**Python library for Xiaomi Mi Yeelight.**

``yeelib`` is an ``asyncio`` based Python library to control Yeelights.
It has no external dependencies and is blazing fast!


Getting Started
---------------

Install

.. code:: shell

    pip install yeelib

Example:

.. code:: python

    import asyncio

    from yeelib import search_bulbs


    @asyncio.coroutine
    def turn_all_lights_on(bulbs):
        while True:
            for b in bulbs.values():
                asyncio.Task(b.send_command("set_power",
                                            ["off", "sudden", 40]))
            yield from asyncio.sleep(10)


    def main():
        loop = asyncio.get_event_loop()
        bulbs = loop.run_until_complete(search_bulbs())
        loop.create_task(turn_all_lights_on(bulbs))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            loop.stop()


    if __name__ == '__main__':
        main()

The script above will turn all off every 10 seconds.
The following script does the same thing, but note how you can define the bulbs
prior calling the ``search_bulbs`` context manager. This works due to the fact
that dictionaries are mutable in Python.


Specifications
--------------

For more information check out the Yeelight developer documentation.
http://www.yeelight.com/download/Yeelight_Inter-Operation_Spec.pdf

.. |version| image:: https://img.shields.io/pypi/v/yeelib.svg
   :target: https://pypi.python.org/pypi/yeelib/
.. |ci| image:: https://api.travis-ci.org/codingjoe/yeelib.svg?branch=master
   :target: https://travis-ci.org/codingjoe/yeelib
.. |coverage| image:: https://codecov.io/gh/codingjoe/yeelib/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/codingjoe/yeelib
.. |license| image:: https://img.shields.io/badge/license-Apache_2-blue.svg
   :target: LICENSE

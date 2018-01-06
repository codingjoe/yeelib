======
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
            print(bulbs)
            for b in bulbs.values():
                asyncio.Task(b.send_command("set_power",
                                            ["off", "sudden", 40]))
            yield from asyncio.sleep(10)


    def main():
        loop = asyncio.get_event_loop()
        with search_bulbs() as bulbs:
            loop.create_task(turn_all_lights_on(bulbs))
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                loop.stop()


    if __name__ == '__main__':
        main()

The script above will turn all off every 10 seconds.
The following script does the same thing, but note how you can define the bulbs
prior calling the ``search_bulbs`` context manager. This works do to the fact
that dictionaries are mutable in Python.

.. code:: python

    import asyncio

    from yeelib import search_bulbs


    @asyncio.coroutine
    def turn_all_lights_on(bulbs):
        while True:
            print(bulbs)
            for b in bulbs.values():
                asyncio.Task(b.send_command("set_power",
                                            ["off", "sudden", 40]))
            yield from asyncio.sleep(10)


    def main():
        bulbs = {}
        asyncio.Task(turn_all_lights_on(bulbs))
        loop = asyncio.get_event_loop()
        try:
            with search_bulbs(bulbs):
                loop.run_forever()
        except KeyboardInterrupt:
            loop.stop()


    if __name__ == '__main__':
        main()


Specifications
--------------

For more information check out the Yeelight developer documentation.
http://www.yeelight.com/download/Yeelight_Inter-Operation_Spec.pdf
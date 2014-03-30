Quickstart
====================================

To start off, rainfall is a micro web framework around asyncio (ex tulip), similiar to the cyclone or tornado. Since it is asyncio based, rainfall is fully asyncronous.

Websocket support is work in progress, should be released soon.

Installation
------------------------------------

As simple as::

    pip install rainfall

.. note::
    sometimes pip for python 3 is called pip3, but you may have it with other name


Hello world
------------------------------------

Let's create a simple hello world app in example.py file like this::

    import asyncio
    from rainfall.web import Application, HTTPHandler


    class HelloHandler(HTTPHandler):
        @asyncio.coroutine
        def handle(self, request):
            return 'Hello!'


    app = Application(
        {
            r'^/$': HelloHandler(),
        },
    )

    if __name__ == '__main__':
        app.run()

Now you can run it by::

    python3 example.py

And go to http://127.0.0.1:8888 in browser, you should see "Hello!"

Docs
======================================

For documentation go to http://rainfall.readthedocs.org/

More examples here https://github.com/mind1master/rainfall/blob/master/rainfall/tests/app.py


Credits
=======================================
Author: Anton Kasyanov (https://github.com/mind1master/)

Contributors: mksh (https://github.com/mksh)

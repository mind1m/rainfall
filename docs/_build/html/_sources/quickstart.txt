
Quickstart
====================================


To start off, rainfall is a micro web framework around asyncio (ex tulip), similiar to the cyclone or tornado. Since it is asyncio based, rainfall is fully asyncronous.

The performance tests have shown that rainfall is not slower then twisted+cyclone and sometimes even faster (benchmark results will be posted later or you can test it by yourself).

Installation
------------------------------------

As simple as::

    pip3 install rainfall

.. note::
    usually pip for python 3 is called pip3, but you may have it with other name


Hello world
------------------------------------

Let's create a simple hello world app in example.py file like this::

    import asyncio
    from rainfall.web import Application, HTTPHandler


    class HelloHandler(HTTPHandler):
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


The structure is the following:

1. First, you create :class:`rainfall.web.HTTPHandler` with required handle() method. It takes :class:`rainfall.http.HTTPRequest` and should return a str or :class:`rainfall.http.HTTPError`
2. Second, you create :class:`rainfall.web.Application`. When a new application is created, you should pass a dict of url: :class:`rainfall.web.HTTPHandler` pairs, where url is regexp telling rainfall when to use this particular handler. If you have experience with Django, this works like django's url patterns.

-------------------------------------
Testing
-------------------------------------

To test the rainfall apps you can use :class:`rainfall.unittest.RainfallTestCase`

Features
====================================


Rainfall comes with a list of features, more are in development.
If you feel that rainfall is missing a feature, please let me know.

Coroutines
------------------------------------

Rainfall's :func:`rainfall.web.HTTPHandler.handle` may be a regular function or `asyncio.coroutine` and use all the asynchronous features like `yield from`.

Example::

    class SleepHandler(HTTPHandler):
        @asyncio.coroutine
        def handle(self, request):
            yield from asyncio.sleep(0.1)
            return 'Done'

Template rendering
------------------------------------

Rainfall uses Jinja2 if you need to render a template.

Example::

    class TemplateHandler(HTTPHandler):
        def handle(self, request):
            return self.render('base.html', text='Rendered')


    settings = {
        'template_path': os.path.join(os.path.dirname(__file__), "templates"),
    }

    app = Application(
        {
            r'^/template$': TemplateHandler(),
        },
        settings=settings,
    )

    app.run()


Url params
------------------------------------
You can easily handle urls with params inside

Example::

    class ParamHandler(HTTPHandler):
        def handle(self, request, number):
            return number

    app = Application(
        {
            r'^/param/(?P<number>\d+)$': ParamHandler(),

        },
    )
    app.run()


GET and POST params
-------------------------------------
Using :attr:`rainfall.http.HTTPRequest.GET` and :attr:`rainfall.http.HTTPRequest.POST` you can easily handle forms data.


Logging
-------------------------------------

Rainfall uses standart python `logging` module.
To configure the file for logs, use `logfile_path` in Application settings.

Testing
-------------------------------------

To test the rainfall apps you can use :class:`rainfall.unittest.RainfallTestCase`

`example.py`::

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

    # this is important for tests
    if __name__ == '__main__':
        app.run()

`test_basic.py`::

    from rainfall.unittest import RainfallTestCase

    from example import app

    class HTTPTestCase(RainfallTestCase):
        app = app

        def test_basic(self):
            r = self.client.query('/')
            self.assertEqual(r.status, 200)
            self.assertEqual(r.body, 'Hello!')

ETag
-------------------------------------

:class:`rainfall.web.HTTPHandler` allows to use ETag for cache validation.

Example::

    class EtagHandler(HTTPHandler):

        use_etag = True
        payload = "PowerOfYourHeart"

        def handle(self, request):
            return self.payload

Then we test it this way::

    def test_etag_wo_ifnonematch(self):
        etag_awaiting = '"' + hashlib.sha1(EtagHandler.payload.encode('utf-8')).hexdigest() + '"'
        r = self.client.query(
            '/etag', method='GET'
        )
        self.assertEqual(r.status, 200)
        self.assertEqual(etag_awaiting, r.headers.get('ETag'))

    def test_etag_with_ifnonematch(self):
        etag_awaiting = '"' + hashlib.sha1(EtagHandler.payload.encode('utf-8')).hexdigest() + '"'
        r = self.client.query(
            '/etag', method='GET',
            headers={
                "If-None-Match": etag_awaiting
            }
        )
        self.assertEqual(r.status, 304)
        self.assertEqual(r.body, '')
        self.assertEqual(etag_awaiting, r.headers.get('ETag'))
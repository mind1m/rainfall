import os
import asyncio
import unittest
import multiprocessing
import http.client
import urllib.parse
import websockets

from .utils import RainfallException


class RainfallTestException(RainfallException):
    pass


class TestClient(object):
    """
    Helper to make request to the rainfall app.
    Created automatically by RainfallTestCase.
    """
    def __init__(self, host, port):
        self.http_connection = http.client.HTTPConnection(host, port)
        self.ws_connections = {}
        self.loop = asyncio.get_event_loop()

    def query(self, url, method='GET', params=None, headers={}):
        """
        Run a query using url and method.
        Returns response object with status, reason, body
        """
        if params:
            params = urllib.parse.urlencode(params)
        self.http_connection.request(method, url, params, headers=headers)
        r = self.http_connection.getresponse()
        r.body = r.read().decode("utf-8")  # converting to unicode
        return r

    @asyncio.coroutine
    def ws_connect(self, url):
        self.ws_connections[url] = self.loop.run_until_complete(websockets.client.connect(url))

    @asyncio.coroutine
    def ws_send(self, url, message):
        if url not in self.ws_connections:
            raise RainfallTestException('No connected websocket to {} found'.format(url))
        self.loop.run_until_complete(self.ws_connections[url].send(message))

    @asyncio.coroutine
    def ws_recv(self, url):
        if url not in self.ws_connections:
            raise RainfallTestException('No connected websocket to {} found'.format(url))
        res = self.loop.run_until_complete(self.ws_connections[url].recv())
        return res

class RainfallTestCase(unittest.TestCase):
    """
    Use it for your rainfall test cases.
    In setUp rainfall server is starting in the separate Process.

    You are required to specify an app variable for tests.
    E.g. ::

        from example import my_first_app


        class HTTPTestCase(RainfallTestCase):
            app = my_first_app

            def test_basic(self):
                r = self.client.query('/')
                self.assertEqual(r.status, 200)
                self.assertEqual(r.body, 'Hello!')

    Inside you can use TestClient's instance via self.client
    """
    app = None  # app to test, specify in your test case

    def setUp(self):
        if not self.app.settings.get('logfile_path'):
            self.app.settings['logfile_path'] = os.path.join(
                os.path.dirname(__file__), 'tests.log'
            )

        q = multiprocessing.Queue()
        self.server_process = multiprocessing.Process(
            target=self.app.run,
            kwargs={'process_queue': q, 'greeting': False}
        )
        self.server_process.start()

        # waiting for server to start
        q.get()

        self.client = TestClient(self.app.settings['host'], self.app.settings['port'])

    def tearDown(self):
        self.server_process.terminate()

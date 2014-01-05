import unittest
import multiprocessing
import http.client, urllib.parse


class TestClient(object):
    def __init__(self, host, port):
        self.conn = http.client.HTTPConnection(host, port)

    def query(self, url, method='GET', params=None):
        """
        Run a query using url and method.
        Returns response with status, reason, body
        """
        if params:
            params = urllib.parse.urlencode(params)
        self.conn.request(method, url, params)
        r = self.conn.getresponse()
        r.body = r.read().decode("utf-8")  # converting to unicode
        return r


class RainfallTestCase(unittest.TestCase):
    app = None  # app to test, specify in your test case

    def setUp(self):
        q = multiprocessing.SimpleQueue()
        self.server_process = multiprocessing.Process(target=self.app.run, kwargs={'silent': True, 'process_queue': q})
        self.server_process.start()

        # waiting for server to start
        while q.empty():
            continue

        self.client = TestClient(self.app.settings['host'], self.app.settings['port'])

    def tearDown(self):
        self.server_process.terminate()


if __name__ == '__main__':
    unittest.main()
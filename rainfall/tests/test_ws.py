from rainfall.unittest import RainfallTestCase
from app import app

class WSTestCase(RainfallTestCase):
    app = app

    def test_ws_echo(self):
        yield from self.client.ws_connect('/ws')
        yield from self.client.ws_send('/ws', 'hello')
        res = yield from self.client.ws_recv('/ws')
        self.assertEqual(res, 'hello')


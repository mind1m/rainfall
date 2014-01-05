from testclient import RainfallTestCase
from app import app

class HTTPTestCase(RainfallTestCase):
    app = app

    def test_basic(self):
        r = self.client.query('/')
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body, 'Hello!')
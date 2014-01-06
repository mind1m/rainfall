import time

from rainfall.unittest import RainfallTestCase
from app import app

class HTTPTestCase(RainfallTestCase):
    app = app

    def test_basic(self):
        r = self.client.query('/')
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body, 'Hello!')

    def test_basic_template(self):
        r = self.client.query('/template')
        self.assertEqual(r.status, 200)
        self.assertTrue('<b>Rendered</b>' in r.body)

    def test_http_error(self):
        r = self.client.query('/http_error')
        self.assertEqual(r.status, 403)

    def test_http_exc(self):
        r = self.client.query('/exc_error')
        self.assertEqual(r.status, 500)

    def test_asyncio_sleep(self):
        start_t = time.time()
        r = self.client.query('/sleep')
        end_t = time.time()
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body, 'Done')
        self.assertTrue(end_t - start_t > 0.1)

    def test_param(self):
        r = self.client.query('/param/2')
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body, '2')

        r = self.client.query('/param/99')
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body, '99')

    def test_form_get(self):
        r = self.client.query('/forms/get?name=Anton&number=42')
        self.assertEqual(r.status, 200)
        self.assertTrue('Name: Anton' in r.body)
        self.assertTrue('Number: 42' in r.body)

    def test_form_post(self):
        r = self.client.query('/forms/post', method='POST',
            params={'name': 'Anton', 'number': 42})

        self.assertEqual(r.status, 200)
        self.assertTrue('Name: Anton' in r.body)
        self.assertTrue('Number: 42' in r.body)

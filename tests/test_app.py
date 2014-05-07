import unittest

from viewer import app


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_index_page_does_not_exist(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 404)

    def tearDown(self):
        pass

#
# Unit tests for the viewer.web package.
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

import unittest

from viewer.web import app


class WebTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_index_page_exists(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)

    def tearDown(self):
        pass

#
# Unit tests for the viewer.format module.
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

import unittest
import datetime

from viewer.format import format_date


class FormatDateTests(unittest.TestCase):
    """Tests for format_date()."""

    def test_returns_correctly_formatted_date(self):
        date = datetime.datetime(2014, 6, 7, 14, 25, 2)
        self.assertEqual(format_date(date), '2014-06-07 14:25:02')

#
# Unit tests for the viewer.format module.
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

import unittest
import datetime

from viewer.format import format_age
from viewer.format import format_date


class FormatAgeWithNonNegativeAgesTests(unittest.TestCase):
    """Tests for format_age() with non-negative values."""

    def test_returns_correctly_formatted_age_zero_seconds(self):
        age = datetime.timedelta(seconds=0)
        self.assertEqual(format_age(age), '0 seconds')

    def test_returns_correctly_formatted_age_one_second(self):
        age = datetime.timedelta(seconds=1)
        self.assertEqual(format_age(age), '1 second')

    def test_returns_correctly_formatted_age_two_seconds(self):
        age = datetime.timedelta(seconds=2)
        self.assertEqual(format_age(age), '2 seconds')

    def test_returns_correctly_formatted_age_max_seconds(self):
        age = datetime.timedelta(seconds=59)
        self.assertEqual(format_age(age), '59 seconds')

    def test_returns_correctly_formatted_age_one_minute(self):
        age = datetime.timedelta(minutes=1)
        self.assertEqual(format_age(age), '1 minute')

    def test_returns_correctly_formatted_age_one_minute_and_some_seconds(self):
        age = datetime.timedelta(minutes=1, seconds=2)
        self.assertEqual(format_age(age), '1 minute')

    def test_returns_correctly_formatted_age_two_minutes(self):
        age = datetime.timedelta(minutes=2)
        self.assertEqual(format_age(age), '2 minutes')

    def test_returns_correctly_formatted_age_two_minutes_and_some_seconds(self):
        age = datetime.timedelta(minutes=2, seconds=5)
        self.assertEqual(format_age(age), '2 minutes')

    def test_returns_correctly_formatted_age_max_minutes(self):
        age = datetime.timedelta(minutes=59, seconds=59)
        self.assertEqual(format_age(age), '59 minutes')

    def test_returns_correctly_formatted_age_one_hour(self):
        age = datetime.timedelta(hours=1)
        self.assertEqual(format_age(age), '1 hour')

    def test_returns_correctly_formatted_age_one_hour_and_some_minutes(self):
        age = datetime.timedelta(hours=1, minutes=5)
        self.assertEqual(format_age(age), '1 hour')

    def test_returns_correctly_formatted_age_two_hours(self):
        age = datetime.timedelta(hours=2)
        self.assertEqual(format_age(age), '2 hours')

    def test_returns_correctly_formatted_age_two_hours_and_some_minutes(self):
        age = datetime.timedelta(hours=2, minutes=5)
        self.assertEqual(format_age(age), '2 hours')

    def test_returns_correctly_formatted_age_max_hours(self):
        age = datetime.timedelta(hours=23, minutes=59, seconds=59)
        self.assertEqual(format_age(age), '23 hours')

    def test_returns_correctly_formatted_age_one_day(self):
        age = datetime.timedelta(days=1)
        self.assertEqual(format_age(age), '1 day')

    def test_returns_correctly_formatted_age_one_day_and_some_hours(self):
        age = datetime.timedelta(days=1, hours=5)
        self.assertEqual(format_age(age), '1 day')

    def test_returns_correctly_formatted_age_two_days(self):
        age = datetime.timedelta(days=2)
        self.assertEqual(format_age(age), '2 days')

    def test_returns_correctly_formatted_age_two_days_and_some_hours(self):
        age = datetime.timedelta(days=2, hours=5)
        self.assertEqual(format_age(age), '2 days')


class FormatAgeWithNegativeAgesTests(unittest.TestCase):
    """Tests for format_age() with negative values."""

    def test_returns_correctly_formatted_age_minus_one_second(self):
        age = datetime.timedelta(seconds=-1)
        self.assertEqual(format_age(age), '-1 second')

    def test_returns_correctly_formatted_age_minus_two_seconds(self):
        age = datetime.timedelta(seconds=-2)
        self.assertEqual(format_age(age), '-2 seconds')

    def test_returns_correctly_formatted_age_minus_max_seconds(self):
        age = datetime.timedelta(seconds=-59)
        self.assertEqual(format_age(age), '-59 seconds')

    def test_returns_correctly_formatted_age_minus_one_minute(self):
        age = datetime.timedelta(minutes=-1)
        self.assertEqual(format_age(age), '-1 minute')

    def test_returns_correctly_formatted_age_minus_one_minute_and_some_seconds(self):
        age = datetime.timedelta(minutes=-1, seconds=-2)
        self.assertEqual(format_age(age), '-1 minute')

    def test_returns_correctly_formatted_age_minus_two_minutes(self):
        age = datetime.timedelta(minutes=-2)
        self.assertEqual(format_age(age), '-2 minutes')

    def test_returns_correctly_formatted_age_minus_two_minutes_and_some_seconds(self):
        age = datetime.timedelta(minutes=-2, seconds=-5)
        self.assertEqual(format_age(age), '-2 minutes')

    def test_returns_correctly_formatted_age_minus_max_minutes(self):
        age = datetime.timedelta(minutes=-59, seconds=-59)
        self.assertEqual(format_age(age), '-59 minutes')

    def test_returns_correctly_formatted_age_minus_one_hour(self):
        age = datetime.timedelta(hours=-1)
        self.assertEqual(format_age(age), '-1 hour')

    def test_returns_correctly_formatted_age_minus_one_hour_and_some_minutes(self):
        age = datetime.timedelta(hours=-1, minutes=-5)
        self.assertEqual(format_age(age), '-1 hour')

    def test_returns_correctly_formatted_age_minus_two_hours(self):
        age = datetime.timedelta(hours=-2)
        self.assertEqual(format_age(age), '-2 hours')

    def test_returns_correctly_formatted_age_minus_two_hours_and_some_minutes(self):
        age = datetime.timedelta(hours=-2, minutes=-5)
        self.assertEqual(format_age(age), '-2 hours')

    def test_returns_correctly_formatted_age_minus_max_hours(self):
        age = datetime.timedelta(hours=-23, minutes=-59, seconds=-59)
        self.assertEqual(format_age(age), '-23 hours')

    def test_returns_correctly_formatted_age_minus_one_day(self):
        age = datetime.timedelta(days=-1)
        self.assertEqual(format_age(age), '-1 day')

    def test_returns_correctly_formatted_age_minus_one_day_and_some_hours(self):
        age = datetime.timedelta(days=-1, hours=-5)
        self.assertEqual(format_age(age), '-1 day')

    def test_returns_correctly_formatted_age_minus_two_days(self):
        age = datetime.timedelta(days=-2)
        self.assertEqual(format_age(age), '-2 days')

    def test_returns_correctly_formatted_age_two_days_and_some_hours(self):
        age = datetime.timedelta(days=-2, hours=-5)
        self.assertEqual(format_age(age), '-2 days')


class FormatDateTests(unittest.TestCase):
    """Tests for format_date()."""

    def test_returns_correctly_formatted_date(self):
        date = datetime.datetime(2014, 6, 7, 14, 25, 2)
        self.assertEqual(format_date(date), '2014-06-07 14:25:02')

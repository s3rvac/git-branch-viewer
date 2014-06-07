#
# Unit tests for the viewer.utils module.
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

import os
import unittest
from unittest import mock

from viewer.utils import chdir


@mock.patch('os.chdir')
class ChdirTests(unittest.TestCase):
    """Tests for the chdir() context manager."""

    def setUp(self):
        self.orig_cwd = os.getcwd()
        self.dst_dir = 'test'

    def test_os_chdir_is_called_with_dst_dir_in_entry(self, mock_chdir):
        with chdir(self.dst_dir):
            mock_chdir.assert_called_once_with(self.dst_dir)

    def test_os_chdir_is_called_with_orig_cwd_in_exit(self, mock_chdir):
        with chdir(self.dst_dir):
            mock_chdir.reset_mock()
        mock_chdir.assert_called_once_with(self.orig_cwd)

    def test_os_chdir_is_called_with_orig_cwd_in_exit_even_if_exception_occurs(
            self, mock_chdir):
        try:
            with chdir(self.dst_dir):
                mock_chdir.reset_mock()
                raise RuntimeError
        except RuntimeError:
            mock_chdir.assert_called_once_with(self.orig_cwd)

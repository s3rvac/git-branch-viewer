#
# Unit tests for the viewer.web package.
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

import unittest
from unittest import mock

import viewer
import viewer.web


class WebTests(unittest.TestCase):
    def setUp(self):
        # Create and initialize a mocked repository.
        self.repo_mock = mock.MagicMock(spec=viewer.git.Repo)
        self.repo_name = 'my testing repo'
        type(self.repo_mock).name = mock.PropertyMock(return_value=self.repo_name)

        # Patch repository creation.
        patcher = mock.patch('viewer.git.Repo', return_value=self.repo_mock)
        self.addCleanup(patcher.stop)
        self.repo_cls_mock = patcher.start()

        self.app = viewer.web.app.test_client()

    def test_index_page_exists(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)

    def test_repo_is_initialized_with_path_from_config(self):
        REPO_PATH = '/path/to/repo'
        viewer.web.app.config['GIT_REPO_PATH'] = REPO_PATH
        rv = self.app.get('/')
        self.repo_cls_mock.assert_called_once_with(REPO_PATH)

    def test_repo_name_is_shown_on_index_page(self):
        rv = self.app.get('/')
        self.assertIn(self.repo_name, rv.data.decode())

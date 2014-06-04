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

from .test_git import get_new_commit


class WebTests(unittest.TestCase):
    """A base class for all web tests."""

    def setUp(self):
        # Create a mocked repository.
        self.repo_mock = mock.MagicMock(spec=viewer.git.Repo)

        # Patch repository creation.
        patcher = mock.patch('viewer.git.Repo', return_value=self.repo_mock)
        self.addCleanup(patcher.stop)
        self.repo_cls_mock = patcher.start()

        self.app = viewer.web.app.test_client()


class GeneralIndexPageTests(WebTests):
    """General tests for the index page."""

    def test_index_page_exists(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)

    def test_repo_is_initialized_with_path_from_config(self):
        REPO_PATH = '/path/to/repo'
        viewer.web.app.config['GIT_REPO_PATH'] = REPO_PATH
        rv = self.app.get('/')
        self.repo_cls_mock.assert_called_once_with(REPO_PATH)

    def test_repo_name_is_shown_on_index_page(self):
        REPO_NAME = 'my testing repo'
        type(self.repo_mock).name = mock.PropertyMock(return_value=REPO_NAME)
        rv = self.app.get('/')
        self.assertIn(REPO_NAME, rv.data.decode())

    def test_remote_is_shown_on_index_page(self):
        REMOTE = 'test_remote'
        viewer.web.app.config['GIT_REMOTE'] = REMOTE
        rv = self.app.get('/')
        self.assertIn(REMOTE, rv.data.decode())


class BranchesOnIndexPageTests(WebTests):
    """Tests for the branches shown on the index page."""

    def setUp(self):
        super().setUp()
        self.REMOTE = 'test_remote'
        self.BRANCHES = [
            viewer.git.Branch(self.repo_mock, self.REMOTE, 'test_branch1'),
            viewer.git.Branch(self.repo_mock, self.REMOTE, 'test_branch2')
        ]

    def test_remote_from_config_is_used_when_getting_branches(self):
        viewer.web.app.config['GIT_REMOTE'] = self.REMOTE
        rv = self.app.get('/')
        self.repo_mock.get_branches_on_remote.assert_called_with(self.REMOTE)

    def test_branches_are_shown_on_index_page(self):
        self.repo_mock.get_branches_on_remote.return_value = self.BRANCHES
        rv = self.app.get('/')
        for branch in self.BRANCHES:
            self.assertIn(branch.name, rv.data.decode())

    def test_commit_for_each_branch_is_shown_on_index_page(self):
        COMMIT = get_new_commit()
        self.repo_mock.get_branches_on_remote.return_value = self.BRANCHES
        # For simplicity, we return the same commit for every branch.
        self.repo_mock.get_commit_for_branch.return_value = COMMIT
        rv = self.app.get('/')
        # We check just some of the commit's data because what is actually
        # shown and in what format may differ over time.
        self.assertIn(COMMIT.short_hash(), rv.data.decode())
        self.assertIn(COMMIT.author, rv.data.decode())
        self.assertIn(COMMIT.email, rv.data.decode())

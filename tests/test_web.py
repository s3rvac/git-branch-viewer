#
# Unit tests for the viewer.web package.
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

import re
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
        self.app.get('/')
        self.repo_cls_mock.assert_called_once_with(REPO_PATH)

    def test_repo_name_is_shown(self):
        REPO_NAME = 'my testing repo'
        type(self.repo_mock).name = mock.PropertyMock(return_value=REPO_NAME)
        rv = self.app.get('/')
        self.assertIn(REPO_NAME, rv.data.decode())

    def test_remote_is_shown(self):
        REMOTE = 'test_remote'
        viewer.web.app.config['GIT_REMOTE'] = REMOTE
        rv = self.app.get('/')
        self.assertIn(REMOTE, rv.data.decode())

    def test_link_to_project_on_github_is_shown_in_footer(self):
        rv = self.app.get('/')
        EXPECTED_RE = re.compile(r"""
            id="footer".*
            <a[^>]+href="https://github.com/s3rvac/git-branch-viewer"[^>]*>Git\ Branch\ Viewer</a>
            """, re.VERBOSE | re.MULTILINE | re.DOTALL)
        self.assertRegex(rv.data.decode(), EXPECTED_RE)


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
        self.app.get('/')
        self.repo_mock.get_branches_on_remote.assert_called_with(self.REMOTE)

    def test_branches_are_shown(self):
        self.repo_mock.get_branches_on_remote.return_value = self.BRANCHES
        rv = self.app.get('/')
        for branch in self.BRANCHES:
            self.assertIn(branch.name, rv.data.decode())

    def test_branches_to_be_ignored_are_ignored(self):
        self.repo_mock.get_branches_on_remote.return_value = self.BRANCHES
        IGNORED_BRANCH_NAME = self.BRANCHES[1].name
        viewer.web.app.config['GIT_BRANCHES_TO_IGNORE'] = [IGNORED_BRANCH_NAME]
        rv = self.app.get('/')
        EXPECTED_RE = re.compile(r'.*Ignored.*{}'.format(IGNORED_BRANCH_NAME),
            re.MULTILINE | re.DOTALL)
        self.assertRegex(rv.data.decode(), EXPECTED_RE)


class CommitsOnIndexPageTests(WebTests):
    """Tests for the commits shown on the index page."""

    def setUp(self):
        super().setUp()
        self.REMOTE = 'test_remote'
        self.BRANCH = viewer.git.Branch(self.repo_mock, self.REMOTE, 'test_branch')
        self.repo_mock.get_branches_on_remote.return_value = [self.BRANCH]

    def test_commit_for_branch_is_shown(self):
        COMMIT = get_new_commit()
        self.repo_mock.get_commit_for_branch.return_value = COMMIT
        rv = self.app.get('/')
        # We check just some of the commit's data because what is actually
        # shown and in what format may differ over time.
        self.assertIn(COMMIT.short_hash(), rv.data.decode())
        self.assertIn(COMMIT.author, rv.data.decode())
        self.assertIn(COMMIT.email, rv.data.decode())

    def test_commit_hash_is_link_to_commit_details_taken_from_config(self):
        COMMIT = get_new_commit()
        self.repo_mock.get_commit_for_branch.return_value = COMMIT
        COMMIT_DETAILS_URL_FMT = 'http://show-commit.net/{}'
        viewer.web.app.config['COMMIT_DETAILS_URL_FMT'] = COMMIT_DETAILS_URL_FMT
        rv = self.app.get('/')
        COMMIT_DETAILS_URL = COMMIT_DETAILS_URL_FMT.format(COMMIT.hash)
        EXPECTED_RE = re.compile(r'<a[^>]+href="{}"[^>]*>{}</a>'.format(
            COMMIT_DETAILS_URL, COMMIT.short_hash()), re.MULTILINE)
        self.assertRegex(rv.data.decode(), EXPECTED_RE)

    def test_when_commit_details_url_fmt_is_not_set_no_commit_url_us_shown(self):
        COMMIT = get_new_commit()
        self.repo_mock.get_commit_for_branch.return_value = COMMIT
        viewer.web.app.config['COMMIT_DETAILS_URL_FMT'] = None
        rv = self.app.get('/')
        NOT_EXPECTED_RE = r'{}</a>'.format(COMMIT.short_hash())
        self.assertNotRegex(rv.data.decode(), NOT_EXPECTED_RE)

    def test_author_is_link_to_his_or_her_email(self):
        COMMIT = get_new_commit()
        self.repo_mock.get_commit_for_branch.return_value = COMMIT
        rv = self.app.get('/')
        EXPECTED_RE = re.compile(r'<a[^>]+href="mailto:{}"[^>]*>{}</a>'.format(
            COMMIT.email, COMMIT.author), re.MULTILINE)
        self.assertRegex(rv.data.decode(), EXPECTED_RE)

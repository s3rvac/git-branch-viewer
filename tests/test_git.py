#
# Unit tests for the viewer.git module.
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

import os
import subprocess
import unittest
from unittest import mock

from viewer.git import Git
from viewer.git import GitCmdNotFoundError
from viewer.git import NoGitRepositoryError


@mock.patch('os.chdir')
@mock.patch('subprocess.check_call')
class GitCreateTests(unittest.TestCase):
    def test_create_git_from_existing_repository_enters_the_repo_and_calls_git_status(
            self, mock_check_call, mock_chdir):
        REPO_PATH = '/path/to/existing/repository'
        git = Git(REPO_PATH)
        mock_chdir.assert_any_call(REPO_PATH)
        mock_check_call.assert_called_once_with(['git', 'status'])

    def test_create_git_from_nonexisting_location_raises_exception(
            self, mock_check_call, mock_chdir):
        mock_chdir.side_effect = FileNotFoundError('No such file or directory')
        REPO_PATH = '/path/to/nonexisting/location'
        self.assertRaises(FileNotFoundError, Git, REPO_PATH)

    def test_create_git_from_location_with_no_repository_raises_exception(
            self, mock_check_call, mock_chdir):
        mock_check_call.side_effect = subprocess.CalledProcessError(
            128, "['git', 'status']",
            b'fatal: Not a git repository (or any parent up to mount point)')
        REPO_PATH = '/path/to/existing/location/with/no/repository'
        self.assertRaises(NoGitRepositoryError, Git, REPO_PATH)
        mock_check_call.assert_called_once_with(['git', 'status'])

    def test_exception_is_raised_when_git_is_not_installed(
            self, mock_check_call, mock_chdir):
        mock_check_call.side_effect = FileNotFoundError(
            "[Errno 2] No such file or directory: 'git'")
        REPO_PATH = '/path/to/existing/location/with/norepository'
        self.assertRaises(GitCmdNotFoundError, Git, REPO_PATH)
        mock_check_call.assert_called_once_with(['git', 'status'])

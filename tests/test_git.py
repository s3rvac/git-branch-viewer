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
from viewer.git import NoGitRepositoryError


class GitCreateTests(unittest.TestCase):
    @mock.patch('os.chdir')
    @mock.patch('subprocess.check_call')
    def test_create_git_from_existing_repository_enters_the_repo_and_calls_git_status(
            self, mock_check_call, mock_chdir):
        REPO_PATH = '/path/to/existing/repository'
        git = Git(REPO_PATH)
        mock_chdir.assert_any_call(REPO_PATH)
        mock_check_call.assert_called_once_with(['git', 'status'])

    @mock.patch('os.chdir',
        side_effect=FileNotFoundError('No such file or directory'))
    def test_create_git_from_nonexisting_location_raises_exception(self,
            mock_chdir):
        REPO_PATH = '/path/to/nonexisting/location'
        self.assertRaises(FileNotFoundError, Git, REPO_PATH)

    @mock.patch('os.chdir')
    @mock.patch('subprocess.check_call',
        side_effect=subprocess.CalledProcessError(128, "['git', 'status']",
            b'fatal: Not a git repository (or any parent up to mount point)'))
    def test_create_git_from_location_with_no_repository_raises_exception(self,
            mock_check_call, mock_chdir):
        REPO_PATH = '/path/to/existing/location/with/norepository'
        self.assertRaises(NoGitRepositoryError, Git, REPO_PATH)
        mock_check_call.assert_called_once_with(['git', 'status'])

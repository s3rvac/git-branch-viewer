#
# Unit tests for the viewer.git module.
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

import subprocess
import unittest
from unittest import mock

from viewer.git import Git
from viewer.git import GitBinaryNotFoundError
from viewer.git import GitCmdError


class GitTests(unittest.TestCase):
    """A base class for all git tests."""

    def setUp(self):
        # Patch os.chdir.
        patcher = mock.patch('os.chdir')
        self.addCleanup(patcher.stop)
        self.mock_chdir = patcher.start()

        # Patch subprocess.check_output.
        patcher = mock.patch('subprocess.check_output')
        self.addCleanup(patcher.stop)
        self.mock_check_output = patcher.start()


class GitCreateTests(GitTests):
    """Tests for Git.__init__()."""

    def test_create_git_from_repository_enters_the_repo_and_calls_git_status(self):
        REPO_PATH = '/path/to/existing/repository'
        Git(REPO_PATH)
        self.mock_chdir.assert_any_call(REPO_PATH)
        self.mock_check_output.assert_called_once_with(['git', 'status'])

    def test_path_is_accessible_after_creating_git_from_existing_repository(self):
        REPO_PATH = '/path/to/existing/repository'
        git = Git(REPO_PATH)
        self.assertEqual(git.path, REPO_PATH)

    def test_create_git_from_nonexisting_location_raises_exception(self):
        self.mock_chdir.side_effect = FileNotFoundError('No such file or directory')
        REPO_PATH = '/path/to/nonexisting/location'
        self.assertRaises(FileNotFoundError, Git, REPO_PATH)

    def test_create_git_from_location_with_no_repository_raises_exception(self):
        self.mock_check_output.side_effect = subprocess.CalledProcessError(
            128, "['git', 'status']",
            b'fatal: Not a git repository (or any parent up to mount point)')
        REPO_PATH = '/path/to/existing/location/with/no/repository'
        self.assertRaises(GitCmdError, Git, REPO_PATH)
        self.mock_check_output.assert_called_once_with(['git', 'status'])

    def test_exception_is_raised_when_git_binary_is_not_found(self):
        # FileNotFoundError is raised when the command does not exist.
        self.mock_check_output.side_effect = FileNotFoundError(
            "[Errno 2] No such file or directory: 'git'")
        REPO_PATH = '/path/to/existing/location/with/norepository'
        self.assertRaises(GitBinaryNotFoundError, Git, REPO_PATH)
        self.mock_check_output.assert_called_once_with(['git', 'status'])


class RunGitCmdTests(GitTests):
    """Tests for Git.run_git_cmd()."""

    def setUp(self):
        super().setUp()
        self.git = Git('/path/to/existing/repository')

    def test_git_status_returns_output(self):
        GIT_STATUS_OUTPUT = 'The output from git status.'
        self.mock_check_output.return_value = GIT_STATUS_OUTPUT
        self.assertEqual(self.git.run_git_cmd(['status']), GIT_STATUS_OUTPUT)

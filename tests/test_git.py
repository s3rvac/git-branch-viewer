#
# Unit tests for the viewer.git module.
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

import datetime
import random
import subprocess
import unittest
from unittest import mock

from viewer.git import Branch
from viewer.git import Commit
from viewer.git import Git
from viewer.git import GitBinaryNotFoundError
from viewer.git import GitCmdError


class CommitTests(unittest.TestCase):
    """Tests for the Commit class."""

    def setUp(self):
        self.hash = '1795de317458e658f8134ae76d668c8539043c28'
        self.author = 'Petr Zemek'
        self.email = 's3rvac@gmail.com'
        self.date = datetime.date.today()
        self.commit = Commit(self.hash, self.author, self.email, self.date)

    def test_data_passed_into_constructor_are_accessible_after_creation(self):
        self.assertEqual(self.commit.hash, self.hash)
        self.assertEqual(self.commit.author, self.author)
        self.assertEqual(self.commit.email, self.email)
        self.assertEqual(self.commit.date, self.date)

    def test_short_hash_returns_correct_result(self):
        self.assertEqual(self.commit.short_hash(), self.hash[:8])
        self.assertEqual(self.commit.short_hash(10), self.hash[:10])

    def test_value_error_is_raised_when_hash_has_invalid_length(self):
        with self.assertRaises(ValueError):
            Commit('', 'PZ', 'pz@pz.net', datetime.date.today())
        with self.assertRaises(ValueError):
            Commit('abcdef', 'PZ', 'pz@pz.net', datetime.date.today())
        with self.assertRaises(ValueError):
            Commit('a'*41, 'PZ', 'pz@pz.net', datetime.date.today())


def get_new_commit(hash=None, author=None, email=None, date=None):
    """Returns a new commit, possibly based on the given data (if not None)."""
    def get_rand_hash():
        return ''.join(random.choice('0123456789abcdef') for _ in range(40))

    hash = hash or get_rand_hash()
    author = author or 'Petr Zemek'
    email = email or 's3rvac@gmail.com'
    date = datetime.date.today()
    return Commit(hash, author, email, date)


class BranchTests(unittest.TestCase):
    """Tests for the Branch class."""

    def test_data_passed_into_constructor_are_accessible_after_creation(self):
        name = 'remotes/origin/test'
        commit = get_new_commit()
        unmerged_commits = [get_new_commit() for _ in range(5)]
        branch = Branch(name, commit, unmerged_commits)
        self.assertEqual(branch.name, name)
        self.assertEqual(branch.commit, commit)
        self.assertEqual(branch.unmerged_commits, unmerged_commits)


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

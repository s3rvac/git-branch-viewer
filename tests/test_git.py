#
# Unit tests for the viewer.git module.
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

import random
import subprocess
import unittest
import datetime
from unittest import mock

from viewer.git import Branch
from viewer.git import Commit
from viewer.git import Git
from viewer.git import GitBinaryNotFoundError
from viewer.git import GitCmdError


def get_curr_date():
    """Returns the current date."""
    return datetime.datetime.now()


def get_rand_hash(characters=Commit.VALID_HASH_CHARACTERS):
    """Returns a new, random hash from the given characters"""
    return ''.join(random.choice(
        list(characters)) for _ in range(Commit.VALID_HASH_LENGTH))


class CommitCreateAndAccessTests(unittest.TestCase):
    """Tests for Commit.__init__() and accessors."""

    def setUp(self):
        self.hash = get_rand_hash()
        self.author = 'Petr Zemek'
        self.email = 's3rvac@gmail.com'
        self.date = get_curr_date()
        self.commit = Commit(self.hash, self.author, self.email, self.date)

    def test_valid_hash_length_has_proper_value(self):
        self.assertEqual(Commit.VALID_HASH_LENGTH, 40)

    def test_valid_hash_characters_has_proper_value(self):
        self.assertEqual(Commit.VALID_HASH_CHARACTERS, set('abcdef0123456789'))

    def test_data_passed_into_constructor_are_accessible_after_creation(self):
        self.assertEqual(self.commit.hash, self.hash)
        self.assertEqual(self.commit.author, self.author)
        self.assertEqual(self.commit.email, self.email)
        self.assertEqual(self.commit.date, self.date)

    def test_short_hash_returns_correct_result(self):
        self.assertEqual(self.commit.short_hash(), self.hash[:8])
        self.assertEqual(self.commit.short_hash(10), self.hash[:10])

    def test_hash_is_properly_normalized(self):
        hash = get_rand_hash('ABCDEF')
        commit = Commit(hash, 'PZ', 'pz@pz.net', get_curr_date())
        self.assertEqual(commit.hash, hash.lower())

    def test_value_error_is_raised_when_hash_has_invalid_length(self):
        with self.assertRaises(ValueError):
            Commit('', 'PZ', 'pz@pz.net', get_curr_date())
        with self.assertRaises(ValueError):
            Commit('abcdef', 'PZ', 'pz@pz.net', get_curr_date())
        with self.assertRaises(ValueError):
            Commit('a' * (Commit.VALID_HASH_LENGTH + 1),
                'PZ', 'pz@pz.net', get_curr_date())

    def test_value_error_is_raised_when_hash_has_invalid_characters(self):
        with self.assertRaises(ValueError):
            Commit((Commit.VALID_HASH_LENGTH - 1) * 'a' + 'g',
                'PZ', 'pz@pz.net', get_curr_date())

    def test_hash_is_validated_when_set_after_creation(self):
        with self.assertRaises(ValueError):
            self.commit.hash = ''


class CommitComparisonTests(unittest.TestCase):
    """Tests for commit comparison."""

    def test_two_identical_commits_are_equal(self):
        commit = Commit(get_rand_hash(), 'PZ', 'pz@pz.net', get_curr_date())
        self.assertEqual(commit, commit)

    def test_two_commits_with_equal_data_are_equal(self):
        hash = get_rand_hash()
        author = 'PZ'
        email = 'pz@pz.net'
        date = get_curr_date()
        commit1 = Commit(hash, author, email, date)
        commit2 = Commit(hash, author, email, date)
        self.assertEqual(commit1, commit2)

    def test_two_commits_with_different_hash_are_not_equal(self):
        author = 'PZ'
        email = 'pz@pz.net'
        date = get_curr_date()
        commit1 = Commit(get_rand_hash(), author, email, date)
        commit2 = Commit(get_rand_hash(), author, email, date)
        self.assertNotEqual(commit1, commit2)

    def test_two_commits_with_different_author_are_not_equal(self):
        hash = get_rand_hash()
        email = 'pz@pz.net'
        date = get_curr_date()
        commit1 = Commit(hash, 'Petr Zemek', email, date)
        commit2 = Commit(hash, 'PZ', email, date)
        self.assertNotEqual(commit1, commit2)

    def test_two_commits_with_different_email_are_not_equal(self):
        hash = get_rand_hash()
        author = 'PZ'
        date = get_curr_date()
        commit1 = Commit(hash, author, 'pz@pz.net', date)
        commit2 = Commit(hash, author, 's3rvac@gmail.com', date)
        self.assertNotEqual(commit1, commit2)

    def test_two_commits_with_different_date_are_not_equal(self):
        hash = get_rand_hash()
        author = 'PZ'
        email = 'pz@pz.net'
        commit1 = Commit(hash, author, email,
            datetime.datetime(2007, 12, 11, 5, 43, 14))
        commit2 = Commit(hash, author, email,
            datetime.datetime(2014, 5, 18, 10, 27, 53))
        self.assertNotEqual(commit1, commit2)


def get_new_commit(hash=None, author=None, email=None, date=None):
    """Returns a new commit, possibly based on the given data (if not None)."""
    hash = hash or get_rand_hash()
    author = author or 'Petr Zemek'
    email = email or 's3rvac@gmail.com'
    date = get_curr_date()
    return Commit(hash, author, email, date)


class CommitReprTests(unittest.TestCase):
    """Tests for Commit.__repr__()."""

    def test_repr_works_correctly(self):
        commit = get_new_commit()
        commit_repr = repr(commit)
        self.assertIsInstance(commit_repr, str)
        self.assertEqual(eval(commit_repr), commit)


class BranchCreateAndAccessTests(unittest.TestCase):
    """Tests for Branch.__init__() and accessors."""

    def test_data_passed_into_constructor_are_accessible_after_creation(self):
        name = 'test'
        remote = 'origin'
        commit = get_new_commit()
        branch = Branch(name, remote, commit)
        self.assertEqual(branch.name, name)
        self.assertEqual(branch.remote, remote)
        self.assertEqual(branch.commit, commit)


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


class GitRunGitCmdTests(GitTests):
    """Tests for Git.run_git_cmd()."""

    def setUp(self):
        super().setUp()
        self.git = Git('/path/to/existing/repository')

    def test_git_status_returns_output(self):
        GIT_STATUS_OUTPUT = 'The output from git status.'
        self.mock_check_output.return_value = GIT_STATUS_OUTPUT
        self.assertEqual(self.git.run_git_cmd(['status']), GIT_STATUS_OUTPUT)

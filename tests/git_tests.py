#
# Unit tests for the viewer.git module.
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

# Cannot use `from datetime import datetime` because of eval() in `repr` tests.
import datetime
import os
import random
import subprocess
import unittest
from unittest import mock

from viewer.git import Branch
from viewer.git import Commit
from viewer.git import GitBinaryNotFoundError
from viewer.git import GitCmdError
from viewer.git import Repo
from viewer.git import sort_branches


def get_curr_date():
    """Returns the current date."""
    # Do not include milliseconds into the date because git uses just seconds.
    curr_date_ts = int(datetime.datetime.now().timestamp())
    return datetime.datetime.fromtimestamp(curr_date_ts)


def get_rand_hash(characters=Commit.VALID_HASH_CHARACTERS):
    """Returns a new, random hash from the given characters"""
    return ''.join(random.choice(
        list(characters)) for _ in range(Commit.VALID_HASH_LENGTH))


def get_new_commit(hash=None, author=None, email=None, date=None, subject=None):
    """Returns a new commit, possibly based on the given data (if not None)."""
    hash = hash if hash is not None else get_rand_hash()
    author = author if author is not None else 'Petr Zemek'
    email = email if email is not None else 's3rvac@gmail.com'
    date = date if date is not None else get_curr_date()
    subject = subject if subject is not None else 'Commit message'
    return Commit(hash, author, email, date, subject)


class CommitClassTests(unittest.TestCase):
    """Tests for the Commit class itself."""

    def test_valid_hash_length_has_proper_value(self):
        self.assertEqual(Commit.VALID_HASH_LENGTH, 40)

    def test_valid_hash_characters_has_proper_value(self):
        self.assertEqual(Commit.VALID_HASH_CHARACTERS, set('abcdef0123456789'))


class CommitCreateAndAccessTests(unittest.TestCase):
    """Tests for Commit.__init__() and accessors."""

    def test_data_passed_into_constructor_are_accessible_after_creation(self):
        hash = get_rand_hash()
        author = 'Petr Zemek'
        email = 's3rvac@gmail.com'
        date = get_curr_date()
        subject = 'Commit message'
        commit = Commit(hash, author, email, date, subject)
        self.assertEqual(commit.hash, hash)
        self.assertEqual(commit.author, author)
        self.assertEqual(commit.email, email)
        self.assertEqual(commit.date, date)
        self.assertEqual(commit.subject, subject)

    def test_data_cannot_be_changed_after_creation(self):
        commit = get_new_commit()
        with self.assertRaises(AttributeError):
            commit.hash = get_rand_hash()
        with self.assertRaises(AttributeError):
            commit.author = 'Other Author'
        with self.assertRaises(AttributeError):
            commit.email = 'Other email'
        with self.assertRaises(AttributeError):
            commit.date = get_curr_date()
        with self.assertRaises(AttributeError):
            commit.subject = 'Other commit message'

    def test_hash_is_properly_normalized(self):
        commit = get_new_commit(
            hash='207891DB5BDDBFB0C7210ACA8C76AC6A9C5F9859')
        self.assertEqual(commit.hash,
                 '207891db5bddbfb0c7210aca8c76ac6a9c5f9859')

    def test_value_error_is_raised_when_hash_is_empty(self):
        with self.assertRaises(ValueError):
            get_new_commit(hash='')

    def test_value_error_is_raised_when_hash_too_short(self):
        with self.assertRaises(ValueError):
            get_new_commit(hash='abcdef')

    def test_value_error_is_raised_when_hash_too_long(self):
        with self.assertRaises(ValueError):
            get_new_commit(hash='a' * (Commit.VALID_HASH_LENGTH + 1))

    def test_value_error_is_raised_when_hash_has_invalid_characters(self):
        with self.assertRaises(ValueError):
            get_new_commit(hash=(Commit.VALID_HASH_LENGTH - 1) * 'a' + 'g')


class CommitShortHashTests(unittest.TestCase):
    """Tests for Commit.short_hash()."""

    def test_short_hash_returns_correct_result(self):
        commit = get_new_commit(hash='207891db5bddbfb0c7210aca8c76ac6a9c5f9859')
        self.assertEqual(commit.short_hash(10), '207891db5b')


class CommitShortSubjectTests(unittest.TestCase):
    """Tests for Commit.short_subject()."""

    def test_short_subject_returns_subject_when_subject_is_shorter(self):
        commit = get_new_commit(subject='test')
        self.assertEqual(commit.short_subject(5), commit.subject)

    def test_short_subject_returns_subject_when_subject_has_same_length(self):
        commit = get_new_commit(subject='test')
        self.assertEqual(commit.short_subject(4), commit.subject)

    def test_short_subject_returns_shorter_subject_when_subject_is_longer(self):
        commit = get_new_commit(subject='test')
        self.assertEqual(commit.short_subject(3), 'tes...')


class CommitAgeTests(unittest.TestCase):
    """Tests for Commit.age."""

    @mock.patch('datetime.datetime')
    def test_age_returns_correct_result(self, datetime_mock):
        commit = get_new_commit()
        today = get_curr_date()
        datetime_mock.today.return_value = today
        expected_age = today - commit.date
        self.assertEqual(commit.age, expected_age)


class CommitComparisonTests(unittest.TestCase):
    """Tests for commit comparison."""

    def test_two_identical_commits_are_equal(self):
        commit = Commit(get_rand_hash(), 'PZ', 'pz@pz.net', get_curr_date(),
            'Commit message')
        self.assertEqual(commit, commit)

    def test_two_commits_with_equal_data_are_equal(self):
        hash = get_rand_hash()
        author = 'PZ'
        email = 'pz@pz.net'
        date = get_curr_date()
        subject = 'Commit message'
        commit1 = Commit(hash, author, email, date, subject)
        commit2 = Commit(hash, author, email, date, subject)
        self.assertEqual(commit1, commit2)

    def test_two_commits_with_different_hash_are_not_equal(self):
        author = 'PZ'
        email = 'pz@pz.net'
        date = get_curr_date()
        subject = 'Commit message'
        commit1 = Commit(get_rand_hash(), author, email, date, subject)
        commit2 = Commit(get_rand_hash(), author, email, date, subject)
        self.assertNotEqual(commit1, commit2)

    def test_two_commits_with_different_author_are_not_equal(self):
        hash = get_rand_hash()
        email = 'pz@pz.net'
        date = get_curr_date()
        subject = 'Commit message'
        commit1 = Commit(hash, 'Petr Zemek', email, date, subject)
        commit2 = Commit(hash, 'PZ', email, date, subject)
        self.assertNotEqual(commit1, commit2)

    def test_two_commits_with_different_email_are_not_equal(self):
        hash = get_rand_hash()
        author = 'PZ'
        date = get_curr_date()
        subject = 'Commit message'
        commit1 = Commit(hash, author, 'pz@pz.net', date, subject)
        commit2 = Commit(hash, author, 's3rvac@gmail.com', date, subject)
        self.assertNotEqual(commit1, commit2)

    def test_two_commits_with_different_date_are_not_equal(self):
        hash = get_rand_hash()
        author = 'PZ'
        email = 'pz@pz.net'
        subject = 'Commit message'
        commit1 = Commit(hash, author, email,
            datetime.datetime(2007, 12, 11, 5, 43, 14), subject)
        commit2 = Commit(hash, author, email,
            datetime.datetime(2014, 5, 18, 10, 27, 53), subject)
        self.assertNotEqual(commit1, commit2)

    def test_two_commits_with_different_msg_are_not_equal(self):
        hash = get_rand_hash()
        author = 'PZ'
        date = get_curr_date()
        commit1 = Commit(hash, author, 'pz@pz.net', date,
            'Commit message')
        commit2 = Commit(hash, author, 's3rvac@gmail.com', date,
            'Some other commit message')
        self.assertNotEqual(commit1, commit2)


class CommitReprTests(unittest.TestCase):
    """Tests for Commit.__repr__()."""

    def test_repr_works_correctly(self):
        commit = get_new_commit()
        commit_repr = repr(commit)
        self.assertIsInstance(commit_repr, str)
        self.assertEqual(eval(commit_repr), commit)


def get_git_repo_mock(path='/path/to/existing/repository'):
    """Returns a Mock object for a git repository."""
    repo = mock.MagicMock(spec=Repo, path=path)
    return repo


class BranchCreateAndAccessTests(unittest.TestCase):
    """Tests for Branch.__init__() and accessors."""

    def setUp(self):
        self.repo_mock = get_git_repo_mock()
        self.remote = 'origin'
        self.name = 'test'
        self.branch = Branch(self.repo_mock, self.remote, self.name)

    def test_data_passed_into_constructor_are_accessible_after_creation(self):
        self.assertEqual(self.branch.repo, self.repo_mock)
        self.assertEqual(self.branch.remote, self.remote)
        self.assertEqual(self.branch.name, self.name)

    def test_data_cannot_be_changed_after_creation(self):
        with self.assertRaises(AttributeError):
            self.branch.repo = get_git_repo_mock()
        with self.assertRaises(AttributeError):
            self.branch.remote = 'other_remote'
        with self.assertRaises(AttributeError):
            self.branch.name = 'other_name'


class BranchCommitTests(unittest.TestCase):
    """Tests for Branch.commit."""

    def test_get_commit_calls_proper_repo_method_and_returns_correct_commit(self):
        repo_mock = get_git_repo_mock()
        branch = Branch(repo_mock, 'origin', 'featureX')
        expected_commit = get_new_commit()
        repo_mock.get_commit_for_branch.return_value = expected_commit
        self.assertEqual(branch.commit, expected_commit)
        repo_mock.get_commit_for_branch.assert_called_once_with(branch)


class BranchFullNameTests(unittest.TestCase):
    """Tests for Branch.full_name."""

    def test_full_name_returns_proper_name(self):
        remote = 'origin'
        branch_name = 'featureX'
        repo_mock = get_git_repo_mock()
        branch = Branch(repo_mock, remote, branch_name)
        self.assertEqual(branch.full_name, '{}/{}'.format(remote, branch_name))


class BranchAgeTests(unittest.TestCase):
    """Tests for Branch.age."""

    @mock.patch('datetime.datetime')
    def test_age_returns_age_of_commit(self, datetime_mock):
        today = get_curr_date()
        datetime_mock.today.return_value = today
        commit = get_new_commit()
        repo_mock = get_git_repo_mock()
        repo_mock.get_commit_for_branch.return_value = commit
        branch = Branch(repo_mock, 'origin', 'featureX')
        self.assertEqual(branch.age, commit.age)


class BranchUnmergedCommitsTests(unittest.TestCase):
    """Tests for methods related to unmerged commits."""

    def setUp(self):
        self.repo_mock = get_git_repo_mock()
        self.branch = Branch(self.repo_mock, 'origin', 'featureX')
        self.master_branch = Branch(self.repo_mock, 'origin', 'master')

    def test_unmerged_commits_calls_repo_get_unmerged_commits_and_returns_its_result(self):
        commits = [get_new_commit()]
        self.repo_mock.get_unmerged_commits.return_value = commits
        self.assertEqual(self.branch.unmerged_commits(self.master_branch, limit=5), commits)
        self.repo_mock.get_unmerged_commits.assert_called_with(
            self.master_branch, self.branch, 5)

    def test_num_of_unmerged_commits_calls_repo_get_num_of_unmerged_commits_and_returns_its_result(self):
        self.repo_mock.get_num_of_unmerged_commits.return_value = 1
        self.assertEqual(self.branch.num_of_unmerged_commits(self.master_branch), 1)
        self.repo_mock.get_num_of_unmerged_commits.assert_called_with(
            self.master_branch, self.branch)

    def test_has_unmerged_commits_calls_repo_has_unmerged_commits_and_returns_its_result(self):
        self.repo_mock.has_unmerged_commits.return_value = True
        self.assertTrue(self.branch.has_unmerged_commits(self.master_branch))
        self.repo_mock.has_unmerged_commits.assert_called_with(self.master_branch, self.branch)

    def test_has_more_unmerged_commits_returns_true_when_there_are_more_such_commits(self):
        self.branch.num_of_unmerged_commits = mock.Mock(spec=Branch.num_of_unmerged_commits)
        self.branch.num_of_unmerged_commits.return_value = 6
        self.assertTrue(self.branch.has_more_unmerged_commits_than(self.master_branch, 4))

    def test_has_more_unmerged_commits_returns_false_when_there_are_not_more_such_commits(self):
        self.branch.num_of_unmerged_commits = mock.Mock(spec=Branch.num_of_unmerged_commits)
        self.branch.num_of_unmerged_commits.return_value = 4
        self.assertFalse(self.branch.has_more_unmerged_commits_than(self.master_branch, 4))


class BranchComparisonTests(unittest.TestCase):
    """Tests for branch comparison."""

    def test_two_identical_branches_are_equal(self):
        branch = Branch(get_git_repo_mock(), 'origin', 'featureX')
        self.assertEqual(branch, branch)

    def test_two_branches_with_equal_data_are_equal(self):
        repo_mock = get_git_repo_mock()
        branch1 = Branch(repo_mock, 'origin', 'featureX')
        branch2 = Branch(repo_mock, 'origin', 'featureX')
        self.assertEqual(branch1, branch2)

    def test_two_branches_with_different_repo_are_not_equal(self):
        repo1_mock = get_git_repo_mock('/path')
        repo2_mock = get_git_repo_mock('/some/other/path')
        branch1 = Branch(repo1_mock, 'origin', 'featureX')
        branch2 = Branch(repo2_mock, 'other_location', 'featureX')
        self.assertNotEqual(branch1, branch2)

    def test_two_branches_with_different_remote_are_not_equal(self):
        repo_mock = get_git_repo_mock()
        branch1 = Branch(repo_mock, 'origin', 'featureX')
        branch2 = Branch(repo_mock, 'other_location', 'featureX')
        self.assertNotEqual(branch1, branch2)

    def test_two_branches_with_different_name_are_not_equal(self):
        repo_mock = get_git_repo_mock()
        branch1 = Branch(repo_mock, 'origin', 'featureX')
        branch2 = Branch(repo_mock, 'origin', 'my_branch')
        self.assertNotEqual(branch1, branch2)


class BranchReprTests(unittest.TestCase):
    """Tests for Branch.__repr__()."""

    def test_repr_works_correctly(self):
        repo_mock = get_git_repo_mock()
        branch = Branch(repo_mock, 'origin', 'featureX')
        branch_repr = repr(branch)
        self.assertEqual(branch_repr, 'Branch({!r}, {!r}, {!r})'.format(
            repo_mock, branch.remote, branch.name))


class SortBranchesTests(unittest.TestCase):
    """Tests for sort_branches()."""

    def setUp(self):
        self.repo_mock = get_git_repo_mock()

    def test_sort_branches_by_name_work_correctly(self):
        branchA = Branch(self.repo_mock, 'origin', 'A')
        branchB = Branch(self.repo_mock, 'origin', 'B')
        branchC = Branch(self.repo_mock, 'origin', 'C')
        branches = [branchC, branchA, branchB]
        sort_branches(branches, 'name')
        self.assertEqual(branches, [branchA, branchB, branchC])


class RepoTests(unittest.TestCase):
    """A base class for all Repo tests."""

    def setUp(self):
        # Patch os.chdir.
        patcher = mock.patch('os.chdir')
        self.addCleanup(patcher.stop)
        self.mock_chdir = patcher.start()

        # Patch subprocess.check_output.
        patcher = mock.patch('subprocess.check_output')
        self.addCleanup(patcher.stop)
        self.mock_check_output = patcher.start()


class RepoCreateTests(RepoTests):
    """Tests for Repo.__init__()."""

    def test_create_repo_enters_the_repo_and_calls_git_status(self):
        REPO_PATH = '/path/to/existing/repository'
        Repo(REPO_PATH)
        self.mock_chdir.assert_any_call(REPO_PATH)
        self.mock_check_output.assert_called_once_with(['git', 'status'],
            universal_newlines=True)

    def test_path_is_accessible_after_creating_repo_from_existing_repository(self):
        REPO_PATH = '/path/to/existing/repository'
        repo = Repo(REPO_PATH)
        self.assertEqual(repo.path, REPO_PATH)

    @mock.patch('os.path.abspath')
    def test_rel_path_is_converted_into_abs_path_after_creating_repo(self,
            mock_abspath):
        ABS_REPO_PATH = '/path/to/existing/repository'
        REL_REPO_PATH = '../repository'
        mock_abspath.return_value = ABS_REPO_PATH
        repo = Repo(REL_REPO_PATH)
        self.assertEqual(repo.path, ABS_REPO_PATH)

    def test_path_cannot_be_changed_after_creation(self):
        repo = Repo('/path/to/existing/repository')
        with self.assertRaises(AttributeError):
            repo.path = '/some/other/path'

    def test_create_repo_from_nonexisting_location_raises_exception(self):
        self.mock_chdir.side_effect = FileNotFoundError('No such file or directory')
        REPO_PATH = '/path/to/nonexisting/location'
        self.assertRaises(FileNotFoundError, Repo, REPO_PATH)

    def test_create_repo_from_location_with_no_repository_raises_exception(self):
        self.mock_check_output.side_effect = subprocess.CalledProcessError(
            128, "['git', 'status']",
            b'fatal: Not a git repository (or any parent up to mount point)')
        REPO_PATH = '/path/to/existing/location/with/no/repository'
        self.assertRaises(GitCmdError, Repo, REPO_PATH)
        self.mock_check_output.assert_called_once_with(['git', 'status'],
            universal_newlines=True)

    def test_exception_is_raised_when_git_binary_is_not_found(self):
        # FileNotFoundError is raised when the command does not exist.
        self.mock_check_output.side_effect = FileNotFoundError(
            "[Errno 2] No such file or directory: 'git'")
        REPO_PATH = '/path/to/existing/location/with/norepository'
        self.assertRaises(GitBinaryNotFoundError, Repo, REPO_PATH)
        self.mock_check_output.assert_called_once_with(['git', 'status'],
            universal_newlines=True)


class RepoNameTests(RepoTests):
    """Tests for Repo.name."""

    def test_name_calls_proper_command(self):
        REPO_PATH = '/path/to/existing/repository'
        repo = Repo(REPO_PATH)
        repo.name
        self.mock_check_output.assert_called_with(
            ['git', 'rev-parse', '--show-toplevel'],
            universal_newlines=True)

    def test_name_returns_correct_name(self):
        REPO_NAME = 'repository'
        REPO_BASE_PATH = '/path/to/existing/{}'.format(REPO_NAME)
        REPO_PATH = '{}/subdirectory'.format(REPO_BASE_PATH)
        repo = Repo(REPO_PATH)
        self.mock_check_output.return_value = '{}\n'.format(REPO_BASE_PATH)
        self.assertEqual(repo.name, REPO_NAME)


class RepoComparisonTests(RepoTests):
    """Tests for repository comparison."""

    def test_two_repos_with_same_path_are_equal(self):
        REPO_PATH = '/path/to/existing/repository'
        repo1 = Repo(REPO_PATH)
        repo2 = Repo(REPO_PATH)
        self.assertEqual(repo1, repo2)

    def test_two_repos_with_different_path_are_not_equal(self):
        repo1 = Repo('/path/to/existing/repository')
        repo2 = Repo('/other/path/to/other/existing/repository')
        self.assertNotEqual(repo1, repo2)


class RepoReprTests(RepoTests):
    """Tests for Repo.__repr__()."""

    def test_repr_works_correctly(self):
        repo = Repo('/path/to/existing/repository')
        repo_repr = repr(repo)
        self.assertIsInstance(repo_repr, str)
        self.assertEqual(eval(repo_repr), repo)


class RepoWithRepoTests(RepoTests):
    """Base class for tests of a created repository."""

    def setUp(self):
        super().setUp()
        self.repo = Repo('/path/to/existing/repository')


class RepoRunGitCmdTests(RepoWithRepoTests):
    """Tests for Repo.run_git_cmd()."""

    def test_git_status_returns_output(self):
        GIT_STATUS_OUTPUT = 'The output from git status.'
        self.mock_check_output.return_value = GIT_STATUS_OUTPUT
        self.assertEqual(self.repo.run_git_cmd(['status']), GIT_STATUS_OUTPUT)


class RepoGetBranchesOnRemoteTests(RepoWithRepoTests):
    """Tests for Repo.get_branches_on_remote()."""

    def test_calls_proper_command_to_get_branches_on_given_remote(self):
        remote = 'origin'
        self.repo.get_branches_on_remote(remote)
        self.mock_check_output.assert_called_with(
            ['git', 'ls-remote', '--heads', remote],
            universal_newlines=True)

    def test_returns_empty_list_when_there_are_no_branches(self):
        self.mock_check_output.return_value = ''
        self.assertEqual(self.repo.get_branches_on_remote('origin'), [])

    def test_returns_single_branch_when_there_is_single_branch(self):
        remote = 'origin'
        hash = '1956e0f534d57e409508e821e03b5f6c317690fd'
        name = 'master'
        self.mock_check_output.return_value = '{} refs/heads/{}\n'.format(
            hash, name)
        expected_branches = [
            Branch(self.repo, remote, name)
        ]
        self.assertEqual(self.repo.get_branches_on_remote(remote),
            expected_branches)

    def test_returns_two_branches_when_there_are_two_branches(self):
        remote = 'origin'
        hash1 = '1956e0f534d57e409508e821e03b5f6c317690fd'
        name1 = 'master'
        hash2 = '6b2a042d4d1b80ebda22e7c63cc8e830a0d77045'
        name2 = 'featureX'
        self.mock_check_output.return_value = """
            {} refs/heads/{}
            {} refs/heads/{}
            """.format(hash1, name1, hash2, name2)
        expected_branches = [
            Branch(self.repo, remote, name1),
            Branch(self.repo, remote, name2)
        ]
        self.assertEqual(self.repo.get_branches_on_remote(remote),
            expected_branches)


class RepoGetCommitTests(RepoWithRepoTests):
    """A base class for all Repo.get_commit_*() tests."""

    def mock_check_output_side_effect(self, *args, **kwargs):
        if 'show' in args[0]:
            return '{}\n{}\n{}\n{}\n{}\n\ndiff'.format(
                self.hash, self.author, self.email,
                int(self.date.timestamp()), self.subject)
        return ''

    def setUp(self):
        super().setUp()
        self.hash = '4b34858294e9f4eee1cdd9af58911154b99472e3'
        self.author = 'Petr Zemek'
        self.email = 's3rvac@gmail.com'
        self.date = get_curr_date()
        self.subject = 'Commit message'
        self.mock_check_output.side_effect = self.mock_check_output_side_effect


class RepoGetCommitFromHashTests(RepoGetCommitTests):
    """Tests for Repo.get_commit_from_hash()."""

    def test_calls_proper_subprocess_command(self):
        hash = '8a9abf8ad351dc9c7e2a5ba9f3b4d41c038ea605'
        self.repo.get_commit_from_hash(hash)
        self.mock_check_output.assert_called_with(
            ['git', 'show', '--quiet', '--format=format:%H%n%an%n%ae%n%at%n%s%n', hash],
            universal_newlines=True)

    def test_returns_correct_commit(self):
        self.assertEqual(self.repo.get_commit_from_hash(hash),
            Commit(self.hash, self.author, self.email, self.date, self.subject))


class RepoGetCommitForBranchTests(RepoGetCommitTests):
    """Tests for Repo.get_commit_for_branch()."""

    def setUp(self):
        super().setUp()
        self.branch = Branch(self.repo, 'origin', 'master')

    def test_calls_proper_subprocess_command(self):
        self.repo.get_commit_for_branch(self.branch)
        self.mock_check_output.assert_called_with(
            ['git', 'show', '--quiet', '--format=format:%H%n%an%n%ae%n%at%n%s%n',
             self.branch.full_name], universal_newlines=True)

    def test_returns_correct_commit(self):
        self.assertEqual(self.repo.get_commit_for_branch(self.branch),
            Commit(self.hash, self.author, self.email, self.date, self.subject))

class RepoUnmergedCommitsTests(RepoWithRepoTests):
    """A base class for all tests of getting unmerged commits."""

    def setUp(self):
        super().setUp()
        self.master_branch = Branch(self.repo, 'origin', 'master')
        self.other_branch = Branch(self.repo, 'origin', 'other')


class RepoGetUnmergedCommitsTests(RepoUnmergedCommitsTests):
    """Tests for Repo.get_unmerged_commits()."""

    def test_calls_proper_subprocess_command_when_no_limit_is_given(self):
        self.repo.get_unmerged_commits(self.master_branch, self.other_branch)
        self.mock_check_output.assert_called_with(
            ['git', 'log', '--format=format:%H', '{}..{}'.format(
                self.master_branch.full_name, self.other_branch.full_name)],
            universal_newlines=True)

    def test_calls_proper_subprocess_command_when_limit_is_given(self):
        self.repo.get_unmerged_commits(self.master_branch, self.other_branch,
            limit=5)
        self.mock_check_output.assert_called_with(
            ['git', 'log', '-5', '--format=format:%H', '{}..{}'.format(
                self.master_branch.full_name, self.other_branch.full_name)],
            universal_newlines=True)

    def test_no_unmerged_commits(self):
        self.mock_check_output.return_value = '\n'
        unmerged_commits = self.repo.get_unmerged_commits(
            self.master_branch, self.other_branch)
        expected_unmerged_commits = []
        self.assertEqual(unmerged_commits, expected_unmerged_commits)

    def test_calls_get_commit_from_hash_for_every_hash_in_output(self):
        commits = [get_new_commit(), get_new_commit()]
        self.mock_check_output.return_value = '\n'.join(
            commit.hash for commit in commits)
        def mock_get_commit_from_hash_side_effect(hash):
            for commit in commits:
                if commit.hash == hash:
                    return commit
        self.repo.get_commit_from_hash = mock.MagicMock(
            spec=Repo.get_commit_from_hash,
            side_effect=mock_get_commit_from_hash_side_effect)
        unmerged_commits = self.repo.get_unmerged_commits(
            self.master_branch, self.other_branch)
        self.assertEqual(unmerged_commits, commits)


class RepoGetNumOfUnmergedCommitsTests(RepoUnmergedCommitsTests):
    """Tests for Repo.get_num_of_unmerged_commits()."""

    def test_calls_proper_subprocess_command(self):
        self.repo.has_unmerged_commits(self.master_branch, self.other_branch)
        self.mock_check_output.assert_called_with(
            ['git', 'log', '-1', '--format=format:%h', '{}..{}'.format(
                self.master_branch.full_name, self.other_branch.full_name)],
            universal_newlines=True)

    def test_there_are_no_unmerged_commits(self):
        self.mock_check_output.return_value = '\n'
        num_of_unmerged_commits = self.repo.get_num_of_unmerged_commits(
            self.master_branch, self.other_branch)
        self.assertEqual(num_of_unmerged_commits, 0)

    def test_there_are_unmerged_commits(self):
        self.mock_check_output.return_value = '327c90a\n548a89e\n'
        num_of_unmerged_commits = self.repo.get_num_of_unmerged_commits(
            self.master_branch, self.other_branch)
        self.assertEqual(num_of_unmerged_commits, 2)


class RepoHasUnmergedCommitsTests(RepoUnmergedCommitsTests):
    """Tests for Repo.has_unmerged_commits()."""

    def test_calls_proper_subprocess_command(self):
        self.repo.has_unmerged_commits(self.master_branch, self.other_branch)
        self.mock_check_output.assert_called_with(
            ['git', 'log', '-1', '--format=format:%h', '{}..{}'.format(
                self.master_branch.full_name, self.other_branch.full_name)],
            universal_newlines=True)

    def test_there_are_no_unmerged_commits(self):
        self.mock_check_output.return_value = '\n'
        self.assertFalse(
            self.repo.has_unmerged_commits(self.master_branch, self.other_branch))

    def test_there_are_unmerged_commits(self):
        self.mock_check_output.return_value = '327c90a\n548a89e\n'
        self.assertTrue(
            self.repo.has_unmerged_commits(self.master_branch, self.other_branch))


@mock.patch('os.path.getmtime')
class RepoGetDateOfLastUpdateTests(RepoWithRepoTests):
    """Tests for Repo.get_date_of_last_update()."""

    def test_calls_getmtime_with_proper_argument(self, getmtime_mock):
        self.repo.get_date_of_last_update()
        getmtime_mock.assert_called_with(
            os.path.join(self.repo.path, '.git', 'FETCH_HEAD'))

    def test_returns_correct_date(self, getmtime_mock):
        expected_date = get_curr_date()
        getmtime_mock.return_value = expected_date.timestamp()
        self.assertEqual(self.repo.get_date_of_last_update(), expected_date)

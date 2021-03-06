"""
    viewer.git
    ~~~~~~~~~~

    Interface to Git.

    :copyright: © 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
    :license: BSD, see LICENSE for more details
"""

import datetime
import operator
import os
import re
import subprocess

from viewer.utils import chdir
from viewer.utils import nonempty_lines


class BaseGitError(Exception):
    """A base class for all exception raised by the classes in this module."""
    pass


class GitCmdError(BaseGitError):
    """An exception that is raised when a Git command fails."""
    pass


class GitBinaryNotFoundError(GitCmdError):
    """An exception that is raised when the Git binary is not found."""
    pass


class Commit:
    """A representation of a Git commit."""

    #: The length of a valid hash. Hashes of a different length are not
    #: permitted.
    VALID_HASH_LENGTH = 40

    #: The set of valid hash characters '0123456789abcdef'. Other characters
    #: are not permitted in a hash.
    VALID_HASH_CHARACTERS = set('0123456789abcdef')

    def __init__(self, hash, author, email, date, subject):
        """Creates a commit with the given data.

        :param str hash: Identifier of the commit.
        :param str author: Author of the commit.
        :param str email: Email of the author.
        :param date date: Date the commit was authored.
        :param str subject: Commit subject (the first line of the commit
                            message).

        The hash is normalized so that it contains only lowercase characters.
        The data cannot be changed after the commit is created.

        :raises ValueError: If the hash's length differs from
                            :attr:`VALID_HASH_LENGTH` or if the hash contains
                            characters out of :attr:`VALID_HASH_CHARACTERS`.
        """
        self._hash = self._normalize_hash(hash)
        self._validate_hash(self._hash)

        self._author = author
        self._email = email
        self._date = date
        self._subject = subject

    @property
    def hash(self):
        """Identifier of the commit."""
        return self._hash

    @property
    def author(self):
        """Author of the commit."""
        return self._author

    @property
    def email(self):
        """Email of the author."""
        return self._email

    @property
    def date(self):
        """Date the commit was authored."""
        return self._date

    @property
    def subject(self):
        """Subject (the first line of commit message)."""
        return self._subject

    def short_subject(self, length=50):
        """Shorter version of the subject.

        When the subject is of a shorter or equal length as `length`, it is
        returned unmodified. However, when it is longer than `length`, the
        first `length` characters are returned with appended ellipsis
        (`...`).
        """
        if len(self.subject) <= length:
            return self.subject
        return '{}...'.format(self.subject[:length])

    def short_hash(self, length=8):
        """Shorter version of the hash."""
        return self.hash[:length]

    @property
    def age(self):
        """Age of the commit."""
        return datetime.datetime.today() - self.date

    def __eq__(self, other):
        return (self.hash == other.hash and
                self.author == other.author and
                self.email == other.email and
                self.date == other.date and
                self.subject == other.subject)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '{}({!r}, {!r}, {!r}, {!r}, {!r})'.format(
            self.__class__.__name__,
            self.hash,
            self.author,
            self.email,
            self.date,
            self.subject)

    def _normalize_hash(self, hash):
        return hash.lower()

    def _validate_hash(self, hash):
        self._validate_hash_length(hash)
        self._validate_hash_characters(hash)

    def _validate_hash_length(self, hash):
        if len(hash) != self.VALID_HASH_LENGTH:
            raise ValueError(
                "hash '{}' has invalid length {} (expected {})".format(
                    hash, len(hash), self.VALID_HASH_LENGTH
                )
            )

    def _validate_hash_characters(self, hash):
        hash_characters = set(hash)
        invalid_characters = hash_characters - self.VALID_HASH_CHARACTERS
        if invalid_characters:
            raise ValueError(
                "hash '{}' contains invalid character(s): '{}'".format(
                    hash, ''.join(invalid_characters)
                )
            )


class Branch:
    """A representation of a Git branch."""

    def __init__(self, repo, remote, name):
        """Constructs a branch with the given data.

        :param Repo repo: Git repository in which this branch is.
        :param str remote: Name of the remote on which this branch is.
        :param str name: Name of the branch.

        The data cannot be changed after the branch is created.
        """
        self._repo = repo
        self._remote = remote
        self._name = name

    @property
    def repo(self):
        """Git repository in which this branch is."""
        return self._repo

    @property
    def remote(self):
        """Name of the remote on which this branch is."""
        return self._remote

    @property
    def name(self):
        """Name of the branch."""
        return self._name

    @property
    def full_name(self):
        """Full name of the branch (`'remote/name'`)."""
        return '{}/{}'.format(self.remote, self.name)

    @property
    def commit(self):
        """Commit representing the branch."""
        return self._repo.get_commit_for_branch(self)

    @property
    def age(self):
        """Age of the branch.

        It is the age of the commit representing the branch.
        """
        return self.commit.age

    def unmerged_commits(self, master_branch, limit=None):
        """Returns a list of commits that are not in `master_branch`.

        :param int limit: If not `None`, returns at most `limit` commits.
        """
        return self.repo.get_unmerged_commits(master_branch, self, limit)

    def num_of_unmerged_commits(self, master_branch):
        """Returns the number of commits that are not in `master_branch`."""
        return self.repo.get_num_of_unmerged_commits(master_branch, self)

    def has_unmerged_commits(self, master_branch):
        """Checks if there are commits in the branch that are not in
        `master_branch`.

        :return `True` if there are such commits, `False` otherwise.
        """
        return self.repo.has_unmerged_commits(master_branch, self)

    def has_more_unmerged_commits_than(self, master_branch, limit):
        """Checks if there are more than `limit` commits in the branch that are
        not in `master_branch`.
        """
        return self.num_of_unmerged_commits(master_branch) > limit

    def __eq__(self, other):
        return (self.repo == other.repo and
                self.remote == other.remote and
                self.name == other.name)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '{}({!r}, {!r}, {!r})'.format(
            self.__class__.__name__,
            self.repo,
            self.remote,
            self.name
        )


def sort_branches(branches, attr):
    """Sorts the given list of branches in place by the given attribute
    (`str`).
    """
    return branches.sort(key=operator.attrgetter(attr))


class Repo:
    """An interface to a Git repository.

    The methods in this class may raise the following exceptions:

    :raises FileNotFoundError: If the repository path path does not exist or
                               cannot be entered.
    :raises GitBinaryNotFoundError: If the Git binary (i.e. ``git``) is not
                                    found.
    :raises GitCmdError: If there is an error when running a Git command.
    """

    def __init__(self, path):
        """Creates an interface to a Git repository in the given `path`.

        :param str path: A path to the repository.

        If the path is relative, it is converted into an absolute path.

        See the class description for a list of exceptions that this method may
        raise.
        """
        self._path = os.path.abspath(path)
        self._verify_repository_existence()

    @property
    def path(self):
        """Absolute path to the repository."""
        return self._path

    @property
    def name(self):
        """Name of the repository (its top-level directory)."""
        # `git rev-parse --show-toplevel` prints the path to the top-level
        # directory of the repository.
        return os.path.basename(
            self.run_git_cmd(['rev-parse', '--show-toplevel']).strip()
        )

    def run_git_cmd(self, args):
        """Runs the Git command with the given arguments in the repository and
        returns the output.

        :param seq args: A sequence of parameters passed to git.

        See the class description for a list of exceptions that this method may
        raise.
        """
        with chdir(self.path):
            try:
                return subprocess.check_output(
                    ['git'] + list(args),
                    universal_newlines=True
                )
            # When a command is not found or cannot be executed,
            # subprocess.check_output() raises OSError.
            except OSError:
                raise GitBinaryNotFoundError(
                    "'git' is not installed or cannot be executed"
                )
            except subprocess.CalledProcessError as ex:
                raise GitCmdError(ex.output)

    def get_branches_on_remote(self, remote):
        """Returns a list of all branches on the given remote."""
        output = self.run_git_cmd(['branch', '--remote', '--no-color'])
        return self._get_branches_from_branch_remote_output(output, remote)

    def get_commit_from_hash(self, hash):
        """Returns the commit corresponding to the given hash."""
        return self._get_commit_from_git_show_with_object(hash)

    def get_commit_for_branch(self, branch):
        """Returns the commit for the given branch."""
        return self._get_commit_from_git_show_with_object(
            '{}/{}'.format(branch.remote, branch.name)
        )

    def get_unmerged_commits(self, master_branch, other_branch, limit=None):
        """Returns a list of commits that are in `other_branch` but not in
        `master_branch`.

        :param int limit: If not `None`, returns at most `limit` commits.
        """
        hashes = self._get_hashes_of_unmerged_commits(
            master_branch,
            other_branch,
            limit
        )
        return list(map(self.get_commit_from_hash, hashes))

    def get_num_of_unmerged_commits(self, master_branch, other_branch):
        """Returns the number of commits that are in `other_branch` but not in
        `master_branch`.
        """
        hashes = self._get_hashes_of_unmerged_commits(
            master_branch,
            other_branch
        )
        return len(hashes)

    def has_unmerged_commits(self, master_branch, other_branch):
        """Checks if there are commits in `other_branch` that are not in
        `master_branch`.

        :return `True` if there are such commits, `False` otherwise.
        """
        # The following command either generates a single line (= there is at
        # least one unmerged commit), or nothing (no unmerged commits).
        output = self.run_git_cmd([
            'log',
            '-1',
            '--format=format:%h',
            '{}..{}'.format(master_branch.full_name, other_branch.full_name)
        ])
        return bool(output.strip())

    def get_date_of_last_update(self):
        """Returns the date when the repository was last updated."""
        # We obtain this information by checking the last modification time of
        # the .git/FETCH_HEAD file. This is not bulletproof (see the comments
        # in http://stackoverflow.com/a/9229377), but I don't know of any
        # better way.
        return datetime.datetime.fromtimestamp(
            os.path.getmtime(os.path.join(self.path, '.git', 'FETCH_HEAD'))
        )

    def __eq__(self, other):
        return self.path == other.path

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '{}({!r})'.format(
            self.__class__.__name__,
            self.path)

    def _get_hashes_of_unmerged_commits(self, master_branch, other_branch,
                                        limit=None):
        # The following command generates output of the form
        #
        #   327c90a7c0bb4a739c2a245aeffa5f569cbd67da
        #   548a89e53ffe8fb532655156b700ea1ed1e410fb
        #   ...
        #
        # where the number of lines is limited by the given limit (if any).
        cmd = ['log']
        if limit is not None:
            cmd.append('-{}'.format(limit))
        cmd.extend([
            '--format=format:%H', '{}..{}'.format(
                master_branch.full_name,
                other_branch.full_name
            )
        ])
        output = self.run_git_cmd(cmd)
        return nonempty_lines(output)

    def _get_branches_from_branch_remote_output(self, output, remote):
        # The `git branch --remote` output should be of the form
        #
        #   remote/branch1_name
        #   remote/branch2_name
        #   ...
        #
        branches = []
        for line in output.split('\n'):
            m = re.match(r"""
                    \s*                # Optional spaces at the beginning
                    {}/(?P<name>[^ ]+) # remote/branch_name
                    $
                """.format(remote), line, re.VERBOSE)
            if m:
                branches.append(Branch(self, remote, m.group('name')))
        return branches

    def _get_commit_from_git_show_with_object(self, obj):
        # We use `git show` with a custom format to get just the needed
        # information about the commit. The used format produces output of the
        # following form:
        #
        #   hash
        #   author
        #   email
        #   date (timestamp)
        #   subject
        #
        # The '--quiet' parameter prevents a diff from being displayed (we do
        # not need it).
        output = self.run_git_cmd(
            ['show', '--quiet', '--format=format:%H%n%an%n%ae%n%at%n%s%n', obj]
        )
        m = re.match(r"""
                (?P<hash>[a-fA-F0-9]+)\n
                (?P<author>.+)\n
                (?P<email>.+)\n
                (?P<date_ts>[0-9]+)\n
                (?P<subject>.+)\n
            """, output, re.VERBOSE | re.MULTILINE)
        hash = m.group('hash')
        author = m.group('author')
        email = m.group('email')
        date = datetime.datetime.fromtimestamp(int(m.group('date_ts')))
        subject = m.group('subject')
        return Commit(hash, author, email, date, subject)

    def _verify_repository_existence(self):
        self.run_git_cmd(['status'])

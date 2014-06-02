"""
    viewer.git
    ~~~~~~~~~~

    Interface to git.

    :copyright: © 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
    :license: BSD, see LICENSE for more details
"""

import datetime
import os
import re
import subprocess

from .utils import chdir


class BaseGitError(Exception):
    """A base class for all exception raised by the classes in this module."""
    pass


class GitCmdError(BaseGitError):
    """An exception that is raised when a git command fails."""
    pass


class GitBinaryNotFoundError(GitCmdError):
    """An exception that is raised when the git binary is not found."""
    pass


class Commit:
    """A representation of a git commit."""

    #: The length of a valid hash. Hashes of a different length are not
    #: permitted.
    VALID_HASH_LENGTH = 40

    #: The set of valid hash characters '0123456789abcdef'. Other characters
    #: are not permitted in a hash.
    VALID_HASH_CHARACTERS = set('0123456789abcdef')

    def __init__(self, hash, author, email, date, msg):
        """Creates a commit with the given data.

        :param str hash: Identifier of the commit.
        :param str author: Author of the commit.
        :param str email: Email of the author.
        :param date date: Date the commit was authored.
        :param str msg: Commit message.

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
        self._msg = msg

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
    def msg(self):
        """Commit message."""
        return self._msg

    def short_hash(self, length=8):
        """Shorter version of the hash."""
        return self.hash[:length]

    def __eq__(self, other):
        return (self.hash == other.hash and
                self.author == other.author and
                self.email == other.email and
                self.date == other.date and
                self.msg == other.msg)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '{}({!r}, {!r}, {!r}, {!r}, {!r})'.format(
            self.__class__.__name__,
            self.hash,
            self.author,
            self.email,
            self.date,
            self.msg)

    def _normalize_hash(self, hash):
        return hash.lower()

    def _validate_hash(self, hash):
        self._validate_hash_length(hash)
        self._validate_hash_characters(hash)

    def _validate_hash_length(self, hash):
        if len(hash) != self.VALID_HASH_LENGTH:
            raise ValueError(
                "hash '{}' has invalid length {} (expected {})".format(
                    hash, len(hash), self.VALID_HASH_LENGTH))

    def _validate_hash_characters(self, hash):
        hash_characters = set(hash)
        invalid_characters = hash_characters - self.VALID_HASH_CHARACTERS
        if invalid_characters:
            raise ValueError(
                "hash '{}' contains invalid character(s): '{}'".format(
                    hash, ''.join(invalid_characters)))


class Branch:
    """A representation of a git branch."""

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
            self.name)


class Repo:
    """An interface to a git repository.

    The methods in this class may raise the following exceptions:

    :raises FileNotFoundError: If the repository path path does not exist or
                               cannot be entered.
    :raises GitBinaryNotFoundError: If the git binary (i.e. ``git``) is not
                                    found.
    :raises GitCmdError: If there is an error when running a git command.
    """

    def __init__(self, path):
        """Creates an interface to a git repository in the given `path`.

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

    def run_git_cmd(self, args):
        """Runs the git command with the given arguments in the repository and
        returns the output.

        :param seq args: A sequence of parameters passed to git.

        See the class description for a list of exceptions that this method may
        raise.
        """
        with chdir(self.path):
            try:
                return subprocess.check_output(['git'] + list(args))
            # When a command is not found or cannot be executed,
            # subprocess.check_output() raises OSError.
            except OSError:
                raise GitBinaryNotFoundError(
                    "'git' is not installed or cannot be executed")
            except subprocess.CalledProcessError as ex:
                raise GitCmdError(ex.output)

    def get_branches_on_remote(self, remote):
        """Returns all the branches on the given remote in a list."""
        output = self.run_git_cmd(['ls-remote', '--heads', remote])
        return self._get_branches_from_ls_remote_output(output, remote)

    def get_commit_from_hash(self, hash):
        """Returns the commit corresponding to the given hash."""
        return self._get_commit_from_git_show_with_args(hash)

    def get_commit_for_branch(self, branch):
        """Returns the commit for the given branch."""
        return self._get_commit_from_git_show_with_args(
            branch.remote, branch.name)

    def __eq__(self, other):
        return self.path == other.path

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '{}({!r})'.format(
            self.__class__.__name__,
            self.path)

    def _get_branches_from_ls_remote_output(self, output, remote):
        # The ls-remote output should be of the form
        #
        #   hash1        refs/heads/branch1_name
        #   hash1        refs/heads/branch2_name
        #   ...
        #
        branches = []
        for line in output.split('\n'):
            m = re.match(r"""
                    \s*                     # Optional spaces at the beginning
                    [a-fA-F0-9]+            # Hash
                    \s+                     # Spaces
                    refs/heads/(?P<name>.+) # Branch name
                    $
                """, line, re.VERBOSE)
            if m:
                branches.append(Branch(self, remote, m.group('name')))
        return branches

    def _get_commit_from_git_show_with_args(self, *args):
        output = self.run_git_cmd(['show', '--format=raw'] + list(args))
        return self._get_commit_from_show_output(output)

    def _get_commit_from_show_output(self, output):
        # The output of `git show --format=raw` should be of the form
        #
        #   commit 4b34858294e9f4eee1cdd9af58911154b99472e3
        #   ...
        #   author PZ <pz@pz.net> 1401389467 +0200
        #   ...
        #
        #   commit message
        #
        hash = self._get_commit_hash_from_show_output(output)
        author, email, date = \
            self._get_commit_author_email_date_from_show_output(output)
        msg = self._get_commit_msg_from_show_output(output)
        return Commit(hash, author, email, date, msg)

    def _get_commit_hash_from_show_output(self, output):
        m = re.search(r"""
                commit \s+ (?P<hash>[a-fA-F0-9]+)
            """, output, re.VERBOSE | re.MULTILINE)
        return m.group('hash')

    def _get_commit_author_email_date_from_show_output(self, output):
        m = re.search(r"""
                author \s+ (?P<author>.+)
                       \s+ <(?P<email>.+)>
                       \s+ (?P<date_ts>[0-9]+)
                       \s+ (?P<tz>[+-][0-9]+)
                $
            """, output, re.VERBOSE | re.MULTILINE)
        author = m.group('author')
        email = m.group('email')
        date = datetime.datetime.fromtimestamp(int(m.group('date_ts')))
        return author, email, date

    def _get_commit_msg_from_show_output(self, output):
        m = re.search(r"""
                \n
                \n
                (?P<msg>.*)
                \n
                $
            """, output, re.VERBOSE | re.MULTILINE)
        return m.group('msg').strip()

    def _verify_repository_existence(self):
        self.run_git_cmd(['status'])

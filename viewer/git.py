"""
    viewer.git
    ~~~~~~~~~~

    Interface to git.

    :copyright: © 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
    :license: BSD, see LICENSE for more details
"""

import datetime
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

    def __init__(self, hash, author, email, date):
        """Creates a commit with the given data.

        :param str hash: Identifier of the commit.
        :param str author: Author of the commit.
        :param str email: Email of the author.
        :param date date: Date the commit was authored.

        The hash is normalized so that it contains only lowercase characters.

        :raises ValueError: If the hash's length differs from
                            :attr:`VALID_HASH_LENGTH` or if the hash contains
                            characters out of :attr:`VALID_HASH_CHARACTERS`.
        """
        #: Identifier of the commit.
        self.hash = hash
        #: Author of the commit.
        self.author = author
        #: Email of the author.
        self.email = email
        #: Date the commit was authored.
        self.date = date

    @property
    def hash(self):
        return self._hash

    @hash.setter
    def hash(self, new_hash):
        new_hash = self._normalize_hash(new_hash)
        self._validate_hash(new_hash)
        self._hash = new_hash

    def short_hash(self, length=8):
        """Returns a shorter version of the hash."""
        return self.hash[:length]

    def __eq__(self, other):
        return (self.hash == other.hash and
                self.author == other.author and
                self.email == other.email and
                self.date == other.date)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '{}({!r}, {!r}, {!r}, {!r})'.format(
            self.__class__.__name__,
            self.hash,
            self.author,
            self.email,
            self.date)

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

    def __init__(self, remote, name):
        """Constructs a branch with the given data.

        :param str remote: Name of the remote on which this branch is.
        :param str name: Name of the branch.
        """
        #: Name of the remote on which this branch is.
        self.remote = remote
        #: Name of the branch.
        self.name = name

    def __eq__(self, other):
        return (self.remote == other.remote and self.name == other.name)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '{}({!r}, {!r})'.format(
            self.__class__.__name__,
            self.remote,
            self.name)


class Git:
    """Interface to a git repository.

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

        See the class description for a list of exceptions that this method may
        raise.
        """
        #: Path to the repository.
        self.path = path

        self._verify_repository_existence()

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
        ls_remote_output = self.run_git_cmd(['ls-remote', '--heads', remote])
        return self._get_branches_from_ls_remote_output(ls_remote_output, remote)

    def get_commit_from_hash(self, hash):
        """Returns the commit corresponding to the given hash."""
        return self._get_commit_from_git_show_with_args(hash)

    def get_commit_for_branch(self, branch):
        """Returns the commit for the given branch."""
        return self._get_commit_from_git_show_with_args(
            branch.remote, branch.name)

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
                branches.append(Branch(remote, m.group('name')))
        return branches

    def _get_commit_from_git_show_with_args(self, *args):
        show_output = self.run_git_cmd(['show', '--format=raw'] + list(args))
        return self._get_commit_from_show_output(show_output)

    def _get_commit_from_show_output(self, show_output):
        # The output of `git show --format=raw` should be of the form
        #
        #   commit 4b34858294e9f4eee1cdd9af58911154b99472e3
        #   ...
        #   author PZ <pz@pz.net> 1401389467 +0200
        #   ...
        #
        hash = self._get_commit_hash_from_show_output(show_output)
        author, email, date = self._get_commit_details_from_show_output(
            show_output)
        return Commit(hash, author, email, date)

    def _get_commit_hash_from_show_output(self, show_output):
        m = re.search(r"""
                commit \s+ (?P<hash>[a-fA-F0-9]+)
            """, show_output, re.VERBOSE | re.MULTILINE)
        return m.group('hash')

    def _get_commit_details_from_show_output(self, show_output):
        m = re.search(r"""
                author \s+ (?P<author>.+)
                       \s+ <(?P<email>.+)>
                       \s+ (?P<date_ts>[0-9]+)
                       \s+ (?P<tz>[+-][0-9]+)
                $
            """, show_output, re.VERBOSE | re.MULTILINE)
        author = m.group('author')
        email = m.group('email')
        date = datetime.datetime.fromtimestamp(int(m.group('date_ts')))
        return author, email, date

    def _verify_repository_existence(self):
        self.run_git_cmd(['status'])

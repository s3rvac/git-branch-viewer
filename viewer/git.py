"""
    viewer.git
    ~~~~~~~~~~

    Interface to git.

    :copyright: © 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
    :license: BSD, see LICENSE for more details
"""

import subprocess

from .utils import chdir


class Commit:
    """A representation of a git commit."""
    VALID_HASH_LENGTH = 40
    VALID_HASH_CHARACTERS = set('0123456789abcdef')

    def __init__(self, hash, author, email, date):
        """Creates a commit with the given data.

         - hash: identifier of the commit (string of VALID_HASH_LENGTH
                 containing only VALID_HASH_CHARACTERS)
         - author: author of the commit (string)
         - email: email of the author (string)
         - date: date the commit was authored (a date object)

        The hash is normalized so that it contains only lowercase characters.
        If the hash has invalid length or contains invalid characters after the
        normalization, ValueError is raised.
        """
        self.hash = hash
        self.author = author
        self.email = email
        self.date = date

        self._normalize_hash()
        self._validate_hash()

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

    def _normalize_hash(self):
        self.hash = self.hash.lower()

    def _validate_hash(self):
        self._validate_hash_length()
        self._validate_hash_characters()

    def _validate_hash_length(self):
        if len(self.hash) != self.VALID_HASH_LENGTH:
            raise ValueError(
                "hash '{}' has invalid length {} (expected {})".format(
                    self.hash, len(self.hash), self.VALID_HASH_LENGTH))

    def _validate_hash_characters(self):
        hash_characters = set(self.hash)
        invalid_characters = hash_characters - self.VALID_HASH_CHARACTERS
        if invalid_characters:
            raise ValueError(
                "hash '{}' contains invalid character(s): '{}'".format(
                    self.hash, ''.join(invalid_characters)))


class Branch:
    """A representation of a git branch."""

    def __init__(self, name, commit, unmerged_commits):
        """Constructs a branch with the given data.

         - name: name of the branch (string)
         - commit: current commit in the branch (a Commit object)
         - unmerged_commits: commits that have not been merged to the master
                             branch (a list of Commit objects)
        """
        self.name = name
        self.commit = commit
        self.unmerged_commits = unmerged_commits


class BaseGitError(Exception):
    """A base class for all exception raised by the Git class."""
    pass


class GitCmdError(BaseGitError):
    """An exception that is raised when a git command fails."""
    pass


class GitBinaryNotFoundError(GitCmdError):
    """An exception that is raised when the git binary was not found."""
    pass


class Git:
    """Interface to a git repository.

    The methods in this class may raise the following exceptions:

     - FileNotFoundError: If the repository path path does not exist or cannot
                          be entered.

     - GitBinaryNotFoundError: If the git binary (i.e. git) is not found.

     - GitCmdError: If there is an error when running a git command.
    """

    def __init__(self, path):
        """Creates an interface to a git repository in the given path.

        The path is then accessible through the path attribute.

        See the class description for a list of exceptions that this method may
        raise.
        """
        self.path = path
        self._verify_repository_existence()

    def run_git_cmd(self, args):
        """Runs the git command with the given arguments in the repository and
        returns the output.

        args has to be a sequence of parameters passed to git.

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

    def _verify_repository_existence(self):
        self.run_git_cmd(['status'])

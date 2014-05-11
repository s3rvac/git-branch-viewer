"""
    viewer.git
    ~~~~~~~~~~

    Interface to git.

    :copyright: © 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
    :license: BSD, see LICENSE for more details
"""

import subprocess

from .utils import chdir


class BaseGitError(Exception):
    """A base class for all exception raised by the Git class."""
    pass


class NoGitRepositoryError(BaseGitError):
    """An exception raised when there is no repository in the given path."""
    pass


class GitCmdNotFoundError(BaseGitError):
    """An exception raised when the git command has not been found."""
    pass


class Git:
    """Interface to a git repository."""

    def __init__(self, path):
        """Creates an interface to a git repository in the given path.

        If the given path does not exist or cannot be entered,
        FileNotFoundError is raised.

        If the path is not a git repository, NoGitRepositoryError is raised.

        If the git command is not found, GitCmdNotFoundError is raised.
        """
        self.path = path

        with chdir(self.path):
            try:
                subprocess.check_call(['git', 'status'])
            # When a command is not found, subprocess.check_call() raises
            #
            #   FileNotFoundError: [Errno 2] No such file or directory: 'cmd'
            #
            except FileNotFoundError as ex:
                raise GitCmdNotFoundError(
                    "'git' is not installed or cannot be run")
            except subprocess.CalledProcessError as ex:
                raise NoGitRepositoryError(
                    "'{}' is not a git repository".format(self.path))

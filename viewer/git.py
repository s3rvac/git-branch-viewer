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


class Git:
    """Interface to a git repository."""

    def __init__(self, path):
        """Creates an interface to a git repository in the given path.

        If the given path does not exist or cannot be entered,
        FileNotFoundError is raised.

        If the path is not a git repository, NoGitRepositoryError is raised.
        """
        self.path = path

        try:
            with chdir(self.path):
                subprocess.check_call(['git', 'status'])
        except subprocess.CalledProcessError as ex:
            raise NoGitRepositoryError("'{}' is not a git repository".format(
                self.path))

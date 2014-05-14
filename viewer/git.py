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


class GitCmdError(BaseGitError):
    """An exception that is raised when a git command fails."""
    pass


class GitBinaryNotFoundError(GitCmdError):
    """An exception that is raised when the git binary was not found."""
    pass


class Git:
    """Interface to a git repository."""

    def __init__(self, path):
        """Creates an interface to a git repository in the given path.

        The path is then accessible through the path attribute.

        See run_git_cmd() for the list of exceptions that may be raised.
        """
        self.path = path
        self._verify_repository_existence()

    def run_git_cmd(self, args):
        """Runs the git command with the given arguments in the repository and
        returns the output.

        args has to be a sequence of parameters passed to git.

        If the path does not exist or cannot be entered, FileNotFoundError is
        raised.

        If the git command is not found, GitBinaryNotFoundError is raised.

        If there is an error when running the command, GitCmdError is raised.
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

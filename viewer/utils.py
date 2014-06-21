"""
    viewer.utils
    ~~~~~~~~~~~~

    General-purpose utilities.

    :copyright: © 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
    :license: BSD, see LICENSE for more details
"""

import contextlib
import os


@contextlib.contextmanager
def chdir(dir):
    """A context manager that performs actions in the given directory.

    Example:

    >>> import os
    >>> print(os.getcwd())
    /
    >>> with chdir('/tmp'):
    ...     print(os.getcwd())
    ...
    /tmp
    >>> print(os.getcwd())
    /
    """
    cwd = os.getcwd()
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(cwd)


def nonempty_lines(text):
    """Returns non-empty lines in the given text."""
    return [line for line in text.split('\n') if line]

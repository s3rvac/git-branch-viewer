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
    """A context manager that enables performing actions in the given
    directory.
    """
    cwd = os.getcwd()
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(cwd)


def nonempty_lines(text):
    """Generates non-empty lines in the given text."""
    for line in text.split('\n'):
        if line:
            yield line

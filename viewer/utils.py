"""
    viewer.utils
    ~~~~~~~~~~~~

    Various utilities.

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

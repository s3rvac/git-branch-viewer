"""
    viewer.format
    ~~~~~~~~~~~~~

    Formatting functions.

    :copyright: © 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
    :license: BSD, see LICENSE for more details
"""


def format_date(date):
    """Formats the given date (:class:`datetime` object).

    :returns: `date` in the form `'YYYY-MM-DD HH:MM:SS'`.
    """
    return date.strftime('%Y-%m-%d %H:%M:%S')

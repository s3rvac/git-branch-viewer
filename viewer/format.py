"""
    viewer.format
    ~~~~~~~~~~~~~

    Formatting functions.

    :copyright: © 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
    :license: BSD, see LICENSE for more details
"""


def format_age(age):
    """Formats the given age (:class:`timedelta` object).

    :returns: `age` of the form `'X seconds/hours/days'`.

    When `age` is negative, the minus sign (`-`) is prepended before the
    returned string.
    """
    def format_nonnegative_age(age):
        # The timedelta internal representation uses only days and seconds (and
        # microseconds, but we do not care about them).
        if age.days > 0:
            repr = '{} days'.format(age.days)
        elif age.seconds >= 3600:
            repr = '{} hours'.format(age.seconds // 3600)
        elif age.seconds >= 60:
            repr = '{} minutes'.format(age.seconds // 60)
        else:
            repr = '{} seconds'.format(age.seconds)
        # Remove the ending 's' if we have only 1 second/minute/hour/day.
        return repr if not repr.startswith('1 ') else repr[:-1]

    def is_negative(age):
        return age.total_seconds() < 0

    if is_negative(age):
        return '-' + format_nonnegative_age(abs(age))
    return format_nonnegative_age(age)


def format_date(date):
    """Formats the given date (:class:`datetime` object).

    :returns: `date` in the form `'YYYY-MM-DD HH:MM:SS'`.
    """
    return date.strftime('%Y-%m-%d %H:%M:%S')

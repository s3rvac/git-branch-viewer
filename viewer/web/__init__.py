"""
    viewer.web
    ~~~~~~~~~~

    Web interface to the viewer.

    :copyright: © 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
    :license: BSD, see LICENSE for more details
"""

from flask import Flask

app = Flask(__name__)

# Default settings.
app.config.from_pyfile('settings/default.cfg')

# Local settings.
app.config.from_pyfile('settings/local.cfg', silent=True)

# Template settings.
app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True

from viewer.web.views import * # noqa

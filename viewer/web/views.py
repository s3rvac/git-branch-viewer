"""
    viewer.web.views
    ~~~~~~~~~~~~~~~~

    Views for the web.

    :copyright: © 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
    :license: BSD, see LICENSE for more details
"""

from flask import render_template
from flask import g

from viewer import git
from . import app


@app.before_request
def before_request():
    g.repo = git.Repo(app.config['GIT_REPO_PATH'])


@app.route('/')
def index():
    branches = g.repo.get_branches_on_remote(app.config['GIT_REMOTE'])
    return render_template('index.html', repo_name=g.repo.name, branches=branches)

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
from viewer.format import format_date
from viewer.format import format_age
from . import app


@app.before_request
def setup_filters():
    app.jinja_env.filters['date'] = format_date
    app.jinja_env.filters['age'] = format_age


@app.before_request
def setup_git_repo():
    g.repo = git.Repo(app.config['GIT_REPO_PATH'])


@app.route('/')
def index():
    all_branches = g.repo.get_branches_on_remote(app.config['GIT_REMOTE'])
    ignored_branches = [branch for branch in all_branches
        if branch.name in app.config['GIT_BRANCHES_TO_IGNORE']]
    shown_branches = [branch for branch in all_branches
        if branch not in ignored_branches]
    context = {
        'repo_name': g.repo.name,
        'repo_last_update_date': g.repo.get_date_of_last_update(),
        'remote': app.config['GIT_REMOTE'],
        'shown_branches': shown_branches,
        'ignored_branches': ignored_branches,
        'commit_details_url_fmt': app.config['COMMIT_DETAILS_URL_FMT']
    }
    return render_template('index.html', **context)

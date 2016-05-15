"""
    viewer.web.views
    ~~~~~~~~~~~~~~~~

    Views for the web.

    :copyright: © 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
    :license: BSD, see LICENSE for more details
"""

import re

from flask import render_template
from flask import g

from viewer import git
from viewer.format import format_age
from viewer.format import format_date
from viewer.web import app


@app.before_request
def setup_filters():
    app.jinja_env.filters['date'] = format_date
    app.jinja_env.filters['age'] = format_age


@app.before_request
def setup_git_repo():
    g.repo = git.Repo(app.config['GIT_REPO_PATH'])


def is_ignored(branch_name):
    """Is a branch with the given name ignored?"""
    IGNORED_BRANCHES = app.config['GIT_BRANCHES_TO_IGNORE']

    # First, check for a direct match by name.
    if branch_name in IGNORED_BRANCHES:
        return True

    # Check for a regular-expression match (the branch names may be regular
    # expressions).
    for ignored_branch_re in IGNORED_BRANCHES:
        if re.fullmatch(ignored_branch_re, branch_name) is not None:
            return True

    return False


@app.route('/')
def index():
    all_branches = g.repo.get_branches_on_remote(app.config['GIT_REMOTE'])
    ignored_branches = [branch for branch in all_branches
                        if is_ignored(branch.name)]
    shown_branches = [branch for branch in all_branches
                      if branch not in ignored_branches]
    git.sort_branches(shown_branches, app.config['SORT_BRANCHES_BY'])
    context = {
        'repo_name': g.repo.name,
        'repo_last_update_date': g.repo.get_date_of_last_update(),
        'remote': app.config['GIT_REMOTE'],
        'master_branch': git.Branch(
            g.repo,
            app.config['GIT_REMOTE'],
            app.config['GIT_MASTER_BRANCH']
        ),
        'shown_branches': shown_branches,
        'ignored_branches': ignored_branches,
        'commit_details_url_fmt': app.config['COMMIT_DETAILS_URL_FMT'],
        'unmerged_commits_limit': app.config['UNMERGED_COMMITS_LIMIT'],
        'commit_subject_limit': app.config['COMMIT_SUBJECT_LIMIT']
    }
    return render_template('index.html', **context)

#!/usr/bin/env python
#
# Starts a local web server on 127.0.0.1:5000 with auto-reload that can be used
# during the development.
#
# Warning: Do NOT use it in production because it may allow attackers to
# execute arbitrary code on the server!
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

from viewer.web import app

app.run(debug=True)

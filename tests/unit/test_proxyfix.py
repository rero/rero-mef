# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the headers the application trusts from the proxies in front of it."""

from flask import Flask, request
from invenio_base.wsgi import wsgi_proxyfix

from rero_mef.config import PROXYFIX_CONFIG


def test_links_keep_the_prefix_nginx_strips():
    """The links of the API keep `/api`, the scheme and the client of nginx."""
    app = Flask(__name__)
    app.config["PROXYFIX_CONFIG"] = PROXYFIX_CONFIG

    @app.route("/mef/")
    def search():
        return {"self": request.url, "client": request.remote_addr}

    app.wsgi_app = wsgi_proxyfix()(app)
    headers = {
        # the load balancer adds the client, nginx the load balancer
        "X-Forwarded-For": "203.0.113.5, 10.0.0.1",
        "X-Forwarded-Proto": "https",
        "X-Forwarded-Prefix": "/api",
    }
    res = app.test_client().get("/mef/", headers=headers)
    assert res.json == {"self": "https://localhost/api/mef/", "client": "203.0.113.5"}

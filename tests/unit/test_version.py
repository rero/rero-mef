# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the version endpoint of the REST API."""

from flask import Flask

from rero_mef.version import __version__
from rero_mef.views import api_blueprint


def test_version():
    app = Flask(__name__)
    app.register_blueprint(api_blueprint)
    response = app.test_client().get("/version")
    assert response.status_code == 200
    assert response.json == {"version": __version__}

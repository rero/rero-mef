# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest fixtures and plugins for the API application."""

import pytest


class _ApiPrefixMiddleware:
    """WSGI middleware that strips /api prefix, mirroring production dispatch.

    In production Invenio mounts the API app at ``/api`` via
    ``DispatcherMiddleware``. This middleware reproduces that behaviour for
    the test client so that every request uses the real ``/api/…`` URL and
    ``url_for()`` returns paths that include the prefix.
    """

    def __init__(self, app, prefix="/api"):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path == self.prefix or path.startswith(self.prefix + "/"):
            environ["SCRIPT_NAME"] = self.prefix
            environ["PATH_INFO"] = path[len(self.prefix) :] or "/"
        return self.app(environ, start_response)


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Create test app with /api prefix middleware."""
    from invenio_app.factory import create_api

    def factory(**kwargs):
        app = create_api(**kwargs)
        app.wsgi_app = _ApiPrefixMiddleware(app.wsgi_app)
        return app

    return factory

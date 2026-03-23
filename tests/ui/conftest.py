# RERO MEF
# Copyright (C) 2020 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Pytest fixtures and plugins for the UI application."""

import json
import os
from os.path import dirname, join

import pytest
import yaml

from rero_mef.utils import add_oai_source

# Webpack asset keys referenced by invenio_theme and rero_mef templates.
_WEBPACK_MANIFEST_STUBS = {
    "theme.css": "/static/dist/theme.css",
    "theme.js": "/static/dist/theme.js",
    "theme-admin.css": "/static/dist/theme-admin.css",
    "global.css": "/static/dist/global.css",
    "adminlte.js": "/static/dist/adminlte.js",
    "base.js": "/static/dist/base.js",
    "i18n_app.js": "/static/dist/i18n_app.js",
    "search_ui_app.js": "/static/dist/search_ui_app.js",
    "search_ui_theme.css": "/static/dist/search_ui_theme.css",
}


@pytest.fixture(scope="session", autouse=True)
def webpack_manifest():
    """Create a stub webpack manifest so UI templates render without assets."""
    dist_dir = os.path.join(
        os.environ.get(
            "INVENIO_INSTANCE_PATH", os.path.join(os.getcwd(), ".venv/var/instance")
        ),
        "static",
        "dist",
    )
    os.makedirs(dist_dir, exist_ok=True)
    manifest_path = os.path.join(dist_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(_WEBPACK_MANIFEST_STUBS, f)


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Create test app."""
    from invenio_app.factory import create_ui

    yield create_ui


@pytest.fixture(scope="module")
def init_oai(app):
    """OAI init."""
    configs = yaml.load(
        open(join(dirname(__file__), "../data/oaisources.yml")), Loader=yaml.FullLoader
    )
    for name, values in sorted(configs.items()):
        add_oai_source(
            name=name,
            baseurl=values["baseurl"],
            metadataprefix=values.get("metadataprefix", "marc21"),
            setspecs=values.get("setspecs", ""),
            comment=values.get("comment", ""),
            update=True,
        )

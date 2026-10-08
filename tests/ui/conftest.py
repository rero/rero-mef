# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest fixtures for the application the CLI and Celery build (`create_ui`), which serves no page."""

from os.path import dirname, join

import pytest
import yaml

from rero_mef.utils import add_oai_source


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Create test app."""
    from invenio_app.factory import create_ui

    yield create_ui


@pytest.fixture(scope="module")
def init_oai(app):
    """OAI init."""
    configs = yaml.load(open(join(dirname(__file__), "../data/oaisources.yml")), Loader=yaml.FullLoader)
    for name, values in sorted(configs.items()):
        add_oai_source(
            name=name,
            baseurl=values["baseurl"],
            metadataprefix=values.get("metadataprefix", "marc21"),
            setspecs=values.get("setspecs", ""),
            comment=values.get("comment", ""),
            update=True,
        )

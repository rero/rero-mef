# -*- coding: utf-8 -*-
#
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

from __future__ import absolute_import, print_function

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

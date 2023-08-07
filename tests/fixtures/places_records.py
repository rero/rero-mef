# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2022 RERO
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

"""Places records."""

import pytest
from utils import create_record

from rero_mef.places import PlaceIdrefRecord, PlaceMefRecord


@pytest.fixture(scope='module')
def place_idref_record(app, place_idref_data):
    """Create a IdRef record."""
    return create_record(PlaceIdrefRecord, place_idref_data)


@pytest.fixture(scope='module')
def place_idref_redirect_record(app, place_idref_redirect_data):
    """Create a IdRef record."""
    return create_record(PlaceIdrefRecord, place_idref_redirect_data)


@pytest.fixture(scope='module')
def place_mef_idref_record(app, place_mef_idref_data, place_idref_record):
    """Create a IdRef record."""
    return create_record(PlaceMefRecord, place_mef_idref_data)


@pytest.fixture(scope='module')
def place_mef_idref_redirect_record(app, place_mef_idref_redirect_data,
                                    place_idref_redirect_record):
    """Create a IdRef record."""
    return create_record(PlaceMefRecord, place_mef_idref_redirect_data)

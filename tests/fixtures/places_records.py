# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Places records."""

import pytest

from rero_mef.places import PlaceGndRecord, PlaceIdrefRecord, PlaceMefRecord

from ..utils import create_record


@pytest.fixture(scope="module")
def place_idref_record(app, place_idref_data):
    """Create a IdRef record."""
    return create_record(PlaceIdrefRecord, place_idref_data)


@pytest.fixture(scope="module")
def place_idref_redirect_record(app, place_idref_redirect_data):
    """Create a IdRef record."""
    return create_record(PlaceIdrefRecord, place_idref_redirect_data)


@pytest.fixture(scope="module")
def place_gnd_record(app, place_gnd_data):
    """Create a GND record."""
    return create_record(PlaceGndRecord, place_gnd_data)


@pytest.fixture(scope="module")
def place_gnd_redirect_record(app, place_gnd_redirect_data):
    """Create a GND record."""
    return create_record(PlaceGndRecord, place_gnd_redirect_data)


@pytest.fixture(scope="module")
def place_mef_idref_record(app, place_mef_idref_data, place_idref_record):
    """Create a IdRef record."""
    return create_record(PlaceMefRecord, place_mef_idref_data)


@pytest.fixture(scope="module")
def place_mef_idref_redirect_record(
    app, place_mef_idref_redirect_data, place_idref_redirect_record
):
    """Create a IdRef record."""
    return create_record(PlaceMefRecord, place_mef_idref_redirect_data)

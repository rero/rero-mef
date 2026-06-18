# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utilities."""

from copy import deepcopy

from flask import current_app
from invenio_records_rest.utils import obj_or_import_string


def get_place_endpoints():
    """Get all places from config."""
    places = current_app.config.get("RERO_PLACES", [])
    endpoints = current_app.config.get("RECORDS_REST_ENDPOINTS", {})
    return {
        endpoint: data for endpoint, data in endpoints.items() if endpoint in places
    }


def make_identifier(identified_by):
    """Make identifier `type|(source)value`."""
    if source := identified_by.get("source"):
        return f"{identified_by['type']}|({source}){identified_by['value']}"
    return f"{identified_by['type']}|{identified_by['value']}"


def get_place_classes(without_mef=True):
    """Get place classes from config."""
    places = {}
    endpoints = deepcopy(get_place_endpoints())
    if without_mef:
        endpoints.pop("plmef", None)
    for place in endpoints:
        if record_class := obj_or_import_string(endpoints[place].get("record_class")):
            places[place] = record_class
    return places

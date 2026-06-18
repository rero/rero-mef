# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utilities."""

from copy import deepcopy

from flask import current_app
from invenio_records_rest.utils import obj_or_import_string


def get_concept_endpoints():
    """Get all contributions from config."""
    concepts = current_app.config.get("RERO_CONCEPTS", [])
    endpoints = current_app.config.get("RECORDS_REST_ENDPOINTS", {})
    return {
        endpoint: data for endpoint, data in endpoints.items() if endpoint in concepts
    }


def get_concept_classes(without_mef=True):
    """Get concept classes from config."""
    concepts = {}
    endpoints = deepcopy(get_concept_endpoints())
    if without_mef:
        concepts.pop("comef", None)
    for concept in endpoints:
        if record_class := obj_or_import_string(endpoints[concept].get("record_class")):
            concepts[concept] = record_class
    return concepts

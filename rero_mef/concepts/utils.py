# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2021 RERO
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

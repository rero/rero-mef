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

from flask import current_app


def get_concepts_endpoints():
    """Get all contributions from config."""
    concepts_endpoints = {}
    concepts = current_app.config.get('CONCEPTS', [])
    endpoints = current_app.config.get('RECORDS_REST_ENDPOINTS', {})
    for endpoint, data in endpoints.items():
        if endpoint in concepts:
            concepts_endpoints[endpoint] = data
    return concepts_endpoints

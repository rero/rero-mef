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

"""Concepts records."""

import pytest
from utils import create_record

from rero_mef.concepts import ConceptIdrefRecord, ConceptMefRecord, ConceptReroRecord


@pytest.fixture(scope="module")
def concept_rero_record(app, concept_rero_data):
    """Create a IdRef record."""
    return create_record(ConceptReroRecord, concept_rero_data)


@pytest.fixture(scope="module")
def concept_idref_record(app, concept_idref_data):
    """Create a IdRef record."""
    return create_record(ConceptIdrefRecord, concept_idref_data)


@pytest.fixture(scope="module")
def concept_idref_redirect_record(app, concept_idref_redirect_data):
    """Create a IdRef record."""
    return create_record(ConceptIdrefRecord, concept_idref_redirect_data)


@pytest.fixture(scope="module")
def concept_mef_rero_record(app, concept_mef_rero_data, concept_rero_record):
    """Create a IdRef record."""
    return create_record(ConceptMefRecord, concept_mef_rero_data)


@pytest.fixture(scope="module")
def concept_mef_idref_record(app, concept_mef_idref_data, concept_idref_record):
    """Create a IdRef record."""
    return create_record(ConceptMefRecord, concept_mef_idref_data)


@pytest.fixture(scope="module")
def concept_mef_idref_redirect_record(
    app, concept_mef_idref_redirect_data, concept_idref_redirect_record
):
    """Create a IdRef record."""
    return create_record(ConceptMefRecord, concept_mef_idref_redirect_data)

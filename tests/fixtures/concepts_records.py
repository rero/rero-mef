# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Concepts records."""

import pytest

from rero_mef.concepts import ConceptIdrefRecord, ConceptMefRecord, ConceptReroRecord

from ..utils import create_record


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

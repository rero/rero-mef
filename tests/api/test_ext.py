# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the RERO MEF extension in the REST API application."""

from invenio_indexer.signals import before_record_index

from rero_mef.concepts.listener import enrich_concept_data
from rero_mef.ext import REROMEFAPP
from rero_mef.listener import enrich_mef_data
from rero_mef.places.listener import enrich_place_data


def test_api_app_loads_the_extension(app):
    """The API indexes records too, so it needs the enrichment signals of the extension."""
    assert isinstance(app.extensions["rero-mef"], REROMEFAPP)
    assert {enrich_mef_data, enrich_concept_data, enrich_place_data} <= set(before_record_index.receivers_for(app))

# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the JSON schemas served by the REST API."""

from invenio_jsonschemas import current_jsonschemas


def test_every_schema_is_served(base_app):
    """Every schema answers with its references inlined."""
    client = base_app.test_client()
    with base_app.app_context():
        paths = sorted(current_jsonschemas.list_schemas())
    assert paths
    failed = [path for path in paths if client.get(f"/schemas/{path}").status_code != 200]
    assert failed == []
    concept = client.get("/schemas/common/concept-v0.0.1.json").json
    # the identifiers of a concept come from common/identified_by-v0.0.1.json
    assert "$ref" not in concept["properties"]["identifiedBy"]

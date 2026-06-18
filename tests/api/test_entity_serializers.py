# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for entity serializers (concepts, places, agents) and query factory."""

import json

from flask import url_for

# ── concepts serializer: add_links + ReroMefSerializer.serialize ──────────────


def test_concept_rero_item_serializer(
    client, concept_rero_record, concept_mef_rero_record
):
    """Fetching a concept entity record exercises concepts/serializers.py add_links."""
    pid = concept_rero_record.get("pid")
    url = url_for("invenio_records_rest.corero_item", pid_value=pid)
    res = client.get(url)
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    # add_links builds MEF links in the response links dict
    assert data.get("id") == pid
    assert "links" in data


def test_concept_rero_list_serializer(client, concept_rero_record):
    """List endpoint exercises concepts/serializers.py search_responsify path."""
    url = url_for("invenio_records_rest.corero_list")
    res = client.get(url)
    assert res.status_code == 200
    body = json.loads(res.get_data(as_text=True))
    assert body["hits"]["total"] >= 1


def test_concept_idref_item_serializer(
    client, concept_idref_record, concept_mef_idref_record
):
    """Fetching an idref concept record exercises add_links for coidref endpoint."""
    pid = concept_idref_record.get("pid")
    url = url_for("invenio_records_rest.cidref_item", pid_value=pid)
    res = client.get(url)
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert data.get("id") == pid


# ── places serializer: add_links + ReroMefSerializer.serialize ───────────────


def test_place_idref_item_serializer(
    client, place_idref_record, place_mef_idref_record
):
    """Fetching a place idref record exercises places/serializers.py add_links."""
    pid = place_idref_record.get("pid")
    url = url_for("invenio_records_rest.pidref_item", pid_value=pid)
    res = client.get(url)
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert data.get("id") == pid
    assert "links" in data


def test_place_idref_list_serializer(client, place_idref_record):
    """List endpoint exercises places/serializers.py search_responsify path."""
    url = url_for("invenio_records_rest.pidref_list")
    res = client.get(url)
    assert res.status_code == 200
    body = json.loads(res.get_data(as_text=True))
    assert body["hits"]["total"] >= 1


# ── query.py: SyntaxError raises InvalidQueryRESTError (400) ─────────────────


def test_query_syntax_error_returns_400(client, agent_mef_record):
    """A query_string that raises SyntaxError is caught and returned as 400."""
    from unittest import mock

    from elasticsearch_dsl.query import Q

    # Patch _default_parser inside and_search_factory to raise SyntaxError
    original_q = Q

    def bad_q(*args, **kwargs):
        if args and args[0] == "query_string":
            raise SyntaxError("bad query")
        return original_q(*args, **kwargs)

    with mock.patch("rero_mef.query.Q", side_effect=bad_q):
        url = url_for("invenio_records_rest.mef_list") + "?q=bad"
        res = client.get(url)

    assert res.status_code == 400

# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the answer to a search query the search engine cannot parse."""

import pytest
from elasticsearch.exceptions import RequestError

from rero_mef.views import invalid_query


def editor_query(term):
    """The query the RERO ILS editor autocomplete sends (remote_entities/proxy.py)."""
    return (
        f'(idref.authorized_access_point:"{term}" OR gnd.authorized_access_point:"{term}")^10 '
        f'OR (autocomplete_name:{term} OR "{term}")^4 OR ({term}) AND sources:(idref OR gnd)'
    )


@pytest.mark.parametrize("term", ["Bern : Kanton", "Paul / Peter", "Mozart!", "Wien {Stadt}", "AND"])
def test_unparsable_query_is_a_bad_request(client, term):
    """A query the RERO ILS editor builds from what its user typed answers 400, not 500."""
    res = client.get(
        "/api/agents/mef",
        query_string={"q": editor_query(term), "page": 1, "size": 10, "facets": ""},
        follow_redirects=True,
    )
    assert res.status_code == 400
    assert res.get_json()["status"] == 400


def test_parsable_query_still_answers(client):
    """Query syntax used on purpose keeps working."""
    res = client.get("/api/agents/mef/", query_string={"q": "_exists_:gnd AND pid:1", "size": 1})
    assert res.status_code == 200


def test_wrapped_parse_error_is_a_bad_request(app):
    """The search engine's rejection of a query answers 400 however it is wrapped.

    With several shards the engine reports a broken `query_string` as a `search_phase_execution_exception`, which
    invenio-records-rest does not recognise as a syntax error and lets through as a 500.
    """
    error = RequestError(
        400, "search_phase_execution_exception", {"error": {"root_cause": [{"type": "parse_exception"}]}}
    )
    assert app._find_error_handler(error, []) is invalid_query
    with app.test_request_context():
        response = invalid_query(error).get_response()
    assert response.status_code == 400
    assert response.get_json()["status"] == 400

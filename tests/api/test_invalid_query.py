# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the answer to a search query the search engine cannot parse."""

from unittest import mock

import pytest
from elasticsearch.exceptions import RequestError


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


def test_parse_exception_is_a_bad_request(client):
    """A `parse_exception` from the search engine answers 400."""
    error = RequestError(
        400, "search_phase_execution_exception", {"error": {"root_cause": [{"type": "parse_exception"}]}}
    )
    with mock.patch("rero_mef.agents.mef.api.AgentMefSearch.execute", side_effect=error):
        res = client.get("/api/agents/mef/", query_string={"q": "Mozart!", "size": 10})
    assert res.status_code == 400
    assert res.get_json()["status"] == 400


def test_other_search_errors_stay_server_errors(client):
    """A search engine error that is no parse error is not reported as an invalid query."""
    error = RequestError(
        400, "illegal_argument_exception", {"error": {"root_cause": [{"type": "illegal_argument_exception"}]}}
    )
    with mock.patch("rero_mef.agents.mef.api.AgentMefSearch.execute", side_effect=error):
        res = client.get("/api/agents/mef/", query_string={"q": "Mozart", "size": 10})
    assert res.status_code == 500

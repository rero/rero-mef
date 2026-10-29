# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the limits the REST API puts on what it is asked."""

import pytest
from flask import Flask
from invenio_records_rest.errors import SearchPaginationRESTError

from rero_mef.query import rest_search_factory
from rero_mef.views import updated_data_error


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"resolve": 1},
        {"pids": ["1", 2]},
        {"pids": []},
        {"from_date": "2022-02-02"},
        {"from_date": "2026-10-29T12:00:00+00:00", "pids": ["1"]},
    ],
)
def test_updated_data_accepted(data):
    """What rero-ils posts passes."""
    assert updated_data_error(data) is None


@pytest.mark.parametrize(
    ("data", "error"),
    [
        (None, "JSON object"),
        ("x", "JSON object"),
        ([1, 2], "JSON object"),
        ({"pids": "1"}, "pids"),
        ({"pids": [{"a": 1}]}, "pids"),
        ({"pids": [True]}, "pids"),
        ({"from_date": "garbage"}, "from_date"),
        ({"from_date": 20220202}, "from_date"),
    ],
)
def test_updated_data_rejected(data, error):
    """A body the search would fail on, once the response is streaming, is refused."""
    assert error in updated_data_error(data)


@pytest.mark.parametrize(("size", "refused"), [("10", False), ("1000", False), ("1001", True), ("x", False)])
def test_rest_search_factory_size(monkeypatch, size, refused):
    """A page larger than RERO_MEF_REST_MAX_SIZE is refused before any search."""
    app = Flask(__name__)
    app.config["RERO_MEF_REST_MAX_SIZE"] = 1000
    monkeypatch.setattr("rero_mef.query.and_search_factory", lambda self, search, query_parser: (search, {}))
    with app.test_request_context(f"/agents/mef/?size={size}"):
        if refused:
            with pytest.raises(SearchPaginationRESTError) as error:
                rest_search_factory(None, "search")
            assert error.value.get_errors() == [{"field": "size", "message": "Must be less than or equal to 1000."}]
        else:
            assert rest_search_factory(None, "search") == ("search", {})

# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for all-MEF search and item API views (rero_mef/views.py)."""

import json
from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def clear_all_mef_cache(app):
    """Clear the cache before every test in this module.

    The all_mef_search view caches ES results. Without this fixture, a cached
    response from one test leaks into the next test's assertion.
    """
    from invenio_cache import current_cache

    with app.app_context():
        current_cache.clear()
    yield


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_fake_search(hits, total):
    """Return a MagicMock search whose execute().to_dict() yields given data."""
    response = {
        "hits": {"total": {"value": total}, "hits": hits},
        "aggregations": {},
    }
    fake = mock.MagicMock()
    fake.extra.return_value = fake
    fake.__getitem__.return_value.execute.return_value.to_dict.return_value = response
    return fake


# ── /api/all/mef/ ─────────────────────────────────────────────────────────────


def test_all_mef_search_missing_alias(client):
    """Return 404 when the all_mef alias cannot be created."""
    with mock.patch("rero_mef.views._ensure_all_mef_alias", return_value=False):
        res = client.get("/api/all/mef/")
    assert res.status_code == 404
    body = json.loads(res.get_data(as_text=True))
    assert body["status"] == 404


def test_all_mef_search_invalid_query(client):
    """Return 400 for an unparseable query string."""
    from invenio_records_rest.errors import InvalidQueryRESTError

    with (
        mock.patch("rero_mef.views._ensure_all_mef_alias", return_value=True),
        mock.patch(
            "rero_mef.views.and_search_factory",
            side_effect=InvalidQueryRESTError(),
        ),
        mock.patch("rero_mef.views.AllMefSearch"),
    ):
        res = client.get("/api/all/mef/?q=:broken:")
    assert res.status_code == 400
    body = json.loads(res.get_data(as_text=True))
    assert body["status"] == 400


def test_all_mef_search_index_not_found(client):
    """Return 404 when the ES index or alias is missing at query time."""
    from elasticsearch.exceptions import NotFoundError

    fake = mock.MagicMock()
    fake.extra.return_value = fake
    fake.__getitem__.return_value.execute.side_effect = NotFoundError(
        404, "index_not_found", {}
    )

    with (
        mock.patch("rero_mef.views._ensure_all_mef_alias", return_value=True),
        mock.patch("rero_mef.views.AllMefSearch", return_value=fake),
        mock.patch("rero_mef.views.and_search_factory", return_value=(fake, {})),
    ):
        res = client.get("/api/all/mef/")
    assert res.status_code == 404
    body = json.loads(res.get_data(as_text=True))
    assert "all_mef" in body["message"]


def test_all_mef_search_success(client):
    """Return 200 with entity-classified hits for agents, concepts, and places."""
    # Use non-overlapping PID ranges that mirror production:
    # agents ~1+, concepts ~2001+, places ~3001+
    hits = [
        {"_id": "1", "_index": "mef-v1", "_source": {"pid": "1"}},
        {"_id": "2001", "_index": "concepts_mef-v1", "_source": {"pid": "2001"}},
        {"_id": "3001", "_index": "places_mef-v1", "_source": {"pid": "3001"}},
    ]
    fake = _make_fake_search(hits, 3)

    with (
        mock.patch("rero_mef.views._ensure_all_mef_alias", return_value=True),
        mock.patch("rero_mef.views.AllMefSearch", return_value=fake),
        mock.patch("rero_mef.views.and_search_factory", return_value=(fake, {})),
    ):
        res = client.get("/api/all/mef/")
    assert res.status_code == 200
    body = json.loads(res.get_data(as_text=True))
    assert body["hits"]["total"] == 3
    by_id = {h["id"]: h for h in body["hits"]["hits"]}
    assert by_id["1"]["entity"] == "agents"
    assert by_id["2001"]["entity"] == "concepts"
    assert by_id["3001"]["entity"] == "places"
    # page=1, size≥3, total=3 → no prev, no next
    assert "prev" not in body["links"]
    assert "next" not in body["links"]


def test_all_mef_search_total_as_int(client):
    """Handle ES responses where total is a plain integer (ES 6 style)."""
    hits = [{"_id": "1", "_index": "mef", "_source": {"pid": "1"}}]
    response = {"hits": {"total": 1, "hits": hits}, "aggregations": {}}
    fake = mock.MagicMock()
    fake.extra.return_value = fake
    fake.__getitem__.return_value.execute.return_value.to_dict.return_value = response

    with (
        mock.patch("rero_mef.views._ensure_all_mef_alias", return_value=True),
        mock.patch("rero_mef.views.AllMefSearch", return_value=fake),
        mock.patch("rero_mef.views.and_search_factory", return_value=(fake, {})),
    ):
        res = client.get("/api/all/mef/")
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True))["hits"]["total"] == 1


def test_all_mef_search_total_above_10000(client):
    """Return the exact total when ES reports more than 10 000 hits.

    Without track_total_hits=True, Elasticsearch caps total.value at 10 000
    even when the real count is higher.  The view must pass the full value
    through so the UI can display the correct number.
    """
    hits = [{"_id": "1", "_index": "mef-v1", "_source": {"pid": "1"}}]
    fake = _make_fake_search(hits, 1_500_000)

    with (
        mock.patch("rero_mef.views._ensure_all_mef_alias", return_value=True),
        mock.patch("rero_mef.views.AllMefSearch", return_value=fake),
        mock.patch("rero_mef.views.and_search_factory", return_value=(fake, {})),
    ):
        res = client.get("/api/all/mef/")
    assert res.status_code == 200
    body = json.loads(res.get_data(as_text=True))
    assert body["hits"]["total"] == 1_500_000
    # verify track_total_hits=True was requested
    fake.extra.assert_called_once_with(track_total_hits=True)


def test_all_mef_search_pagination_next(client):
    """Next link appears when more pages exist."""
    hits = [
        {"_id": str(i), "_index": "mef", "_source": {"pid": str(i)}} for i in range(5)
    ]
    fake = _make_fake_search(hits, 20)

    with (
        mock.patch("rero_mef.views._ensure_all_mef_alias", return_value=True),
        mock.patch("rero_mef.views.AllMefSearch", return_value=fake),
        mock.patch("rero_mef.views.and_search_factory", return_value=(fake, {})),
    ):
        res = client.get("/api/all/mef/?size=5")
    body = json.loads(res.get_data(as_text=True))
    assert "next" in body["links"]
    assert "prev" not in body["links"]


def test_all_mef_search_pagination_prev(client):
    """Prev link appears on page 2+."""
    hits = [
        {"_id": str(i), "_index": "mef", "_source": {"pid": str(i)}} for i in range(5)
    ]
    fake = _make_fake_search(hits, 20)

    with (
        mock.patch("rero_mef.views._ensure_all_mef_alias", return_value=True),
        mock.patch("rero_mef.views.AllMefSearch", return_value=fake),
        mock.patch("rero_mef.views.and_search_factory", return_value=(fake, {})),
    ):
        res = client.get("/api/all/mef/?size=5&page=2")
    body = json.loads(res.get_data(as_text=True))
    assert "prev" in body["links"]
    assert "next" in body["links"]


# ── /api/all/mef/<pid_value> ──────────────────────────────────────────────────


def test_all_mef_item_not_found(client):
    """Return 404 when the PID is unknown across all record classes."""
    with mock.patch("rero_mef.views._endpoint_for_all_mef_pid", return_value=None):
        res = client.get("/api/all/mef/UNKNOWN")
    assert res.status_code == 404
    body = json.loads(res.get_data(as_text=True))
    assert body["status"] == 404


def test_all_mef_item_redirect(client):
    """Redirect (302) to the concrete item endpoint when PID is found."""
    with mock.patch(
        "rero_mef.views._endpoint_for_all_mef_pid",
        return_value="invenio_records_rest.mef_item",
    ):
        res = client.get("/api/all/mef/1")
    assert res.status_code == 302


# ── _endpoint_for_all_mef_pid ────────────────────────────────────────────────


def test_endpoint_for_all_mef_pid_agents(app):
    """Return the agents endpoint when the record is an agent MEF record."""
    from rero_mef.views import _endpoint_for_all_mef_pid

    with mock.patch(
        "rero_mef.views.AgentMefRecord.get_record_by_pid",
        return_value={"pid": "1"},
    ):
        assert _endpoint_for_all_mef_pid("1") == "invenio_records_rest.mef_item"


def test_endpoint_for_all_mef_pid_concepts(app):
    """Return the concepts endpoint when not found in agents but found in concepts."""
    from rero_mef.views import _endpoint_for_all_mef_pid

    with (
        mock.patch(
            "rero_mef.views.AgentMefRecord.get_record_by_pid", return_value=None
        ),
        mock.patch(
            "rero_mef.views.ConceptMefRecord.get_record_by_pid",
            return_value={"pid": "2001"},
        ),
    ):
        assert _endpoint_for_all_mef_pid("2001") == "invenio_records_rest.comef_item"


def test_endpoint_for_all_mef_pid_places(app):
    """Return the places endpoint when found only in places."""
    from rero_mef.views import _endpoint_for_all_mef_pid

    with (
        mock.patch(
            "rero_mef.views.AgentMefRecord.get_record_by_pid", return_value=None
        ),
        mock.patch(
            "rero_mef.views.ConceptMefRecord.get_record_by_pid", return_value=None
        ),
        mock.patch(
            "rero_mef.views.PlaceMefRecord.get_record_by_pid",
            return_value={"pid": "3001"},
        ),
    ):
        assert _endpoint_for_all_mef_pid("3001") == "invenio_records_rest.plmef_item"


def test_endpoint_for_all_mef_pid_not_found(app):
    """Return None when PID is absent from all record classes."""
    from rero_mef.views import _endpoint_for_all_mef_pid

    with (
        mock.patch(
            "rero_mef.views.AgentMefRecord.get_record_by_pid", return_value=None
        ),
        mock.patch(
            "rero_mef.views.ConceptMefRecord.get_record_by_pid", return_value=None
        ),
        mock.patch(
            "rero_mef.views.PlaceMefRecord.get_record_by_pid", return_value=None
        ),
    ):
        assert _endpoint_for_all_mef_pid("UNKNOWN") is None


# ── _ensure_all_mef_alias ────────────────────────────────────────────────────


def test_ensure_all_mef_alias_exists(app):
    """Return True immediately when the all_mef alias exists."""
    from rero_mef.views import _ensure_all_mef_alias

    mock_client = mock.MagicMock()
    mock_client.indices.exists_alias.return_value = True

    with mock.patch("rero_mef.views.current_search_client", mock_client):
        result = _ensure_all_mef_alias()

    mock_client.indices.exists_alias.assert_called_once_with(name="all_mef")
    mock_client.indices.exists.assert_not_called()
    mock_client.indices.update_aliases.assert_not_called()
    assert result is True


def test_ensure_all_mef_alias_falls_through_to_direct_index(app):
    """Fall back to direct index check when alias does not exist."""
    from rero_mef.views import _ensure_all_mef_alias

    mock_client = mock.MagicMock()
    mock_client.indices.exists_alias.return_value = False
    mock_client.indices.exists.return_value = True

    with mock.patch("rero_mef.views.current_search_client", mock_client):
        result = _ensure_all_mef_alias()

    mock_client.indices.exists.assert_called()
    assert result is True


def test_ensure_all_mef_alias_none_found(app):
    """Return False when alias and all backing indexes are missing."""
    from rero_mef.views import _ensure_all_mef_alias

    mock_client = mock.MagicMock()
    mock_client.indices.exists_alias.return_value = False
    mock_client.indices.exists.return_value = False

    with mock.patch("rero_mef.views.current_search_client", mock_client):
        result = _ensure_all_mef_alias()

    assert result is False


def test_ensure_all_mef_alias_index_check_raises(app):
    """Re-raise unexpected errors from the index existence check."""
    import pytest

    from rero_mef.views import _ensure_all_mef_alias

    mock_client = mock.MagicMock()
    mock_client.indices.exists_alias.return_value = False
    mock_client.indices.exists.side_effect = Exception("index check failed")

    with (
        mock.patch("rero_mef.views.current_search_client", mock_client),
        pytest.raises(Exception, match="index check failed"),
    ):
        _ensure_all_mef_alias()


def test_ensure_all_mef_alias_alias_check_raises(app):
    """Re-raise unexpected errors from the alias existence check."""
    import pytest

    from rero_mef.views import _ensure_all_mef_alias

    mock_client = mock.MagicMock()
    mock_client.indices.exists_alias.side_effect = Exception("connection error")

    with (
        mock.patch("rero_mef.views.current_search_client", mock_client),
        pytest.raises(Exception, match="connection error"),
    ):
        _ensure_all_mef_alias()

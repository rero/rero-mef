# RERO MEF
# Copyright (C) 2026 RERO
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

"""Tests for RERO MEF extension (ext.py)."""

from unittest.mock import MagicMock, patch

from rero_mef.ext import REROMEFAPP


def test_ensure_all_mef_alias_success(app):
    """ensure_all_mef_alias creates alias when search is available."""
    mock_client = MagicMock()
    mock_client.indices.get_alias.return_value = {"mef-v7-20240101": {}}

    ext = REROMEFAPP.__new__(REROMEFAPP)
    with patch("rero_mef.ext.current_search_client", mock_client):
        ext.ensure_all_mef_alias(app)

    assert mock_client.indices.put_alias.call_count == 3


def test_ensure_all_mef_alias_es_not_reachable(app):
    """ensure_all_mef_alias skips gracefully when ES is not running (e.g. image build)."""
    from elasticsearch.exceptions import ConnectionError as ESConnectionError

    mock_client = MagicMock()
    mock_client.indices.exists_alias.side_effect = ESConnectionError(
        "N/A", "Connection refused"
    )

    ext = REROMEFAPP.__new__(REROMEFAPP)
    with patch("rero_mef.ext.current_search_client", mock_client):
        ext.ensure_all_mef_alias(app)  # must not raise

    mock_client.indices.get_alias.assert_not_called()
    mock_client.indices.put_alias.assert_not_called()


def test_ensure_all_mef_alias_no_search_ext(app):
    """ensure_all_mef_alias skips when invenio-search is not loaded."""
    ext = REROMEFAPP.__new__(REROMEFAPP)
    saved = app.extensions.pop("invenio-search", None)
    try:
        ext.ensure_all_mef_alias(app)
    finally:
        if saved is not None:
            app.extensions["invenio-search"] = saved


def test_ensure_all_mef_alias_get_alias_not_found(app):
    """ensure_all_mef_alias falls back to direct index when get_alias raises NotFoundError."""
    from elasticsearch.exceptions import NotFoundError

    mock_client = MagicMock()
    mock_client.indices.get_alias.side_effect = NotFoundError(
        404, "index_not_found", {}
    )
    mock_client.indices.put_alias.return_value = True

    ext = REROMEFAPP.__new__(REROMEFAPP)
    with patch("rero_mef.ext.current_search_client", mock_client):
        ext.ensure_all_mef_alias(app)

    # Falls back to using the target alias name as the index name
    assert mock_client.indices.put_alias.call_count == 3


def test_ensure_all_mef_alias_get_alias_unexpected_error(app):
    """ensure_all_mef_alias propagates unexpected errors from get_alias."""
    import pytest

    mock_client = MagicMock()
    mock_client.indices.get_alias.side_effect = ConnectionError("backend unreachable")

    ext = REROMEFAPP.__new__(REROMEFAPP)
    with (
        patch("rero_mef.ext.current_search_client", mock_client),
        pytest.raises(ConnectionError, match="backend unreachable"),
    ):
        ext.ensure_all_mef_alias(app)


def test_ensure_all_mef_alias_put_alias_not_found(app):
    """ensure_all_mef_alias continues attempting all aliases when put_alias raises NotFoundError."""
    from elasticsearch.exceptions import NotFoundError

    mock_client = MagicMock()
    mock_client.indices.get_alias.return_value = {"some-index": {}}
    mock_client.indices.put_alias.side_effect = NotFoundError(
        404, "index_not_found", {}
    )

    ext = REROMEFAPP.__new__(REROMEFAPP)
    with patch("rero_mef.ext.current_search_client", mock_client):
        ext.ensure_all_mef_alias(app)

    assert mock_client.indices.put_alias.call_count == 3


def test_ensure_all_mef_alias_put_alias_unexpected_error(app):
    """ensure_all_mef_alias propagates unexpected errors from put_alias."""
    import pytest

    mock_client = MagicMock()
    mock_client.indices.get_alias.return_value = {"some-index": {}}
    mock_client.indices.put_alias.side_effect = PermissionError("forbidden")

    ext = REROMEFAPP.__new__(REROMEFAPP)
    with (
        patch("rero_mef.ext.current_search_client", mock_client),
        pytest.raises(PermissionError, match="forbidden"),
    ):
        ext.ensure_all_mef_alias(app)

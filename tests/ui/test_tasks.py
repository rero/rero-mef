# RERO MEF
# Copyright (C) 2024-2026 RERO
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

"""Tests for Celery get_record tasks and OAI process/save tasks."""

from unittest.mock import MagicMock, patch

import pytest

from rero_mef.agents.rero.tasks import rero_get_record
from rero_mef.concepts.gnd.tasks import (
    gnd_get_record as concept_gnd_get_record,
)
from rero_mef.concepts.gnd.tasks import (
    process_records_from_dates as concept_gnd_process,
)
from rero_mef.concepts.gnd.tasks import (
    save_records_from_dates as concept_gnd_save,
)
from rero_mef.places.gnd.tasks import (
    gnd_get_record as place_gnd_get_record,
)
from rero_mef.places.gnd.tasks import (
    process_records_from_dates as place_gnd_process,
)
from rero_mef.places.gnd.tasks import (
    save_records_from_dates as place_gnd_save,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_trans(pid):
    """Return a mock Transformation whose .json contains the given pid."""
    t = MagicMock()
    t.json = {"pid": pid}
    return t


# ---------------------------------------------------------------------------
# agents/rero/tasks.py - rero_get_record
# ---------------------------------------------------------------------------


def test_rero_get_record_success(app):
    """HTTP 200 with valid XML returns (record, '…OK')."""
    mock_marc = MagicMock()
    with (
        patch("rero_mef.agents.rero.tasks.requests_retry_session") as mock_sess,
        patch(
            "rero_mef.agents.rero.tasks.parse_xml_to_array", return_value=[mock_marc]
        ),
        patch(
            "rero_mef.agents.rero.tasks.Transformation",
            return_value=_mock_trans("A000069866"),
        ),
    ):
        mock_sess.return_value.get.return_value.status_code = 200
        mock_sess.return_value.get.return_value.content = b"<xml/>"
        record, msg = rero_get_record("A000069866")
    assert record == {"pid": "A000069866"}
    assert "OK" in msg


def test_rero_get_record_pid_mismatch(app):
    """HTTP 200 but fetched PID differs → returns (None, '…PID changed…')."""
    mock_marc = MagicMock()
    with (
        patch("rero_mef.agents.rero.tasks.requests_retry_session") as mock_sess,
        patch(
            "rero_mef.agents.rero.tasks.parse_xml_to_array", return_value=[mock_marc]
        ),
        patch(
            "rero_mef.agents.rero.tasks.Transformation",
            return_value=_mock_trans("OTHER"),
        ),
    ):
        mock_sess.return_value.get.return_value.status_code = 200
        mock_sess.return_value.get.return_value.content = b"<xml/>"
        record, msg = rero_get_record("A000069866")
    assert record is None
    assert "PID changed" in msg


def test_rero_get_record_no_records(app):
    """HTTP 200 but XML parses to empty list → returns (None, '…No record')."""
    with (
        patch("rero_mef.agents.rero.tasks.requests_retry_session") as mock_sess,
        patch("rero_mef.agents.rero.tasks.parse_xml_to_array", return_value=[]),
    ):
        mock_sess.return_value.get.return_value.status_code = 200
        mock_sess.return_value.get.return_value.content = b""
        record, msg = rero_get_record("A000069866")
    assert record is None
    assert "No record" in msg


def test_rero_get_record_http_error(app):
    """Non-200 status → returns (None, '…HTTP Error: <code>')."""
    with patch("rero_mef.agents.rero.tasks.requests_retry_session") as mock_sess:
        mock_sess.return_value.get.return_value.status_code = 404
        record, msg = rero_get_record("A000069866")
    assert record is None
    assert "HTTP Error: 404" in msg


def test_rero_get_record_exception(app):
    """Network exception → returns (None, '…Error: …')."""
    with patch("rero_mef.agents.rero.tasks.requests_retry_session") as mock_sess:
        mock_sess.return_value.get.side_effect = ConnectionError("timeout")
        record, msg = rero_get_record("A000069866")
    assert record is None
    assert "Error:" in msg


def test_rero_get_record_debug_reraises(app):
    """debug=True causes the exception to propagate."""
    with patch("rero_mef.agents.rero.tasks.requests_retry_session") as mock_sess:
        mock_sess.return_value.get.side_effect = ConnectionError("timeout")
        with pytest.raises(ConnectionError):
            rero_get_record("A000069866", debug=True)


# ---------------------------------------------------------------------------
# concepts/gnd/tasks.py - gnd_get_record
# ---------------------------------------------------------------------------


def test_concept_gnd_get_record_success(app):
    """HTTP 200 with valid XML returns (record, '…OK')."""
    mock_marc = MagicMock()
    with (
        patch("rero_mef.concepts.gnd.tasks.requests_retry_session") as mock_sess,
        patch(
            "rero_mef.concepts.gnd.tasks.parse_xml_to_array", return_value=[mock_marc]
        ),
        patch(
            "rero_mef.concepts.gnd.tasks.Transformation",
            return_value=_mock_trans("007355440"),
        ),
    ):
        mock_sess.return_value.get.return_value.status_code = 200
        mock_sess.return_value.get.return_value.content = b"<xml/>"
        record, msg = concept_gnd_get_record("007355440")
    assert record == {"pid": "007355440"}
    assert "OK" in msg


def test_concept_gnd_get_record_pid_mismatch(app):
    """PID mismatch → returns (None, '…PID changed…')."""
    mock_marc = MagicMock()
    with (
        patch("rero_mef.concepts.gnd.tasks.requests_retry_session") as mock_sess,
        patch(
            "rero_mef.concepts.gnd.tasks.parse_xml_to_array", return_value=[mock_marc]
        ),
        patch(
            "rero_mef.concepts.gnd.tasks.Transformation",
            return_value=_mock_trans("OTHER"),
        ),
    ):
        mock_sess.return_value.get.return_value.status_code = 200
        mock_sess.return_value.get.return_value.content = b"<xml/>"
        record, msg = concept_gnd_get_record("007355440")
    assert record is None
    assert "PID changed" in msg


def test_concept_gnd_get_record_no_records(app):
    """Empty parse result → returns (None, '…No record')."""
    with (
        patch("rero_mef.concepts.gnd.tasks.requests_retry_session") as mock_sess,
        patch("rero_mef.concepts.gnd.tasks.parse_xml_to_array", return_value=[]),
    ):
        mock_sess.return_value.get.return_value.status_code = 200
        mock_sess.return_value.get.return_value.content = b""
        record, msg = concept_gnd_get_record("007355440")
    assert record is None
    assert "No record" in msg


def test_concept_gnd_get_record_http_error(app):
    """Non-200 status → returns (None, '…HTTP Error…')."""
    with patch("rero_mef.concepts.gnd.tasks.requests_retry_session") as mock_sess:
        mock_sess.return_value.get.return_value.status_code = 503
        record, msg = concept_gnd_get_record("007355440")
    assert record is None
    assert "HTTP Error: 503" in msg


def test_concept_gnd_get_record_exception(app):
    """Network exception → returns (None, '…Error…')."""
    with patch("rero_mef.concepts.gnd.tasks.requests_retry_session") as mock_sess:
        mock_sess.return_value.get.side_effect = ConnectionError("timeout")
        record, msg = concept_gnd_get_record("007355440")
    assert record is None
    assert "Error:" in msg


def test_concept_gnd_get_record_debug_reraises(app):
    """debug=True causes the exception to propagate."""
    with patch("rero_mef.concepts.gnd.tasks.requests_retry_session") as mock_sess:
        mock_sess.return_value.get.side_effect = ConnectionError("timeout")
        with pytest.raises(ConnectionError):
            concept_gnd_get_record("007355440", debug=True)


def test_concept_gnd_process_records_from_dates(app):
    """process_records_from_dates delegates to oai_process_records_from_dates."""
    with patch(
        "rero_mef.concepts.gnd.tasks.oai_process_records_from_dates"
    ) as mock_oai:
        mock_oai.return_value = {"concepts.gnd": {}}
        result = concept_gnd_process()
    mock_oai.assert_called_once()
    assert result == {"concepts.gnd": {}}


def test_concept_gnd_save_records_from_dates(app):
    """save_records_from_dates delegates to oai_save_records_from_dates."""
    with patch("rero_mef.concepts.gnd.tasks.oai_save_records_from_dates") as mock_oai:
        mock_oai.return_value = 0
        result = concept_gnd_save("output.xml")
    mock_oai.assert_called_once()
    assert result == 0


# ---------------------------------------------------------------------------
# places/gnd/tasks.py - gnd_get_record
# ---------------------------------------------------------------------------


def test_place_gnd_get_record_success(app):
    """HTTP 200 with valid XML returns (record, '…OK')."""
    mock_marc = MagicMock()
    with (
        patch("rero_mef.places.gnd.tasks.requests_retry_session") as mock_sess,
        patch("rero_mef.places.gnd.tasks.parse_xml_to_array", return_value=[mock_marc]),
        patch(
            "rero_mef.places.gnd.tasks.Transformation",
            return_value=_mock_trans("007355440"),
        ),
    ):
        mock_sess.return_value.get.return_value.status_code = 200
        mock_sess.return_value.get.return_value.content = b"<xml/>"
        record, msg = place_gnd_get_record("007355440")
    assert record == {"pid": "007355440"}
    assert "OK" in msg


def test_place_gnd_get_record_pid_mismatch(app):
    """PID mismatch → returns (None, '…PID changed…')."""
    mock_marc = MagicMock()
    with (
        patch("rero_mef.places.gnd.tasks.requests_retry_session") as mock_sess,
        patch("rero_mef.places.gnd.tasks.parse_xml_to_array", return_value=[mock_marc]),
        patch(
            "rero_mef.places.gnd.tasks.Transformation",
            return_value=_mock_trans("OTHER"),
        ),
    ):
        mock_sess.return_value.get.return_value.status_code = 200
        mock_sess.return_value.get.return_value.content = b"<xml/>"
        record, msg = place_gnd_get_record("007355440")
    assert record is None
    assert "PID changed" in msg


def test_place_gnd_get_record_no_records(app):
    """Empty parse result → returns (None, '…No record')."""
    with (
        patch("rero_mef.places.gnd.tasks.requests_retry_session") as mock_sess,
        patch("rero_mef.places.gnd.tasks.parse_xml_to_array", return_value=[]),
    ):
        mock_sess.return_value.get.return_value.status_code = 200
        mock_sess.return_value.get.return_value.content = b""
        record, msg = place_gnd_get_record("007355440")
    assert record is None
    assert "No record" in msg


def test_place_gnd_get_record_http_error(app):
    """Non-200 status → returns (None, '…HTTP Error…')."""
    with patch("rero_mef.places.gnd.tasks.requests_retry_session") as mock_sess:
        mock_sess.return_value.get.return_value.status_code = 500
        record, msg = place_gnd_get_record("007355440")
    assert record is None
    assert "HTTP Error: 500" in msg


def test_place_gnd_get_record_exception(app):
    """Network exception → returns (None, '…Error…')."""
    with patch("rero_mef.places.gnd.tasks.requests_retry_session") as mock_sess:
        mock_sess.return_value.get.side_effect = ConnectionError("timeout")
        record, msg = place_gnd_get_record("007355440")
    assert record is None
    assert "Error:" in msg


def test_place_gnd_get_record_debug_reraises(app):
    """debug=True causes the exception to propagate."""
    with patch("rero_mef.places.gnd.tasks.requests_retry_session") as mock_sess:
        mock_sess.return_value.get.side_effect = ConnectionError("timeout")
        with pytest.raises(ConnectionError):
            place_gnd_get_record("007355440", debug=True)


def test_place_gnd_process_records_from_dates(app):
    """process_records_from_dates delegates to oai_process_records_from_dates."""
    with patch("rero_mef.places.gnd.tasks.oai_process_records_from_dates") as mock_oai:
        mock_oai.return_value = {"places.gnd": {}}
        result = place_gnd_process()
    mock_oai.assert_called_once()
    assert result == {"places.gnd": {}}


def test_place_gnd_save_records_from_dates(app):
    """save_records_from_dates delegates to oai_save_records_from_dates."""
    with patch("rero_mef.places.gnd.tasks.oai_save_records_from_dates") as mock_oai:
        mock_oai.return_value = 0
        result = place_gnd_save("output.xml")
    mock_oai.assert_called_once()
    assert result == 0

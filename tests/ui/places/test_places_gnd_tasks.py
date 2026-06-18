# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test GND places tasks."""

from unittest import mock

import pytest

from rero_mef.places.gnd.tasks import gnd_get_record

pytestmark = pytest.mark.usefixtures("app")


@mock.patch("rero_mef.places.gnd.tasks.requests_retry_session")
def test_gnd_get_record_success(mock_session):
    """Test gnd_get_record successful retrieval."""
    # Mock XML response
    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <controlfield tag="001">040754766</controlfield>
        <datafield tag="151" ind1=" " ind2=" ">
            <subfield code="a">Lausanne</subfield>
        </datafield>
    </record>"""

    mock_response_obj = mock.Mock()
    mock_response_obj.status_code = 200
    mock_response_obj.content = xml_content
    mock_session.return_value.get.return_value = mock_response_obj

    record, message = gnd_get_record("040754766", debug=False)

    assert record is not None
    assert "OK" in message
    assert record.get("pid") == "040754766"


@mock.patch("rero_mef.places.gnd.tasks.requests_retry_session")
def test_gnd_get_record_http_error(mock_session):
    """Test gnd_get_record with HTTP error."""
    mock_response_obj = mock.Mock()
    mock_response_obj.status_code = 404
    mock_session.return_value.get.return_value = mock_response_obj

    record, message = gnd_get_record("999999999", debug=False)

    assert record is None
    assert "HTTP Error: 404" in message


@mock.patch("rero_mef.places.gnd.tasks.requests_retry_session")
def test_gnd_get_record_no_records(mock_session):
    """Test gnd_get_record when no records returned."""
    mock_response_obj = mock.Mock()
    mock_response_obj.status_code = 200
    mock_response_obj.content = b'<?xml version="1.0"?><collection/>'
    mock_session.return_value.get.return_value = mock_response_obj

    record, message = gnd_get_record("040754766", debug=False)

    assert record is None
    assert "No record" in message


@mock.patch("rero_mef.places.gnd.tasks.requests_retry_session")
def test_gnd_get_record_exception(mock_session):
    """Test gnd_get_record with exception."""
    mock_session.return_value.get.side_effect = Exception("Connection error")

    record, message = gnd_get_record("040754766", debug=False)

    assert record is None
    assert "Error: Connection error" in message


@mock.patch("rero_mef.places.gnd.tasks.requests_retry_session")
def test_gnd_get_record_pid_mismatch(mock_session):
    """Test gnd_get_record when PID doesn't match."""
    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
        <controlfield tag="001">123456789</controlfield>
        <datafield tag="151" ind1=" " ind2=" ">
            <subfield code="a">Test Place</subfield>
        </datafield>
    </record>"""

    mock_response_obj = mock.Mock()
    mock_response_obj.status_code = 200
    mock_response_obj.content = xml_content
    mock_session.return_value.get.return_value = mock_response_obj

    record, message = gnd_get_record("040754766", debug=False)

    assert record is None
    assert "PID changed" in message
    assert "040754766 -> 123456789" in message


@mock.patch("rero_mef.places.gnd.tasks.requests_retry_session")
def test_gnd_get_record_debug_reraises(mock_session):
    """Test gnd_get_record reraises exception in debug mode."""
    mock_session.return_value.get.side_effect = ValueError("Test error")

    with pytest.raises(ValueError) as exc_info:
        gnd_get_record("040754766", debug=True)

    assert str(exc_info.value) == "Test error"

# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test how OAI harvest failures reach the logs and Sentry.

Retry attempts are warnings; only the final failure is an error, tagged so an outage of one source can be found and
alerted on in Sentry.
"""

import logging
from unittest import mock

import pytest
import requests
import sentry_sdk
from flask import Flask

from rero_mef.utils import MyOAIItemIterator, _log_oai_failure

DATES = {"from": "2026-10-09", "until": "2026-10-11"}


@pytest.fixture
def app_context():
    with Flask("test").app_context():
        yield


@pytest.fixture
def sentry_events():
    events = []

    def capture(event, hint):
        events.append(event)

    sentry_sdk.init(dsn="https://key@sentry.invalid/1", before_send=capture)
    yield events
    sentry_sdk.init()


def http_error(status_code):
    response = requests.Response()
    response.status_code = status_code
    return requests.HTTPError(f"{status_code} Server Error", response=response)


def test_failure_is_one_tagged_sentry_error(app_context, sentry_events):
    _log_oai_failure("concepts.gnd", "authorities:sachbegriff", DATES, http_error(502))

    [event] = sentry_events
    assert event["level"] == "error"
    assert event["tags"] == {
        "oai.name": "concepts.gnd",
        "oai.set": "authorities:sachbegriff",
        "oai.from": "2026-10-09",
        "oai.until": "2026-10-11",
        "http.status_code": 502,
    }
    assert event["fingerprint"] == ["oai-harvest", "concepts.gnd", "HTTPError"]


def test_failure_without_http_response_has_no_status_tag(app_context, sentry_events):
    _log_oai_failure("agents.idref", None, DATES, requests.ConnectionError("refused"))

    [event] = sentry_events
    assert "http.status_code" not in event["tags"]
    assert event["tags"]["oai.set"] == ""


def test_retry_attempts_are_warnings(app_context, caplog):
    iterator = MyOAIItemIterator.__new__(MyOAIItemIterator)
    iterator.params = {"verb": "ListRecords"}
    iterator.resumption_token = None
    iterator.sickle = mock.Mock(harvest=mock.Mock(side_effect=http_error(502)))

    with mock.patch("rero_mef.utils.sleep"), pytest.raises(requests.HTTPError):
        iterator._next_response()

    assert [record.levelno for record in caplog.records] == [logging.WARNING] * 5
    assert all(record.exc_info is None for record in caplog.records)

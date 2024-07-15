# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2024 RERO
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

"""Views tests."""

from __future__ import absolute_import, print_function

import os

import mock
from sickle.response import OAIResponse
from utils import mock_response

from rero_mef.agents import Action, AgentGndRecord
from rero_mef.agents.gnd.tasks import (
    process_records_from_dates,
    save_records_from_dates,
)
from rero_mef.utils import add_oai_source, oai_get_last_run, oai_set_last_run


def test_add_oai_source(app):
    """Test add oai source."""
    msg = add_oai_source(name="test", baseurl="http://test.com")
    assert msg == "Added"
    msg = add_oai_source(name="test", baseurl="http://test.com")
    assert msg == "Not Updated"
    msg = add_oai_source(
        name="test",
        baseurl="http://test.com",
        setspecs="specs",
        comment="comment",
        update=True,
    )
    assert msg == "Updated"


def test_oai_date_no_config(app, capsys):
    assert oai_get_last_run("agents.gnd", verbose=True) is None
    captured = capsys.readouterr()
    assert captured.out == "ERROR OAI config not found: agents.gnd\n"


@mock.patch("requests.get")
def test_oai_date(app, init_oai, capsys):
    """Test oai harvesting."""
    oai_set_last_run("wrong_name", "2023_01_01", verbose=True)
    captured = capsys.readouterr()
    assert captured.out == "ERROR OAI config not found: wrong_name\n"

    oai_set_last_run("agents.gnd", "wrong_date", verbose=True)
    captured = capsys.readouterr()
    assert captured.out == (
        "OAI set lastrun agents.gnd: invalid literal for int() "
        "with base 10: b'wron'\n"
    )

    date = oai_set_last_run("agents.gnd", "2023-01-01")
    assert date == oai_get_last_run("agents.gnd", verbose=True)


@mock.patch("requests.Session.get")
def test_oai_get_record(
    mock_get, app, init_oai, aggnd_oai_139205527, aggnd_data_139205527, capsys
):
    """Test oai harvesting."""
    mock_get.return_value = mock_response(content=aggnd_oai_139205527)
    online_gnd, msg = AgentGndRecord.get_online_record("139205527")
    assert online_gnd == aggnd_data_139205527
    assert msg == (
        "SRU-agents.gnd  get: 139205527       "
        "https://services.dnb.de/sru/authorities?version=1.1"
        "&operation=searchRetrieve&query=idn%3D139205527"
        "&recordSchema=MARC21-xml | OK"
    )


class MockResponse(object):
    """Mimics the response object returned by HTTP requests."""

    def __init__(self, text):
        # request's response object carry an attribute 'text' which contains
        # the server's response data encoded as unicode.
        self.text = text
        self.content = text


class MultipleResponses(object):
    """Make multiple responses."""

    def __init__(self, empty, response):
        self.count = 0
        self.empty = empty
        self.response = response

    def __iter__(self):
        return self

    def __next__(self):
        self.count += 1
        if self.count == 1:
            return OAIResponse(MockResponse(self.response), {})
        return OAIResponse(MockResponse(self.empty), {})


@mock.patch("sickle.app.Sickle.harvest")
def test_oai_save_to_file(
    mock_sickle,
    app,
    init_oai,
    aggnd_oai_list_records_empty,
    aggnd_oai_list_records,
    tmpdir,
):
    """Test oai harvesting save file."""
    mock_sickle.side_effect = MultipleResponses(
        empty=aggnd_oai_list_records_empty, response=aggnd_oai_list_records
    )
    temp_file_name = os.path.join(tmpdir, "temp_gnd.xml")
    count = save_records_from_dates(
        file_name=temp_file_name,
        from_date="2022-01-01",
        until_date="2022-01-01",
        verbose=False,
    )
    assert count == 1


@mock.patch("sickle.app.Sickle.harvest")
def test_oai_process_records_from_dates(
    mock_sickle, app, init_oai, aggnd_oai_list_records_empty, aggnd_oai_list_records
):
    """Test oai harvesting."""
    last_run = oai_get_last_run("agents.gnd")
    mock_sickle.side_effect = MultipleResponses(
        empty=aggnd_oai_list_records_empty, response=aggnd_oai_list_records
    )
    # tray first time harvesting with records creation
    count, action_count, mef_action_count = process_records_from_dates(
        from_date="2022-01-01",
        until_date="2022-01-01",
        dbcommit=True,
        reindex=True,
        verbose=True,
        debug=True,
    )
    assert count == 1
    assert action_count == {Action.CREATE: 1}
    assert mef_action_count == {Action.CREATE: 1}
    assert last_run == oai_get_last_run("agents.gnd")

    mock_sickle.side_effect = MultipleResponses(
        empty=aggnd_oai_list_records_empty, response=aggnd_oai_list_records
    )
    # try second time harvesting with records update
    count, action_count, mef_action_count = process_records_from_dates(
        dbcommit=True, reindex=True, verbose=True, debug=True
    )
    assert count == 1
    assert action_count == {Action.UPTODATE: 1}
    assert mef_action_count == {Action.UPTODATE: 1}
    assert last_run != oai_get_last_run("agents.gnd")

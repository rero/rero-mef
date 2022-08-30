# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2022 RERO
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

"""Test REST API MEF."""

import json

from flask import url_for

from rero_mef.agents import AgentMefRecord


def test_mef_get_latest(agent_mef_record, agent_idref_record,
                        agent_gnd_record, agent_rero_record,
                        agent_gnd_redirect_record,
                        agent_mef_gnd_redirect_record):
    """Test MEF get latest."""
    mef_data = agent_mef_record.replace_refs()
    # No new record found
    assert AgentMefRecord.get_latest(pid_type='idref', pid='XXX') == {}

    # New IdRef record is old IdRef record
    data = AgentMefRecord.get_latest(pid_type='idref',
                                     pid=agent_idref_record.pid)
    data.pop('_created')
    data.pop('_updated')
    assert data == mef_data

    # New GND record is old GND record
    data = AgentMefRecord.get_latest(pid_type='gnd',
                                     pid=agent_gnd_record.pid)
    data.pop('_created')
    data.pop('_updated')
    assert data == mef_data

    # New RERO record is old RERO record
    data = AgentMefRecord.get_latest(pid_type='rero',
                                     pid=agent_rero_record.pid)
    data.pop('_created')
    data.pop('_updated')
    assert data == mef_data

    # New GND record is one redirect GND record
    data = AgentMefRecord.get_latest(pid_type='gnd',
                                     pid=agent_gnd_redirect_record.pid)
    data.pop('_created')
    data.pop('_updated')
    assert data == mef_data


def test_mef_get_idref_latest(client, agent_mef_record, agent_idref_record,
                              agent_gnd_record, agent_rero_record,
                              agent_idref_redirect_record,
                              agent_mef_idref_redirect_record):
    """Test MEF get latest."""
    mef_data = agent_mef_idref_redirect_record.replace_refs()
    # New IdRef record is one redirect IdRef record
    data = AgentMefRecord.get_latest(pid_type='idref',
                                     pid=agent_idref_record.pid)
    data.pop('_created')
    data.pop('_updated')
    assert data == mef_data

    # test REST API
    url = url_for(
        'api_blueprint.get_latest_mef',
        pid_type='idref',
        pid=agent_idref_record.pid
    )
    res = client.get(url)
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    data.pop('_created')
    data.pop('_updated')
    assert data == mef_data

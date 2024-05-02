# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2021 RERO
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

"""Test REST API GND."""

import json
from copy import deepcopy

from flask import url_for

from rero_mef.agents import Action, AgentGndRecord, AgentMefRecord


def test_view_agents_gnd(client, agent_gnd_record):
    """Test redirect GND."""
    pid = agent_gnd_record.get('pid')
    url = url_for('invenio_records_rest.aggnd_list')
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True))['aggregations'] == {
        'type': {
            'buckets': [{'doc_count': 1, 'key': 'bf:Person'}],
            'doc_count_error_upper_bound': 0,
            'sum_other_doc_count': 0
        },
        'deleted': {'doc_count': 0}
    }

    url = url_for('invenio_records_rest.aggnd_item', pid_value=pid)
    res = client.get(url, follow_redirects=True)
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert data.get('id') == pid
    assert data.get('metadata', {}).get('pid') == pid

    url = url_for('invenio_records_rest.aggnd_item', pid_value='WRONG')
    res = client.get(url, follow_redirects=True)
    assert res.status_code == 404
    assert json.loads(res.get_data(as_text=True)) == {
        "status": 404,
        "message": "PID does not exist."
    }


def test_save_deleted_data(client, agent_gnd_record, agent_gnd_data):
    """Test save deleted data GND."""
    pid = agent_gnd_record.get('pid')
    assert agent_gnd_record['identifier'] == 'http://d-nb.info/gnd/12391664X'
    data = deepcopy(agent_gnd_data)
    data = {
        'deleted': '2022-01-31T10:44:22.552001+00:00',
        'pid': pid,
        'relation_pid': {
            'type': 'redirect_to',
            'value': '1134995709'
        }
    }
    record, action = AgentGndRecord.create_or_update(
        data=data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
        test_md5=False
    )
    assert action == Action.UPDATE
    assert record['deleted'] == data['deleted']
    assert record['relation_pid'] == data['relation_pid']

    mef_record, mef_actions = record.create_or_update_mef(
        dbcommit=True,
        reindex=True
    )
    assert mef_actions == {'1': Action.CREATE}
    assert mef_record.deleted
    assert mef_record['deleted'] == record['deleted']

    record = AgentGndRecord.get_record_by_pid(pid)
    record.pop('deleted')
    record.update(data=record, dbcommit=True, reindex=True)
    mef_record, mef_actions = record.create_or_update_mef(
        dbcommit=True,
        reindex=True
    )
    mef_record = AgentMefRecord.get_record_by_pid(mef_record.pid)
    assert 'deleted' not in mef_record

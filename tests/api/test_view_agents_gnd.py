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

from flask import url_for

from rero_mef.agents.gnd.api import AgentGndRecord


def test_view_agents_gnd(client, agent_gnd_record):
    """Test redirect GND."""

    AgentGndRecord.create(
        data=agent_gnd_record,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AgentGndRecord.update_indexes()
    pid = agent_gnd_record.get('pid')
    url = url_for('api_agents_gnd.redirect_list')
    res = client.get(url)
    assert res.status_code == 308
    res = client.get(url, follow_redirects=True)
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True))['aggregations'] == {
        'agent_type': {
            'buckets': [{'doc_count': 1, 'key': 'bf:Person'}],
            'doc_count_error_upper_bound': 0,
            'sum_other_doc_count': 0
        },
        'deleted': {'doc_count': 0}
    }

    url = url_for('api_agents_gnd.redirect_item', pid=pid)
    res = client.get(url)
    assert res.status_code == 308
    res = client.get(url, follow_redirects=True)
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert data.get('id') == pid
    assert data.get('metadata', {}).get('pid') == pid

    url = url_for('api_agents_gnd.redirect_item', pid='WRONG')
    res = client.get(url, follow_redirects=True)
    assert res.status_code == 404
    assert json.loads(res.get_data(as_text=True)) == {
        "status": 404,
        "message": "PID does not exist."
    }

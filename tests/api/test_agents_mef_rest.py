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

"""Test REST API MEF."""

import json
from datetime import datetime, timedelta, timezone

from flask import url_for
from utils import postdata

from rero_mef.agents import AgentMefRecord


def test_view_agents_mef(client, agent_mef_record, agent_gnd_record,
                         agent_rero_record, agent_idref_record):
    """Test redirect MEF."""
    pid = agent_mef_record.get('pid')
    url = url_for('api_blueprint.agent_mef_redirect_list')
    res = client.get(url)
    assert res.status_code == 308
    res = client.get(url, follow_redirects=True)
    assert res.status_code == 200
    json_data = json.loads(res.get_data(as_text=True))
    assert json_data['hits']['total'] == 1
    assert json_data['aggregations'] == {
        'agent_type': {
            'buckets': [
                {'doc_count': 1, 'key': 'bf:Person'}
            ],
            'doc_count_error_upper_bound': 0,
            'sum_other_doc_count': 0
        },
        'sources': {
            'buckets': [
                {'doc_count': 1, 'key': 'gnd'},
                {'doc_count': 1, 'key': 'idref'},
                {'doc_count': 1, 'key': 'rero'}
            ],
            'doc_count_error_upper_bound': 0,
            'sum_other_doc_count': 0
        },
        'deleted': {'doc_count': 0},
        'deleted_entities': {'doc_count': 0},
    }
    url = url_for('api_blueprint.agent_mef_redirect_item', pid=pid)
    res = client.get(url)
    assert res.status_code == 308
    res = client.get(url, follow_redirects=True)
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert data.get('id') == pid
    assert data.get('metadata', {}).get('pid') == pid

    url = url_for('api_blueprint.agent_mef_redirect_item', pid='WRONG')
    res = client.get(url, follow_redirects=True)
    assert res.status_code == 404
    assert json.loads(res.get_data(as_text=True)) == {
        "status": 404,
        "message": "PID does not exist."
    }


def test_mef_get_latest(agent_mef_record, agent_idref_record,
                        agent_gnd_record, agent_rero_record,
                        agent_gnd_redirect_record,
                        agent_mef_gnd_redirect_record):
    """Test MEF get latest."""
    mef_data = agent_mef_record.add_information(resolve=True)
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


def test_agents_mef_get_idref_latest(client,
                                     agent_mef_record, agent_idref_record,
                                     agent_gnd_record, agent_rero_record,
                                     agent_idref_redirect_record,
                                     agent_mef_idref_redirect_record):
    """Test agents MEF get latest."""
    mef_data = agent_mef_idref_redirect_record.add_information(resolve=True,
                                                               sources=True)
    # New IdRef record is one redirect IdRef record
    data = AgentMefRecord.get_latest(pid_type='idref',
                                     pid=agent_idref_record.pid)
    data.pop('_created')
    data.pop('_updated')
    assert data == mef_data

    # test REST API
    url = url_for(
        'api_blueprint.agent_mef_get_latest',
        pid_type='idref',
        pid=agent_idref_record.pid
    )
    res = client.get(url)
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    data.pop('_created')
    data.pop('_updated')
    assert data == mef_data


def test_agents_mef_get_updated(client, agent_mef_record, agent_idref_record,
                                agent_gnd_record, agent_rero_record,
                                agent_idref_redirect_record,
                                agent_mef_idref_redirect_record,
                                agent_mef_gnd_redirect_record):
    """Test agents MEF get latest."""

    def utf_isoformat(date):
        """Changed datetime to UTC isoformat."""
        # we have to add +00:00 to the datetime isoformat to get
        # the same time string used in ES
        return f'{date.isoformat()}+00:00'

    mef_data = agent_mef_idref_redirect_record.add_information(resolve=True)
    mef_data.pop('sources')
    # New IdRef record is one redirect IdRef record
    res, data = postdata(
        client,
        'api_blueprint.agent_mef_get_updated',
        {}
    )
    assert res.status_code == 200
    assert data == [{
        'pid': agent_mef_record.pid,
        '_created': utf_isoformat(agent_mef_record.created),
        '_updated': utf_isoformat(agent_mef_record.updated)
    }, {
        'pid': agent_mef_gnd_redirect_record.pid,
        '_created': utf_isoformat(agent_mef_gnd_redirect_record.created),
        '_updated': utf_isoformat(agent_mef_gnd_redirect_record.updated)
    }, {
        'pid': agent_mef_idref_redirect_record.pid,
        '_created': utf_isoformat(agent_mef_idref_redirect_record.created),
        '_updated': utf_isoformat(agent_mef_idref_redirect_record.updated)
    }]

    res, data = postdata(
        client,
        'api_blueprint.agent_mef_get_updated',
        {'resolve': 1}
    )
    assert res.status_code == 200
    pids = sorted([rec.get('pid') for rec in data])
    assert pids == ['1', '2', '3']
    assert data[0]['pid'] == agent_mef_record.pid
    assert data[0]['_created'] == utf_isoformat(agent_mef_record.created)
    assert data[0]['gnd']['authorized_access_point'] == \
        'Cavalieri, Giovanni Battista, 1525-1601'
    assert data[0]['idref']['authorized_access_point'] == \
        'Brissé, Nicolas, ....-1540, grammairien'
    assert data[0]['rero']['authorized_access_point'] == \
        'Cavalieri, Giovanni Battista,, ca.1525-1601'

    res, data = postdata(
        client,
        'api_blueprint.agent_mef_get_updated',
        {'pids': ['2']}
    )
    assert res.status_code == 200
    assert data == [{
        'pid': agent_mef_gnd_redirect_record.pid,
        '_created': utf_isoformat(agent_mef_gnd_redirect_record.created),
        '_updated': utf_isoformat(agent_mef_gnd_redirect_record.updated)
    }]

    res, data = postdata(
        client,
        'api_blueprint.agent_mef_get_updated',
        {"from_date": "2022-02-02"}
    )
    assert res.status_code == 200
    assert data == [{
        'pid': agent_mef_record.pid,
        '_created': utf_isoformat(agent_mef_record.created),
        '_updated': utf_isoformat(agent_mef_record.updated)
    }, {
        'pid': agent_mef_gnd_redirect_record.pid,
        '_created': utf_isoformat(agent_mef_gnd_redirect_record.created),
        '_updated': utf_isoformat(agent_mef_gnd_redirect_record.updated)
    }, {
        'pid': agent_mef_idref_redirect_record.pid,
        '_created': utf_isoformat(agent_mef_idref_redirect_record.created),
        '_updated': utf_isoformat(agent_mef_idref_redirect_record.updated)
    }]

    date = datetime.now(timezone.utc) + timedelta(days=1)
    res, data = postdata(
        client,
        'api_blueprint.agent_mef_get_updated',
        {"from_date": date.isoformat()}
    )
    assert res.status_code == 200
    assert data == []

    date = datetime.now(timezone.utc) + timedelta(days=1)
    res, data = postdata(
        client,
        'api_blueprint.agent_mef_get_updated',
        {"from_date": date.isoformat(), "pids": ['2', '4']}
    )
    assert res.status_code == 200
    assert data == [{
        'pid': '4'
    }]

    res, data = postdata(
        client,
        'api_blueprint.agent_mef_get_updated',
        {"pids": ['2', '4']}
    )
    assert res.status_code == 200
    assert data == [{
        'pid': agent_mef_gnd_redirect_record.pid,
        '_created': utf_isoformat(agent_mef_gnd_redirect_record.created),
        '_updated': utf_isoformat(agent_mef_gnd_redirect_record.updated)
    }, {
        'pid': '4'
    }]

    mef_pid2 = agent_mef_idref_redirect_record.mark_as_deleted(
        dbcommit=True,
        reindex=True
    )
    agent_mef_gnd_redirect_record.delete(dbcommit=True, delindex=True)
    AgentMefRecord.flush_indexes()
    res, data = postdata(
        client,
        'api_blueprint.agent_mef_get_updated',
        {"pids": ['1', '2', '3', '4']}
    )
    assert res.status_code == 200
    assert data == [{
        'pid': agent_mef_record.pid,
        '_created': utf_isoformat(agent_mef_record.created),
        '_updated': utf_isoformat(agent_mef_record.updated)
    }, {
        'pid': agent_mef_idref_redirect_record.pid,
        '_created': utf_isoformat(agent_mef_idref_redirect_record.created),
        '_updated': utf_isoformat(agent_mef_idref_redirect_record.updated),
        'deleted': agent_mef_idref_redirect_record.get('deleted')
    }, {
        'pid': agent_mef_gnd_redirect_record.pid
    }, {
        'pid': '4'
    }]

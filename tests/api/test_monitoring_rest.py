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

"""Test REST API monitoring."""

import json
import time

from flask import url_for
from utils import create_and_login_monitoring_user

from rero_mef.agents.idref.api import AgentIdrefRecord
from rero_mef.utils import get_timestamp, set_timestamp


def test_monitoring_es_db_counts(client):
    """Test monitoring es_db_counts."""
    res = client.get(url_for('api_monitoring.es_db_counts'))
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True)) == {
        'data': {
            'aggnd': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'agents_gnd'},
            'agrero': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'agents_rero'},
            'aidref': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'agents_idref'},
            'cidref': {
                'db': 0, 'db-es': 0, 'es': 0, 'index': 'concepts_idref'},
            'comef': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'concepts_mef'},
            'corero': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'concepts_rero'},
            'mef': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'mef'},
            'viaf': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'viaf'}
        }
    }


def test_monitoring_check_es_db_counts(app, client, agent_idref_data):
    """Test monitoring check_es_db_counts."""
    res = client.get(url_for('api_monitoring.check_es_db_counts'))
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True)) == {
        'data': {'status': 'green'}}

    AgentIdrefRecord.create(
        data=agent_idref_data,
        delete_pid=False,
        dbcommit=True,
        reindex=False)
    AgentIdrefRecord.flush_indexes()
    res = client.get(url_for('api_monitoring.check_es_db_counts'))
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True)) == {
        'data': {'status': 'red'},
        'errors': [{
            'code': 'DB_ES_COUNTER_MISSMATCH',
            'details': 'There are 1 items from aidref missing in ES.',
            'id': 'DB_ES_COUNTER_MISSMATCH',
            'links': {
                'about': 'http://localhost/monitoring/check_es_db_counts',
                'aidref': 'http://localhost/monitoring/missing_pids/aidref'
            },
            'title': "DB items counts don't match ES items count."
        }]
    }

    # this view is only accessible by admin
    res = client.get(url_for('api_monitoring.missing_pids', doc_type='aidref'))
    assert res.status_code == 401

    create_and_login_monitoring_user(app, client)

    res = client.get(url_for(
        'api_monitoring.missing_pids', doc_type='aidref', delay=0))
    assert res.status_code == 200

    assert json.loads(res.get_data(as_text=True)) == {
        'data': {
            'DB': [],
            'ES': ['http://localhost/agents/idref/069774331'],
            'ES duplicate': []
        }
    }


def test_timestamps(app, client):
    """Test timestamps"""
    time_stamp = set_timestamp('test', msg='test msg')
    assert get_timestamp('test') == {'time': time_stamp, 'msg': 'test msg'}
    res = client.get(url_for('api_monitoring.timestamps'))
    assert res.status_code == 401

    create_and_login_monitoring_user(app, client)

    res = client.get(url_for('api_monitoring.timestamps'))
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True)) == {
        'data': {
            'test': {
                'msg': 'test msg',
                'unixtime': time.mktime(time_stamp.timetuple()),
                'utctime': time_stamp.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    }

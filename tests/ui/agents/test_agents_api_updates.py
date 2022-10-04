# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2020 RERO
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

"""Test agents api."""

import mock

from rero_mef.agents.gnd.api import AgentGndRecord
from rero_mef.agents.idref.api import AgentIdrefRecord
from rero_mef.agents.mef.api import AgentMefRecord
from rero_mef.agents.rero.api import AgentReroRecord
from rero_mef.agents.viaf.api import AgentViafRecord


@mock.patch(
    'rero_mef.agents.viaf.api.AgentViafRecord.get_online_viaf_record')
def test_create_agent_updates(
        mock_get, app, agent_idref_data, agent_gnd_data,
        agent_rero_data):
    """Test create agent record with VIAF links."""
    # we have to mock the access to viaf
    mock_get.return_value = {
        'pid': '37268949',
        'idref_pid': '069774331',
        'gnd_pid': '100769527xxx'
    }
    # create first record no VIAF and MEF records exist
    assert AgentMefRecord.count() == 0
    assert AgentViafRecord.count() == 0
    record, action, m_record, m_action, v_record, online = \
        AgentIdrefRecord.create_or_update_agent_mef_viaf(
            data=agent_idref_data,
            dbcommit=True,
            reindex=True,
            online=True
        )
    assert action.name == 'CREATE'
    assert record['pid'] == '069774331'
    assert AgentMefRecord.count() == 1
    assert AgentViafRecord.count() == 1
    assert online

    # we should have a MEF and VIAF record now
    mef_pid = list(AgentMefRecord.get_all_pids())[-1]
    agent_mef_record = AgentMefRecord.get_record_by_pid(mef_pid)
    assert agent_mef_record.get('pid') == '1'
    assert agent_mef_record.get('viaf_pid') == '37268949'
    assert agent_mef_record.get('idref')
    assert 'idref' in agent_mef_record
    viaf_pid = list(AgentViafRecord.get_all_pids())[-1]
    agent_viaf_record = AgentViafRecord.get_record_by_pid(viaf_pid)
    assert agent_viaf_record.get('pid') == '37268949'
    assert agent_viaf_record.get('idref_pid') == '069774331'
    assert agent_viaf_record.get('gnd_pid') == '100769527xxx'

    # we have to mock the access to VIAF
    mock_get.return_value = {
        'pid': '66739143',
        'gnd_pid': '12391664X',
        'idref_pid': '068979401',
        'rero_pid': 'A023655346'
    }
    # create second record
    record, action, m_record, m_action, v_record, online = \
        AgentGndRecord.create_or_update_agent_mef_viaf(
            data=agent_gnd_data,
            dbcommit=True,
            reindex=True,
            online=True
        )
    assert action.name == 'CREATE'
    assert record['pid'] == '12391664X'
    assert AgentMefRecord.count() == 2
    assert AgentViafRecord.count() == 2
    assert online

    mef_pid = list(AgentMefRecord.get_all_pids())[-1]
    agent_mef_record = AgentMefRecord.get_record_by_pid(mef_pid)
    assert agent_mef_record.get('pid') == '2'
    assert agent_mef_record.get('viaf_pid') == '66739143'
    assert 'gnd' in agent_mef_record
    viaf_pid = list(AgentViafRecord.get_all_pids())[-1]
    agent_viaf_record = AgentViafRecord.get_record_by_pid(viaf_pid)
    assert agent_viaf_record.get('pid') == '66739143'
    assert agent_viaf_record.get('gnd_pid') == '12391664X'
    assert agent_viaf_record.get('idref_pid') == '068979401'
    assert agent_viaf_record.get('rero_pid') == 'A023655346'

    record, action, m_record, m_action, v_record, online = \
        AgentReroRecord.create_or_update_agent_mef_viaf(
            data=agent_rero_data,
            dbcommit=True,
            reindex=True,
            online=True
        )

    mef_pid = list(AgentMefRecord.get_all_pids())[-1]
    agent_mef_record = AgentMefRecord.get_record_by_pid(mef_pid)
    assert agent_mef_record.get('pid') == '2'
    assert agent_mef_record.get('viaf_pid') == '66739143'
    assert 'gnd' in agent_mef_record
    assert 'rero' in agent_mef_record
    viaf_pid = list(AgentViafRecord.get_all_pids())[-1]
    agent_viaf_record = AgentViafRecord.get_record_by_pid(viaf_pid)
    assert agent_viaf_record.get('pid') == '66739143'
    assert agent_viaf_record.get('gnd_pid') == '12391664X'
    assert agent_viaf_record.get('idref_pid') == '068979401'
    assert agent_viaf_record.get('rero_pid') == 'A023655346'

    agent_mef_record = AgentMefRecord.get_mef_by_viaf_pid(viaf_pid)
    assert agent_mef_record == {
        'pid': '2',
        'viaf_pid': '66739143',
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'gnd': {'$ref': 'https://mef.rero.ch/api/agents/gnd/12391664X'},
        'rero': {'$ref': 'https://mef.rero.ch/api/agents/rero/A023655346'}
    }

    new_viaf_pid = 'xxxxxxxx'
    new_viaf_record = {
        'pid': new_viaf_pid,
        'gnd_pid': '12391664X',
        'idref_pid': '069774331',
        'rero_pid': 'A023655346'
    }
    mock_get.return_value = new_viaf_record
    rec, msg = agent_viaf_record.delete(dbcommit=True, delindex=True,
                                        online=True)
    viaf_rec = AgentViafRecord.get_record_by_pid(new_viaf_pid)
    assert viaf_rec == new_viaf_record

    agent_mef_record = AgentMefRecord.get_mef_by_viaf_pid(new_viaf_pid)
    assert agent_mef_record == {
        'viaf_pid': 'xxxxxxxx',
        'gnd': {'$ref': 'https://mef.rero.ch/api/agents/gnd/12391664X'},
        'rero': {'$ref': 'https://mef.rero.ch/api/agents/rero/A023655346'},
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'pid': '3'
    }
    # test split of MEF record by VIAF change.
    assert AgentMefRecord.count() == 2
    changed_viaf_record = {
        'pid': new_viaf_pid,
        'idref_pid': '069774331',
        'rero_pid': 'A023655346'
    }
    viaf_rec.replace(data=changed_viaf_record, dbcommit=True, reindex=True)
    assert AgentMefRecord.count() == 3

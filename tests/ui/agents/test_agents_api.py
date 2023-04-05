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

import os

from rero_mef.agents import Action, AgentGndRecord, AgentIdrefRecord, \
    AgentMefRecord, AgentReroRecord, AgentViafRecord
from rero_mef.utils import export_json_records, number_records_in_file


def test_create_agent_record_with_viaf_links(
        app, agent_viaf_data, agent_gnd_data, agent_rero_data,
        agent_idref_data, tmpdir):
    """Test create agent record with VIAF links."""
    viaf_record, action = AgentViafRecord.create_or_update(
        agent_viaf_data, dbcommit=True, reindex=True)
    AgentViafRecord.flush_indexes()
    assert action.name == 'CREATE'
    assert viaf_record['pid'] == '66739143'
    assert viaf_record['gnd_pid'] == '12391664X'
    assert viaf_record['rero_pid'] == 'A023655346'
    assert viaf_record['idref_pid'] == '069774331'
    assert len(viaf_record.get_agents_pids()) == 3
    assert viaf_record.get_agents_records() == []
    _, pids_viaf = viaf_record.get_missing_agent_pids('aidref')
    assert pids_viaf == ['66739143']

    gnd_record, action = AgentGndRecord.create_or_update(
        data=agent_gnd_data, dbcommit=True, reindex=True)
    assert action.name == 'CREATE'
    assert gnd_record['pid'] == '12391664X'

    m_record, m_action = gnd_record.create_or_update_mef(
        dbcommit=True, reindex=True)
    assert m_action.name == 'CREATE'
    assert m_record == {
        '$schema': 'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'gnd': {'$ref': 'https://mef.rero.ch/api/agents/gnd/12391664X'},
        'pid': '1',
        'type': 'bf:Person',
        'viaf_pid': '66739143'
    }
    assert viaf_record.get_agents_records() == [agent_gnd_data]
    assert viaf_record.get_viaf(m_record) == [viaf_record]
    assert viaf_record.get_viaf(gnd_record) == [viaf_record]
    pids_db, pids_viaf = viaf_record.get_missing_agent_pids('aggnd')
    assert pids_db == []
    assert pids_viaf == []

    rero_record, action = AgentReroRecord.create_or_update(
        data=agent_rero_data, dbcommit=True, reindex=True)
    assert action.name == 'CREATE'
    assert rero_record['pid'] == 'A023655346'
    m_record, m_action = rero_record.create_or_update_mef(
        dbcommit=True, reindex=True)
    assert m_action.name == 'UPDATE'
    assert m_record == {
        '$schema': 'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'gnd': {'$ref': 'https://mef.rero.ch/api/agents/gnd/12391664X'},
        'pid': '1',
        'rero': {'$ref': 'https://mef.rero.ch/api/agents/rero/A023655346'},
        'type': 'bf:Person',
        'viaf_pid': '66739143'
    }
    assert viaf_record.get_agents_records() == [
        agent_gnd_data, agent_rero_data]

    idref_record, action = AgentIdrefRecord.create_or_update(
        data=agent_idref_data, dbcommit=True, reindex=True)
    assert action.name == 'CREATE'
    assert idref_record['pid'] == '069774331'
    m_record, m_action = idref_record.create_or_update_mef(
        dbcommit=True, reindex=True)
    assert m_action.name == 'UPDATE'
    assert m_record == {
        '$schema': 'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'gnd': {'$ref': 'https://mef.rero.ch/api/agents/gnd/12391664X'},
        'idref': {'$ref': 'https://mef.rero.ch/api/agents/idref/069774331'},
        'pid': '1',
        'rero': {'$ref': 'https://mef.rero.ch/api/agents/rero/A023655346'},
        'type': 'bf:Person',
        'viaf_pid': '66739143'
    }
    assert viaf_record.get_agents_records() == [
        agent_idref_data, agent_gnd_data, agent_rero_data]

    assert m_record == AgentMefRecord.get_mef(
        entity_pid=idref_record.pid, entity_name=idref_record.name)[0]
    assert m_record.pid == AgentMefRecord.get_mef(
        entity_pid=gnd_record.pid, entity_name=gnd_record.name,
        pid_only=True)[0]
    mef_rec_resolved = AgentMefRecord.get_mef(
        entity_pid=viaf_record.pid, entity_name=viaf_record.name)[0]
    assert m_record == mef_rec_resolved

    mef_rec_resolved = mef_rec_resolved.replace_refs()
    assert mef_rec_resolved.get('gnd').get('pid') == gnd_record.pid
    assert mef_rec_resolved.get('rero').get('pid') == rero_record.pid
    assert mef_rec_resolved.get('idref').get('pid') == idref_record.pid

    # Test JSON export.
    tmp_file_name = os.path.join(tmpdir, 'mef.json')
    export_json_records(
        pids=AgentMefRecord.get_all_pids(),
        pid_type='mef',
        output_file_name=tmp_file_name,
    )
    assert number_records_in_file(tmp_file_name, 'json') == 1
    assert '$schema' in open(tmp_file_name).read()
    export_json_records(
        pids=AgentMefRecord.get_all_pids(),
        pid_type='mef',
        output_file_name=tmp_file_name,
        schema=False
    )
    assert number_records_in_file(tmp_file_name, 'json') == 1
    assert '$schema' not in open(tmp_file_name).read()

    # Test update agent record with VIAF links.
    returned_record, action = AgentGndRecord.create_or_update(
        data=agent_gnd_data, dbcommit=True, reindex=True)
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == '12391664X'

    returned_record, action = AgentReroRecord.create_or_update(
        data=agent_rero_data, dbcommit=True, reindex=True)
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == 'A023655346'

    returned_record, action = AgentIdrefRecord.create_or_update(
        data=agent_idref_data, dbcommit=True, reindex=True)
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == '069774331'

    # Test update MD5 agent record with VIAF links.
    returned_record, action = AgentGndRecord.create_or_update(
        data=agent_gnd_data, dbcommit=True, reindex=True, test_md5=True)
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == '12391664X'

    returned_record, action = AgentReroRecord.create_or_update(
        data=agent_rero_data, dbcommit=True, reindex=True, test_md5=True)
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == 'A023655346'

    returned_record, action = AgentIdrefRecord.create_or_update(
        data=agent_idref_data, dbcommit=True, reindex=True, test_md5=True)
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == '069774331'

    # VIAF update with delete
    rero_pid = viaf_record.pop('rero_pid')
    viaf_record = viaf_record.update(
        data=viaf_record, dbcommit=True, reindex=True)
    assert viaf_record.get_agents_pids() == [
        {
            'pid': idref_record.pid,
            'record_class': AgentIdrefRecord
        }, {
            'pid': gnd_record.pid,
            'record_class': AgentGndRecord
        }
    ]
    mef_record_rero = AgentMefRecord.get_mef(
        entity_pid=rero_record.pid, entity_name=rero_record.name)[0]
    assert mef_record_rero.get_entities_pids() == [{
        'pid': rero_record.pid,
        'record_class': AgentReroRecord
    }]

    # VIAF update with merge
    viaf_record = AgentViafRecord.get_record_by_pid(viaf_record.pid)
    viaf_record['rero_pid'] = rero_pid
    viaf_record = viaf_record.update(
        data=viaf_record, dbcommit=True, reindex=True)
    assert viaf_record.get_agents_pids() == [
        {
            'pid': idref_record.pid,
            'record_class': AgentIdrefRecord
        }, {
            'pid': gnd_record.pid,
            'record_class': AgentGndRecord
        }, {
           'pid': rero_record.pid,
           'record_class': AgentReroRecord
        }
    ]
    mef_record_rero = AgentMefRecord.get_record_by_pid(mef_record_rero.pid)
    assert 'rero' not in mef_record_rero

    # VIAF delete
    _, action, mef_actions = viaf_record.delete(dbcommit=True, delindex=True)
    assert action == Action.DELETE
    assert mef_actions == [
        'Mark as deleted MEF: 1',
        'idref: 069774331 MEF: 3 create',
        'gnd: 12391664X MEF: 4 create',
        'rero: A023655346 MEF: 5 create',
    ]

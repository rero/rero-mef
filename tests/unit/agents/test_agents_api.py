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

from rero_mef.agents.gnd.api import AgentGndRecord
from rero_mef.agents.idref.api import AgentIdrefRecord
from rero_mef.agents.mef.api import AgentMefRecord
from rero_mef.agents.rero.api import AgentReroRecord
from rero_mef.agents.viaf.api import AgentViafRecord


def test_create_agent_record_with_viaf_links(
        app, agent_viaf_record, agent_gnd_record, agent_rero_record,
        agent_idref_record):
    """Test create agent record with VIAF links."""
    viaf_record, action = AgentViafRecord.create_or_update(
        agent_viaf_record, dbcommit=True, reindex=True
    )
    AgentViafRecord.flush_indexes()
    assert action.name == 'CREATE'
    assert viaf_record['pid'] == '66739143'
    assert viaf_record['gnd_pid'] == '12391664X'
    assert viaf_record['rero_pid'] == 'A023655346'
    assert viaf_record['idref_pid'] == '069774331'

    record, action, m_record, m_action, v_record, online = \
        AgentGndRecord.create_or_update_agent_mef_viaf(
            data=agent_gnd_record,
            dbcommit=True,
            reindex=True,
            online=False
        )

    assert action.name == 'CREATE'
    assert record['pid'] == '12391664X'
    assert m_action.name == 'CREATE'
    assert m_record == {
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'gnd': {'$ref': 'https://mef.rero.ch/api/agents/gnd/12391664X'},
        'pid': '1',
        'viaf_pid': '66739143'
    }

    record, action, m_record, m_action, v_record, online = \
        AgentReroRecord.create_or_update_agent_mef_viaf(
            data=agent_rero_record,
            dbcommit=True,
            reindex=True,
            online=False
        )
    assert action.name == 'CREATE'
    assert record['pid'] == 'A023655346'
    assert m_action.name == 'UPDATE'
    assert m_record == {
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'gnd': {'$ref': 'https://mef.rero.ch/api/agents/gnd/12391664X'},
        'pid': '1',
        'rero': {'$ref': 'https://mef.rero.ch/api/agents/rero/A023655346'},
        'viaf_pid': '66739143'
    }

    record, action, m_record, m_action, v_record, online = \
        AgentIdrefRecord.create_or_update_agent_mef_viaf(
            data=agent_idref_record,
            dbcommit=True,
            reindex=True,
            online=False
        )
    assert action.name == 'CREATE'
    assert record['pid'] == '069774331'
    assert m_action.name == 'UPDATE'
    assert m_record == {
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'gnd': {'$ref': 'https://mef.rero.ch/api/agents/gnd/12391664X'},
        'idref': {'$ref': 'https://mef.rero.ch/api/agents/idref/069774331'},
        'pid': '1',
        'rero': {'$ref': 'https://mef.rero.ch/api/agents/rero/A023655346'},
        'viaf_pid': '66739143'
    }

    assert m_record == AgentMefRecord.get_mef_by_entity_pid(
        record.pid, 'idref')
    assert m_record.pid == AgentMefRecord.get_mef_by_entity_pid(
        record.pid, 'idref', pid_only=True)
    assert AgentMefRecord.get_mef_by_viaf_pid(viaf_record.pid) == m_record


def test_update_agent_record_with_viaf_links(
        app, agent_viaf_record, agent_gnd_record, agent_rero_record,
        agent_idref_record):
    """Test create agent record with VIAF links."""
    returned_record, action = AgentGndRecord.create_or_update(
        agent_gnd_record, dbcommit=True, reindex=True
    )
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == '12391664X'

    returned_record, action = AgentReroRecord.create_or_update(
        agent_rero_record, dbcommit=True, reindex=True
    )
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == 'A023655346'

    returned_record, action = AgentIdrefRecord.create_or_update(
        agent_idref_record, dbcommit=True, reindex=True
    )
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == '069774331'


def test_uptodate_agent_record_with_viaf_links_md5(
        app, agent_viaf_record, agent_gnd_record, agent_rero_record,
        agent_idref_record):
    """Test create agent record with VIAF links."""
    returned_record, action = AgentGndRecord.create_or_update(
        agent_gnd_record, dbcommit=True, reindex=True, test_md5=True
    )
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == '12391664X'

    returned_record, action = AgentReroRecord.create_or_update(
        agent_rero_record, dbcommit=True, reindex=True, test_md5=True
    )
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == 'A023655346'

    returned_record, action = AgentIdrefRecord.create_or_update(
        agent_idref_record, dbcommit=True, reindex=True,
        test_md5=True
    )
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == '069774331'

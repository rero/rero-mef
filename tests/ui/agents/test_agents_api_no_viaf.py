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
from rero_mef.agents.rero.api import AgentReroRecord


def test_create_agent_record_no_viaf_links(
        app, agent_gnd_data, agent_rero_data, agent_idref_data):
    """Test create agent record without VIAF links."""
    record, action, m_record, m_action, v_record, online = \
        AgentGndRecord.create_or_update_agent_mef_viaf(
            data=agent_gnd_data,
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
    }

    record, action, m_record, m_action, v_record, online = \
        AgentReroRecord.create_or_update_agent_mef_viaf(
            data=agent_rero_data,
            dbcommit=True,
            reindex=True,
            online=False
        )
    assert action.name == 'CREATE'
    assert record['pid'] == 'A023655346'
    assert m_action.name == 'CREATE'
    assert m_record == {
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'pid': '2',
        'rero': {'$ref': 'https://mef.rero.ch/api/agents/rero/A023655346'},
    }

    record, action, m_record, m_action, v_record, online = \
        AgentIdrefRecord.create_or_update_agent_mef_viaf(
            data=agent_idref_data,
            dbcommit=True,
            reindex=True,
            online=False
        )
    assert action.name == 'CREATE'
    assert record['pid'] == '069774331'
    assert m_action.name == 'CREATE'
    assert m_record == {
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'idref': {'$ref': 'https://mef.rero.ch/api/agents/idref/069774331'},
        'pid': '3',
    }

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

from rero_mef.agents import Action, AgentGndRecord, AgentIdrefRecord, \
    AgentReroRecord


def test_create_agent_record_no_viaf_links(
        app, agent_gnd_data, agent_rero_data, agent_idref_data):
    """Test create agent record without VIAF links."""
    gnd_record, action = AgentGndRecord.create_or_update(
            data=agent_gnd_data, dbcommit=True, reindex=True)
    assert action == Action.CREATE
    assert gnd_record['pid'] == '12391664X'

    m_record, m_actions = gnd_record.create_or_update_mef(
        dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.CREATE}
    assert m_record == {
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'gnd': {'$ref': 'https://mef.rero.ch/api/agents/gnd/12391664X'},
        'pid': '1',
        'type': 'bf:Person'
    }

    rero_record, action = AgentReroRecord.create_or_update(
        data=agent_rero_data, dbcommit=True, reindex=True)
    assert action == Action.CREATE
    assert rero_record['pid'] == 'A023655346'

    m_record, m_actions = rero_record.create_or_update_mef(
        dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.CREATE}
    assert m_record == {
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'pid': '2',
        'rero': {'$ref': 'https://mef.rero.ch/api/agents/rero/A023655346'},
        'type': 'bf:Person'
    }

    idref_record, action = AgentIdrefRecord.create_or_update(
        data=agent_idref_data, dbcommit=True, reindex=True)
    assert action == Action.CREATE
    assert idref_record['pid'] == '069774331'

    m_record, m_actions = idref_record.create_or_update_mef(
        dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.CREATE}
    assert m_record == {
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'idref': {'$ref': 'https://mef.rero.ch/api/agents/idref/069774331'},
        'pid': '3',
        'type': 'bf:Person'
    }

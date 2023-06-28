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

"""Test signals."""

from rero_mef.agents import AgentGndRecord, AgentMefSearch, AgentViafRecord


def test_create_mef_with_viaf_links(app, agent_viaf_data, agent_gnd_data):
    """Test create MEF record from agent with VIAF links."""
    v_record, action = AgentViafRecord.create_or_update(
        data=agent_viaf_data, dbcommit=True, reindex=True)
    assert action.name == 'CREATE'
    assert v_record['pid'] == '66739143'
    assert v_record['gnd_pid'] == '12391664X'
    assert v_record['rero_pid'] == 'A023655346'
    assert v_record['idref_pid'] == '069774331'

    record, action = AgentGndRecord.create_or_update(
        data=agent_gnd_data, dbcommit=True, reindex=True)
    assert action.name == 'CREATE'
    assert record['pid'] == '12391664X'

    m_record, m_action = record.create_or_update_mef(
        dbcommit=True, reindex=True)
    assert m_action.name == 'CREATE'
    assert '$ref' in m_record['gnd']

    query = AgentMefSearch() \
        .filter('term', gnd__pid='12391664X') \
        .scan()
    result = next(query)
    assert result.sources == ['gnd']
    assert result.gnd.pid == v_record['gnd_pid']
    assert result.viaf_pid == v_record.pid

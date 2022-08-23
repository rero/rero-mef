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

from rero_mef.agents.gnd.api import AgentGndRecord
from rero_mef.agents.mef.api import AgentMefSearch
from rero_mef.agents.viaf.api import AgentViafRecord


def test_create_mef_with_viaf_links(app, agent_viaf_data, agent_gnd_data):
    """Test create MEF record from agent with VIAF links."""
    v_record, action = AgentViafRecord.create_or_update(
        agent_viaf_data, dbcommit=True, reindex=True
    )
    assert action.name == 'CREATE'
    assert v_record['pid'] == '66739143'
    assert v_record['gnd_pid'] == '12391664X'
    assert v_record['rero_pid'] == 'A023655346'
    assert v_record['idref_pid'] == '069774331'

    record, action, m_record, m_action, v_record, online = \
        AgentGndRecord.create_or_update_agent_mef_viaf(
            data=agent_gnd_data,
            dbcommit=True,
            reindex=True,
            online=False
        )
    assert action.name == 'CREATE'
    assert record['pid'] == '12391664X'

    query = AgentMefSearch(). \
        filter('term', gnd__pid='12391664X'). \
        source('sources').scan()
    assert next(query).sources == ['gnd']

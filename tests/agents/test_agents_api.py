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
from rero_mef.agents.viaf.api import AgentViafRecord


def test_create_agent_record_with_viaf_links(
        app, viaf_record, gnd_record, rero_record, idref_record):
    """Test create agent record with viaf links."""
    returned_record, action = AgentViafRecord.create_or_update(
        viaf_record, dbcommit=True, reindex=True
    )
    AgentViafRecord.update_indexes()
    assert action.name == 'CREATE'
    assert returned_record['pid'] == '66739143'
    assert returned_record['gnd_pid'] == '12391664X'
    assert returned_record['rero_pid'] == 'A023655346'
    assert returned_record['idref_pid'] == '069774331'

    record, action, m_record, m_action, v_record, online = \
        AgentGndRecord.create_or_update_agent_mef_viaf(
            data=gnd_record,
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
        'gnd': {'$ref': 'https://mef.rero.ch/api/gnd/12391664X'},
        'pid': '1',
        'viaf_pid': '66739143'
    }

    record, action, m_record, m_action, v_record, online = \
        AgentReroRecord.create_or_update_agent_mef_viaf(
            data=rero_record,
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
        'gnd': {'$ref': 'https://mef.rero.ch/api/gnd/12391664X'},
        'pid': '1',
        'rero': {'$ref': 'https://mef.rero.ch/api/rero/A023655346'},
        'viaf_pid': '66739143'
    }

    record, action, m_record, m_action, v_record, online = \
        AgentIdrefRecord.create_or_update_agent_mef_viaf(
            data=idref_record,
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
        'gnd': {'$ref': 'https://mef.rero.ch/api/gnd/12391664X'},
        'idref': {'$ref': 'https://mef.rero.ch/api/idref/069774331'},
        'pid': '1',
        'rero': {'$ref': 'https://mef.rero.ch/api/rero/A023655346'},
        'viaf_pid': '66739143'
    }


def test_update_agent_record_with_viaf_links(
        app, viaf_record, gnd_record, rero_record, idref_record):
    """Test create agent record with viaf links."""
    returned_record, action = AgentGndRecord.create_or_update(
        gnd_record, dbcommit=True, reindex=True
    )
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == '12391664X'

    returned_record, action = AgentReroRecord.create_or_update(
        rero_record, dbcommit=True, reindex=True
    )
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == 'A023655346'

    returned_record, action = AgentIdrefRecord.create_or_update(
        idref_record, dbcommit=True, reindex=True
    )
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == '069774331'


def test_uptodate_agent_record_with_viaf_links_md5(
        app, viaf_record, gnd_record, rero_record, idref_record):
    """Test create agent record with viaf links."""
    returned_record, action = AgentGndRecord.create_or_update(
        gnd_record, dbcommit=True, reindex=True, test_md5=True
    )
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == '12391664X'

    returned_record, action = AgentReroRecord.create_or_update(
        rero_record, dbcommit=True, reindex=True, test_md5=True
    )
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == 'A023655346'

    returned_record, action = AgentIdrefRecord.create_or_update(
        idref_record, dbcommit=True, reindex=True,
        test_md5=True
    )
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == '069774331'

# -*- coding: utf-8 -*-
#
# This file is part of RERO MEF.
# Copyright (C) 2018 RERO.
#
# RERO MEF is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO MEF is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO MEF; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Test agents api."""

from rero_mef.agents.gnd.api import AgentGndRecord
from rero_mef.agents.idref.api import AgentIdrefRecord
from rero_mef.agents.rero.api import AgentReroRecord


def test_create_agent_record_no_viaf_links(
        app, gnd_record, rero_record, idref_record):
    """Test create agent record without viaf links."""
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
    assert m_action.name == 'CREATE'
    assert m_record == {
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'pid': '2',
        'rero': {'$ref': 'https://mef.rero.ch/api/rero/A023655346'},
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
    assert m_action.name == 'CREATE'
    assert m_record == {
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'idref': {'$ref': 'https://mef.rero.ch/api/idref/069774331'},
        'pid': '3',
    }

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

"""Test signals."""

from rero_mef.agents.gnd.api import AgentGndRecord
from rero_mef.mef.api import MefSearch
from rero_mef.viaf.api import ViafRecord


def test_create_mef_from_agent_with_viaf_links(app, viaf_record, gnd_record):
    """Test create MEF record from agent with viaf links."""
    v_record, action = ViafRecord.create_or_update(
        viaf_record, dbcommit=True, reindex=True
    )
    assert action.name == 'CREATE'
    assert v_record['pid'] == '66739143'
    assert v_record['gnd_pid'] == '12391664X'
    assert v_record['rero_pid'] == 'A023655346'
    assert v_record['idref_pid'] == '069774331'

    record, action, m_record, m_action, v_record, online = \
        AgentGndRecord.create_or_update_agent_mef_viaf(
            data=gnd_record,
            dbcommit=True,
            reindex=True,
            online=False
        )
    assert action.name == 'CREATE'
    assert record['pid'] == '12391664X'

    query = MefSearch(). \
        filter('term', gnd__pid='12391664X'). \
        source('sources').scan()
    assert next(query).sources == ['gnd']

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

import mock

from rero_mef.agents.gnd.api import AgentGndRecord
from rero_mef.agents.idref.api import AgentIdrefRecord
from rero_mef.agents.rero.api import AgentReroRecord
from rero_mef.mef.api import MefRecord
from rero_mef.viaf.api import ViafRecord


@mock.patch(
    'rero_mef.viaf.api.ViafRecord.get_online_viaf_record')
def test_create_agent_updates(mock_get, app, gnd_record, rero_record,
                              idref_record):
    """Test create agent record with viaf links."""
    # we have to mock the access to viaf
    mock_get.return_value = {
        'pid': '37268949',
        'idref_pid': '069774331',
        'gnd_pid': '100769527xxx'
    }
    # create first record no viaf and mef records exist
    assert MefRecord.count() == 0
    assert ViafRecord.count() == 0
    record, action, m_record, m_action, v_record, online = \
        AgentIdrefRecord.create_or_update_agent_mef_viaf(
            data=idref_record,
            dbcommit=True,
            reindex=True,
            online=True
        )
    assert action.name == 'CREATE'
    assert record['pid'] == '069774331'
    assert MefRecord.count() == 1
    assert ViafRecord.count() == 1
    assert online

    # we should have a mef and viaf record now
    mef_pid = list(MefRecord.get_all_pids())[-1]
    mef_record = MefRecord.get_record_by_pid(mef_pid)
    assert mef_record.get('pid') == '1'
    assert mef_record.get('viaf_pid') == '37268949'
    assert 'idref' in mef_record
    viaf_pid = list(ViafRecord.get_all_pids())[-1]
    viaf_record = ViafRecord.get_record_by_pid(viaf_pid)
    assert viaf_record.get('pid') == '37268949'
    assert viaf_record.get('idref_pid') == '069774331'

    # we have to mock the access to viaf
    mock_get.return_value = {
        'pid': '66739143',
        'gnd_pid': '12391664X',
        'idref_pid': '068979401',
        'rero_pid': 'A023655346'
    }
    # create second record
    record, action, m_record, m_action, v_record, online = \
        AgentGndRecord.create_or_update_agent_mef_viaf(
            data=gnd_record,
            dbcommit=True,
            reindex=True,
            online=True
        )
    mef_pid = list(MefRecord.get_all_pids())[-1]
    mef_record = MefRecord.get_record_by_pid(mef_pid)
    assert mef_record.get('pid') == '2'
    assert mef_record.get('viaf_pid') == '66739143'
    assert 'gnd' in mef_record
    viaf_pid = list(ViafRecord.get_all_pids())[-1]
    viaf_record = ViafRecord.get_record_by_pid(viaf_pid)
    assert viaf_record.get('pid') == '66739143'
    assert viaf_record.get('gnd_pid') == '12391664X'

    record, action, m_record, m_action, v_record, online = \
        AgentReroRecord.create_or_update_agent_mef_viaf(
            data=rero_record,
            dbcommit=True,
            reindex=True,
            online=True
        )

    mef_pid = list(MefRecord.get_all_pids())[-1]
    mef_record = MefRecord.get_record_by_pid(mef_pid)
    assert mef_record.get('pid') == '2'
    assert mef_record.get('viaf_pid') == '66739143'
    assert 'rero' in mef_record
    viaf_pid = list(ViafRecord.get_all_pids())[-1]
    viaf_record = ViafRecord.get_record_by_pid(viaf_pid)
    assert viaf_record.get('pid') == '66739143'
    assert viaf_record.get('rero_pid') == 'A023655346'

    mef_record = MefRecord.get_mef_by_viaf_pid(viaf_pid)
    assert mef_record == {
        'pid': '2',
        'viaf_pid': '66739143',
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'gnd': {'$ref': 'https://mef.rero.ch/api/gnd/12391664X'},
        'rero': {'$ref': 'https://mef.rero.ch/api/rero/A023655346'}
    }
    new_viaf_pid = 'xxxxxxxx'
    new_viaf_record = {
        'pid': new_viaf_pid,
        'gnd_pid': '12391664X',
        'idref_pid': '069774331',
        'rero_pid': 'A023655346'
    }
    mock_get.return_value = new_viaf_record
    rec, msg = viaf_record.delete(dbcommit=True, delindex=True, online=True)
    assert ViafRecord.get_record_by_pid(new_viaf_pid) == new_viaf_record
    mef_record = MefRecord.get_mef_by_viaf_pid(new_viaf_pid)
    assert mef_record == {
        'viaf_pid': 'xxxxxxxx',
        'gnd': {'$ref': 'https://mef.rero.ch/api/gnd/12391664X'},
        'rero': {'$ref': 'https://mef.rero.ch/api/rero/A023655346'},
        '$schema':
            'https://mef.rero.ch/schemas/mef/mef-v0.0.1.json',
        'pid': '3'
    }

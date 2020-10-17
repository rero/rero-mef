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

"""Test contributions api."""

from rero_mef.contributions.gnd.api import GndRecord
from rero_mef.contributions.idref.api import IdrefRecord
from rero_mef.contributions.rero.api import ReroRecord
from rero_mef.contributions.viaf.api import ViafRecord


def test_create_agent_record_with_viaf_links(
        app, viaf_record, gnd_record, rero_record, idref_record):
    """Test create agent record with viaf links."""
    returned_record, action = ViafRecord.create_or_update(
        viaf_record, dbcommit=True, reindex=True
    )
    ViafRecord.update_indexes()
    assert action.name == 'CREATE'
    assert returned_record['pid'] == '66739143'
    assert returned_record['gnd_pid'] == '12391664X'
    assert returned_record['rero_pid'] == 'A023655346'
    assert returned_record['idref_pid'] == '069774331'

    record, action, m_record, m_action, v_record, online = \
        GndRecord.create_or_update_agent_mef_viaf(
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
            'https://mef.rero.ch/schemas/mef/mef-contribution-v0.0.1.json',
        'gnd': {'$ref': 'https://mef.rero.ch/api/gnd/12391664X'},
        'pid': '1',
        'viaf_pid': '66739143'
    }

    record, action, m_record, m_action, v_record, online = \
        ReroRecord.create_or_update_agent_mef_viaf(
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
            'https://mef.rero.ch/schemas/mef/mef-contribution-v0.0.1.json',
        'gnd': {'$ref': 'https://mef.rero.ch/api/gnd/12391664X'},
        'pid': '1',
        'rero': {'$ref': 'https://mef.rero.ch/api/rero/A023655346'},
        'viaf_pid': '66739143'
    }

    record, action, m_record, m_action, v_record, online = \
        IdrefRecord.create_or_update_agent_mef_viaf(
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
            'https://mef.rero.ch/schemas/mef/mef-contribution-v0.0.1.json',
        'gnd': {'$ref': 'https://mef.rero.ch/api/gnd/12391664X'},
        'idref': {'$ref': 'https://mef.rero.ch/api/idref/069774331'},
        'pid': '1',
        'rero': {'$ref': 'https://mef.rero.ch/api/rero/A023655346'},
        'viaf_pid': '66739143'
    }


def test_update_agent_record_with_viaf_links(
        app, viaf_record, gnd_record, rero_record, idref_record):
    """Test create agent record with viaf links."""
    returned_record, action = GndRecord.create_or_update(
        gnd_record, dbcommit=True, reindex=True
    )
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == '12391664X'

    returned_record, action = ReroRecord.create_or_update(
        rero_record, dbcommit=True, reindex=True
    )
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == 'A023655346'

    returned_record, action = IdrefRecord.create_or_update(
        idref_record, dbcommit=True, reindex=True
    )
    assert action.name == 'UPDATE'
    assert returned_record['pid'] == '069774331'


def test_uptodate_agent_record_with_viaf_links_md5(
        app, viaf_record, gnd_record, rero_record, idref_record):
    """Test create agent record with viaf links."""
    returned_record, action = GndRecord.create_or_update(
        gnd_record, dbcommit=True, reindex=True, test_md5=True
    )
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == '12391664X'

    returned_record, action = ReroRecord.create_or_update(
        rero_record, dbcommit=True, reindex=True, test_md5=True
    )
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == 'A023655346'

    returned_record, action = IdrefRecord.create_or_update(
        idref_record, dbcommit=True, reindex=True,
        test_md5=True
    )
    assert action.name == 'UPTODATE'
    assert returned_record['pid'] == '069774331'

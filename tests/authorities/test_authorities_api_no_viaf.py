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

"""Test authorities api."""

import mock
from invenio_search import current_search

from rero_mef.authorities.gnd.api import GndRecord
from rero_mef.authorities.idref.api import IdrefRecord
from rero_mef.authorities.rero.api import ReroRecord


def update_indexes(agency):
    index = '{agency}-{agency}-person-v0.0.1'.format(
        agency=agency
    )
    current_search.flush_and_refresh(index=index)


@mock.patch('rero_mef.authorities.viaf.api.ViafRecord.get_online_viaf_record')
def test_create_agency_record_no_viaf_links(
        mock_get, app, gnd_record, rero_record, idref_record):
    """Test create agency record without viaf links."""
    mock_get.return_value = {
        'pid': '66739143',
        'gnd_pid': '12391664X',
        'idref_pid': '068979401',
        'rero_pid': 'A023655346'
    }
    returned_record, action, mef_action = GndRecord.create_or_update(
        gnd_record, agency='gnd', dbcommit=True, reindex=True
    )
    update_indexes('gnd')
    update_indexes('mef')
    update_indexes('viaf')
    assert action.name == 'CREATE'
    assert mef_action.name == 'CREATE'
    assert returned_record == gnd_record

    returned_record, action, mef_action = ReroRecord.create_or_update(
        rero_record, agency='rero', dbcommit=True, reindex=True
    )
    update_indexes('rero')
    update_indexes('mef')
    update_indexes('viaf')
    assert action.name == 'CREATE'
    assert mef_action.name == 'UPDATE'
    assert returned_record == rero_record

    mock_get.return_value = {
        'pid': '37268949',
        'idref_pid': '069774331',
        'gnd_pid': '100769527'
    }
    returned_record, action, mef_action = IdrefRecord.create_or_update(
        idref_record, agency='idref', dbcommit=True, reindex=True
    )
    update_indexes('idref')
    update_indexes('mef')
    update_indexes('viaf')
    assert action.name == 'CREATE'
    assert mef_action.name == 'CREATE'
    assert returned_record == idref_record

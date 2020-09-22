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

from invenio_search import current_search

from rero_mef.authorities.gnd.api import GndRecord
# from rero_mef.authorities.mef.api import MefSearch
from rero_mef.authorities.viaf.api import ViafRecord


def update_indexes(agency):
    """Update indexes."""
    index = '{agency}-{agency}-person-v0.0.1'.format(
        agency=agency
    )
    current_search.flush_and_refresh(index=index)


def test_create_mef_from_agency_with_viaf_links(
        app, viaf_record, gnd_record):
    """Test create MEF record from agency with viaf links."""
    returned_record, action, mef_action = ViafRecord.create_or_update(
        viaf_record, agency='viaf', dbcommit=True, reindex=True
    )
    update_indexes('viaf')
    assert action.name == 'CREATE'
    assert returned_record['pid'] == '66739143'
    assert returned_record['gnd_pid'] == '12391664X'
    assert returned_record['rero_pid'] == 'A023655346'
    assert returned_record['idref_pid'] == '069774331'

    returned_record, action, mef_action = GndRecord.create_or_update(
        gnd_record, agency='gnd', dbcommit=True, reindex=True
    )
    # update_indexes('gnd')
    # update_indexes('mef')
    # assert action.name == 'CREATE'
    # assert mef_action.name == 'CREATE'
    # assert returned_record['pid'] == '12391664X'
    #
    # result = MefSearch().filter('term', bnf__pid='12391664X').source().scan()
    # sources = [n['sources'] for n in result]
    # assert sources[0] == ['gnd']

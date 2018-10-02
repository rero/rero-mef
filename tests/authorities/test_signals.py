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

from rero_mef.authorities.api import BnfRecord, GndRecord, MefSearch, \
    ViafRecord


def update_indexes(agency):
    data = {
        'auth': 'authorities-',
        'agency': agency,
        'person': '-person-v0.0.1'
    }
    index = '{auth}{agency}{person}'.format(**data)
    current_search.flush_and_refresh(index=index)


def test_create_mef_from_agency_with_viaf_links(
        app, viaf_record, bnf_record, gnd_record):
    """Test create MEF record from agency with viaf links."""
    returned_record, status = ViafRecord.create_or_update(
        viaf_record, agency='viaf', dbcommit=True, reindex=True
    )
    update_indexes('viaf')
    assert status == 'create'
    assert returned_record['viaf_pid'] == '66739143'
    assert returned_record['bnf_pid'] == '10000690'
    assert returned_record['gnd_pid'] == '12391664X'
    assert returned_record['rero_pid'] == 'A023655346'

    returned_bnf_record, bnf_status = BnfRecord.create_or_update(
        bnf_record, agency='bnf', dbcommit=True, reindex=True
    )
    update_indexes('bnf')
    update_indexes('mef')
    assert bnf_status == 'create'
    assert returned_bnf_record['pid'] == '10000690'

    returned_gnd_record, gnd_status = GndRecord.create_or_update(
        gnd_record, agency='gnd', dbcommit=True, reindex=True
    )
    update_indexes('gnd')
    update_indexes('mef')
    assert gnd_status == 'create'
    assert returned_gnd_record['pid'] == '12391664X'

    key = '{agency}{identifier}'.format(agency='bnf', identifier='.pid')
    result = MefSearch().filter(
        'term', **{key: '10000690'}).source().scan()
    sources = [n['sources'] for n in result]
    assert sources[0] == ['gnd', 'bnf']

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

from invenio_search import current_search

from rero_mef.authorities.bnf.api import BnfRecord
from rero_mef.authorities.gnd.api import GndRecord
from rero_mef.authorities.idref.api import IdrefRecord
from rero_mef.authorities.mef.api import MefRecord
from rero_mef.authorities.rero.api import ReroRecord
from rero_mef.authorities.viaf.api import ViafRecord


def update_indexes(agency):
    index = '{agency}-{agency}-person-v0.0.1'.format(
        agency=agency
    )
    current_search.flush_and_refresh(index=index)


def test_create_viaf_record(app, viaf_record):
    """Test create Viaf record."""
    returned_record, action, mef_action = ViafRecord.create_or_update(
        viaf_record, dbcommit=True, reindex=True
    )
    update_indexes('viaf')
    assert action.name == 'CREATE'
    assert returned_record['pid'] == '66739143'
    assert returned_record['bnf_pid'] == '10000690'
    assert returned_record['gnd_pid'] == '12391664X'
    assert returned_record['rero_pid'] == 'A023655346'
    assert returned_record['idref_pid'] == '069774331'


def test_create_agency_record_with_viaf_links(
        app, viaf_record, bnf_record, gnd_record, rero_record, idref_record):
    """Test create agency record with viaf links."""
    returned_record, action, mef_action = BnfRecord.create_or_update(
        bnf_record, agency='bnf', dbcommit=True, reindex=True
    )
    update_indexes('bnf')
    update_indexes('mef')
    assert action.name == 'CREATE'
    assert mef_action.name == 'CREATE'
    assert returned_record['pid'] == '10000690'

    returned_record, action, mef_action = GndRecord.create_or_update(
        gnd_record, agency='gnd', dbcommit=True, reindex=True
    )
    update_indexes('gnd')
    update_indexes('mef')
    assert action.name == 'CREATE'
    assert mef_action.name == 'UPDATE'
    assert returned_record['pid'] == '12391664X'

    returned_record, action, mef_action = ReroRecord.create_or_update(
        rero_record, agency='rero', dbcommit=True, reindex=True
    )
    update_indexes('rero')
    update_indexes('mef')
    assert action.name == 'CREATE'
    assert mef_action.name == 'UPDATE'
    assert returned_record['pid'] == 'A023655346'

    returned_record, action, mef_action = IdrefRecord.create_or_update(
        idref_record, agency='idref', dbcommit=True, reindex=True
    )
    update_indexes('idref')
    update_indexes('mef')
    assert action.name == 'CREATE'
    assert mef_action.name == 'UPDATE'
    assert returned_record['pid'] == '069774331'


def test_update_agency_record_with_viaf_links(
        app, viaf_record, bnf_record, gnd_record, rero_record, idref_record):
    """Test create agency record with viaf links."""
    returned_record, action, mef_action = BnfRecord.create_or_update(
        bnf_record, agency='bnf', dbcommit=True, reindex=True
    )
    update_indexes('bnf')
    update_indexes('mef')
    assert action.name == 'UPDATE'
    assert mef_action.name == 'UPDATE'
    assert returned_record['pid'] == '10000690'

    returned_record, action, mef_action = GndRecord.create_or_update(
        gnd_record, agency='gnd', dbcommit=True, reindex=True
    )
    update_indexes('gnd')
    update_indexes('mef')
    assert action.name == 'UPDATE'
    assert mef_action.name == 'UPDATE'
    assert returned_record['pid'] == '12391664X'

    returned_record, action, mef_action = ReroRecord.create_or_update(
        rero_record, agency='rero', dbcommit=True, reindex=True
    )
    update_indexes('rero')
    update_indexes('mef')
    assert action.name == 'UPDATE'
    assert mef_action.name == 'UPDATE'
    assert returned_record['pid'] == 'A023655346'

    returned_record, action, mef_action = IdrefRecord.create_or_update(
        idref_record, agency='idref', dbcommit=True, reindex=True
    )
    update_indexes('idref')
    update_indexes('mef')
    assert action.name == 'UPDATE'
    assert mef_action.name == 'UPDATE'
    assert returned_record['pid'] == '069774331'


def test_uptodate_agency_record_with_viaf_links_md5(
        app, viaf_record, bnf_record, gnd_record, rero_record, idref_record):
    """Test create agency record with viaf links."""
    returned_record, action, mef_action = BnfRecord.create_or_update(
        bnf_record, agency='bnf', dbcommit=True, reindex=True, test_md5=True
    )
    assert action.name == 'UPTODATE'
    assert mef_action.name == 'UPTODATE'
    assert returned_record['pid'] == '10000690'

    returned_record, action, mef_action = GndRecord.create_or_update(
        gnd_record, agency='gnd', dbcommit=True, reindex=True, test_md5=True
    )
    assert action.name == 'UPTODATE'
    assert mef_action.name == 'UPTODATE'
    assert returned_record['pid'] == '12391664X'

    returned_record, action, mef_action = ReroRecord.create_or_update(
        rero_record, agency='rero', dbcommit=True, reindex=True, test_md5=True
    )
    assert action.name == 'UPTODATE'
    assert mef_action.name == 'UPTODATE'
    assert returned_record['pid'] == 'A023655346'

    returned_record, action, mef_action = IdrefRecord.create_or_update(
        idref_record, agency='idref', dbcommit=True, reindex=True,
        test_md5=True
    )
    assert action.name == 'UPTODATE'
    assert mef_action.name == 'UPTODATE'
    assert returned_record['pid'] == '069774331'


def test_mef_record(app, viaf_record):
    """Test MEF record."""
    viaf_pid = viaf_record['pid']
    mef_rec = MefRecord.get_mef_by_viaf_pid(viaf_pid=viaf_pid)
    assert mef_rec.get('bnf')
    assert mef_rec.get('gnd')
    assert mef_rec.get('rero')
    assert mef_rec.get('idref')

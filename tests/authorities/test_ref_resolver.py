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

"""Test ref resolver."""

from invenio_search import current_search

from rero_mef.authorities.api import BnfRecord, GndRecord, MefRecord, \
    ReroRecord, ViafRecord


def test_ref_resolvers(
        app, bnf_record, gnd_record, rero_record, viaf_record):
    """Test ref resolvers."""

    """VIAF record."""
    viaf_rec, status = ViafRecord.create_or_update(
        viaf_record, agency='viaf', dbcommit=True, reindex=True
    )
    viaf_pid = viaf_rec['pid']
    current_search.flush_and_refresh(
        index='authorities-viaf-person-v0.0.1')
    current_search.flush_and_refresh(
        index='authorities-mef-person-v0.0.1')

    """BNF record."""
    bnf_rec, status = BnfRecord.create_or_update(
        bnf_record, agency='bnf', dbcommit=True, reindex=True
    )
    current_search.flush_and_refresh(
        index='authorities-bnf-person-v0.0.1')
    current_search.flush_and_refresh(
        index='authorities-mef-person-v0.0.1')
    bnf_pid = bnf_rec['pid']

    """GND record."""
    gnd_rec, status = GndRecord.create_or_update(
        gnd_record, agency='gnd', dbcommit=True, reindex=True
    )
    current_search.flush_and_refresh(
        index='authorities-gnd-person-v0.0.1')
    current_search.flush_and_refresh(
        index='authorities-mef-person-v0.0.1')
    gnd_pid = gnd_rec.get('pid')

    """RERO record."""
    rero_rec, status = ReroRecord.create_or_update(
        rero_record, agency='rero', dbcommit=True, reindex=True
    )
    current_search.flush_and_refresh(
        index='authorities-rero-person-v0.0.1')
    rero_pid = rero_rec.get('pid')
    current_search.flush_and_refresh(
        index='authorities-mef-person-v0.0.1')

    """MEF record."""
    mef_rec_resolved = MefRecord.get_mef_by_viaf_pid(
        viaf_pid=viaf_pid
    )
    mef_rec_resolved = mef_rec_resolved.replace_refs()
    assert mef_rec_resolved.get('bnf').get('pid') == bnf_pid
    assert mef_rec_resolved.get('gnd').get('pid') == gnd_pid
    assert mef_rec_resolved.get('rero').get('pid') == rero_pid

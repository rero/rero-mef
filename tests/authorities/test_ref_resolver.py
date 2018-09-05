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

from rero_mef.authorities.api import BnfRecord, GndRecord, MefRecord, \
    ReroRecord


def test_ref_resolvers(db, mef_record, bnf_record, gnd_record, rero_record):
    """Test ref resolvers."""
    mef_rec = MefRecord.create(mef_record)
    bnf_rec = BnfRecord.create(bnf_record)
    bnf_ifp = bnf_rec.get('identifier_for_person')
    gnd_rec = GndRecord.create(gnd_record)
    gnd_ifp = gnd_rec.get('identifier_for_person')
    rero_rec = ReroRecord.create(rero_record)
    rero_ifp = rero_rec.get('identifier_for_person')
    mef_rec_resolved = mef_rec.replace_refs()
    assert mef_rec_resolved.get('bnf').get('identifier_for_person') == bnf_ifp
    assert mef_rec_resolved.get('gnd').get('identifier_for_person') == gnd_ifp
    assert mef_rec_resolved.get('rero').get(
        'identifier_for_person'
    ) == rero_ifp

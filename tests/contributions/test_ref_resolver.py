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

from rero_mef.contributions.gnd.api import GndRecord
from rero_mef.contributions.idref.api import IdrefRecord
from rero_mef.contributions.mef.api import MefRecord
from rero_mef.contributions.rero.api import ReroRecord
from rero_mef.contributions.viaf.api import ViafRecord


def test_ref_resolvers(
        app, gnd_record, rero_record, viaf_record, idref_record):
    """Test ref resolvers."""

    # VIAF record
    record, action = ViafRecord.create_or_update(
        data=viaf_record,
        dbcommit=True,
        reindex=True
    )
    viaf_pid = record['pid']

    # GND record
    record, action, m_record, m_action, v_record, online = \
        GndRecord.create_or_update_agent_mef_viaf(
            data=gnd_record,
            dbcommit=True,
            reindex=True,
            online=False
        )
    gnd_pid = record.get('pid')

    # RERO record
    record, action, m_record, m_action, v_record, online = \
        ReroRecord.create_or_update_agent_mef_viaf(
            data=rero_record,
            dbcommit=True,
            reindex=True,
            online=False
        )
    rero_pid = record.get('pid')

    # IDREF record
    record, action, m_record, m_action, v_record, online = \
        IdrefRecord.create_or_update_agent_mef_viaf(
            data=idref_record,
            dbcommit=True,
            reindex=True,
            online=False
        )
    idref_pid = record.get('pid')

    # MEF record
    mef_rec_resolved = MefRecord.get_mef_by_viaf_pid(
        viaf_pid=viaf_pid
    )
    mef_rec_resolved = mef_rec_resolved.replace_refs()
    assert mef_rec_resolved.get('gnd').get('pid') == gnd_pid
    assert mef_rec_resolved.get('rero').get('pid') == rero_pid
    assert mef_rec_resolved.get('idref').get('pid') == idref_pid

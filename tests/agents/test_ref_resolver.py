# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2020 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Test ref resolver."""

from rero_mef.agents.gnd.api import AgentGndRecord
from rero_mef.agents.idref.api import AgentIdrefRecord
from rero_mef.agents.rero.api import AgentReroRecord
from rero_mef.mef.api import MefRecord
from rero_mef.viaf.api import ViafRecord


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
        AgentGndRecord.create_or_update_agent_mef_viaf(
            data=gnd_record,
            dbcommit=True,
            reindex=True,
            online=False
        )
    gnd_pid = record.get('pid')

    # RERO record
    record, action, m_record, m_action, v_record, online = \
        AgentReroRecord.create_or_update_agent_mef_viaf(
            data=rero_record,
            dbcommit=True,
            reindex=True,
            online=False
        )
    rero_pid = record.get('pid')

    # IDREF record
    record, action, m_record, m_action, v_record, online = \
        AgentIdrefRecord.create_or_update_agent_mef_viaf(
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

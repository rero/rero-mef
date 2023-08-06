# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2021 RERO
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

"""Test api."""

from rero_mef.agents import AgentGndRecord
from rero_mef.api import Action
from rero_mef.concepts import ConceptIdrefRecord


def test_mef_minter(app, agent_gnd_data, concept_idref_data):
    """Test Mef minter."""
    aggnd_rec = AgentGndRecord.create(data=agent_gnd_data, dbcommit=True,
                                      reindex=True)
    assert aggnd_rec.pid == agent_gnd_data.get('pid')
    mef_aggnd_rec, action = aggnd_rec.create_or_update_mef(dbcommit=True,
                                                           reindex=True)
    assert action == {'1': Action.CREATE}
    assert mef_aggnd_rec.pid == '1'
    assert mef_aggnd_rec.get('gnd')

    cidref_rec = ConceptIdrefRecord.create(data=concept_idref_data,
                                           dbcommit=True, reindex=True)
    assert cidref_rec.pid == concept_idref_data.get('pid')
    mef_cidref_rec, action = cidref_rec.create_or_update_mef(dbcommit=True,
                                                             reindex=True)
    assert action == {'2': Action.CREATE}
    assert mef_cidref_rec.pid == '2'
    assert mef_cidref_rec.get('idref')

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

"""Test agents MEF api."""

from rero_mef.agents.mef.api import AgentMefRecord


def test_get_all_pids_without_agents_and_viaf(app):
    """Test get all pids without agents and VIAF."""
    record = {
        "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json"
    }
    m_record = AgentMefRecord.create(
        data=record, dbcommit=True, reindex=True)
    AgentMefRecord.flush_indexes()
    assert list(AgentMefRecord.get_all_pids_without_agents_and_viaf()) == \
        [m_record.pid]


def test_get_pids_with_multiple_mef(app, agent_mef_record):
    """Test get pids with multiple MEF."""
    m_record_1 = AgentMefRecord.create(
        data=agent_mef_record, delete_pid=True, dbcommit=True, reindex=True)
    m_record_2 = AgentMefRecord.create(
        data=agent_mef_record, delete_pid=True, dbcommit=True, reindex=True)
    AgentMefRecord.flush_indexes()
    pids, multiple_pids, missing_pids = AgentMefRecord \
        .get_pids_with_multiple_mef(record_types=['aidref', 'aggnd', 'agrero'])
    assert pids == {'aggnd': {}, 'agrero': {}, 'aidref': {}}
    assert multiple_pids == {
        'aggnd': {'12391664X': [m_record_1.pid, m_record_2.pid]},
        'agrero': {'A023655346': [m_record_1.pid, m_record_2.pid]},
        'aidref': {'069774331': [m_record_1.pid, m_record_2.pid]}
    }
    assert missing_pids == {'aggnd': [], 'agrero': [], 'aidref': []}

    m_record_2.mark_as_deleted(dbcommit=True, reindex=True)
    assert m_record_2.deleted is not None


# TODO: Find out why this test is not working in github.
# def test_get_all_missing_pids(app, agent_gnd_record, agent_rero_record,
#                               agent_idref_record):
#     """Test get all missing pids."""
#     for mef_record in AgentMefRecord.get_all_records():
#         mef_record.delete(dbcommit=True, delindex=True)
#     AgentGndRecord.create(
#         data=agent_gnd_record, dbcommit=True, reindex=True)
#     AgentGndRecord.flush_indexes()
#     AgentIdrefRecord.create(
#         data=agent_idref_record, dbcommit=True, reindex=True)
#     AgentIdrefRecord.flush_indexes()
#     AgentReroRecord.create(
#         data=agent_rero_record, dbcommit=True, reindex=True)
#     AgentReroRecord.flush_indexes()
#     missing_pids, to_much_pids = AgentMefRecord.get_all_missing_pids(
#         record_types=['aidref', 'aggnd', 'agrero'])
#     assert missing_pids == {
#         'aggnd': {'12391664X': 1},
#         'agrero': {'A023655346': 1},
#         'aidref': {'069774331': 1}
#     }
#     assert to_much_pids == {}

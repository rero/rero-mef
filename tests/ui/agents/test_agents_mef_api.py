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

from utils import create_record

from rero_mef.agents import AgentMefRecord


def test_get_all_pids_without_agents_and_viaf(app):
    """Test get all pids without agents and VIAF."""
    record = {
        "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json"
    }
    m_record = create_record(AgentMefRecord, record)
    assert list(AgentMefRecord.get_all_pids_without_agents_and_viaf()) == \
        [m_record.pid]


def test_get_multiple_missing_pids(app, agent_mef_data, agent_viaf_record):
    """Test get pids with multiple MEF."""
    m_record_1 = create_record(AgentMefRecord, agent_mef_data, delete_pid=True)
    m_record_2 = create_record(AgentMefRecord, agent_mef_data, delete_pid=True)
    pids, multiple_pids, missing_pids, none_pids = AgentMefRecord \
        .get_multiple_missing_pids(
            record_types=['aidref', 'aggnd', 'agrero'])
    assert pids == {'aggnd': {}, 'agrero': {}, 'aidref': {}}
    assert multiple_pids == {
        'aggnd': {'12391664X': [m_record_2.pid, m_record_1.pid]},
        'agrero': {'A023655346': [m_record_2.pid, m_record_1.pid]},
        'aidref': {'069774331': [m_record_2.pid, m_record_1.pid]}
    }
    assert missing_pids == {'aggnd': [], 'agrero': [], 'aidref': []}
    assert none_pids == {'aggnd': [], 'agrero': [], 'aidref': []}

    m_record_2.mark_as_deleted(dbcommit=True, reindex=True)
    assert m_record_2.deleted is not None

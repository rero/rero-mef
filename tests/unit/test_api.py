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

from rero_mef.agents.idref.api import AgentIdrefIndexer, AgentIdrefRecord
from rero_mef.api import Action
from rero_mef.tasks import process_bulk_queue


def test_reromefrecord_api(app, agent_idref_record):
    """Test ReroMefRecord api."""

    idref = AgentIdrefRecord.create(
        data=agent_idref_record,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AgentIdrefRecord.update_indexes()

    assert AgentIdrefRecord.count() == 1
    assert AgentIdrefRecord.index_all() == 1

    assert len(list(AgentIdrefRecord.get_all_records())) == len(list(
        AgentIdrefRecord.get_all_records(limit=0)))

    assert AgentIdrefRecord.get_metadata_identifier_names() == (
        'agent_idref_metadata', 'agent_idref_id')

    count = 0
    for _ in AgentIdrefRecord.get_all_records():
        count += 1
    assert count == 1

    _, agent_action = idref.update_test_md5(
        data=idref, dbcommit=True, reindex=True)
    assert agent_action == Action.UPTODATE

    idref['gender'] = 'female'
    _, agent_action = idref.update_test_md5(
        data=idref, dbcommit=True, reindex=True)
    assert agent_action == Action.UPDATE

    assert AgentIdrefRecord.get_pid_by_id(idref.id) == idref.pid

    AgentIdrefIndexer().bulk_index(list(AgentIdrefRecord.get_all_ids()))
    process_bulk_queue(stats_only=True)
    # TODO: Find out how to test bulk indexing.
    # assert process_bulk_queue(stats_only=True) == (1, 0)
# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test api."""

from rero_mef.agents import (
    AgentIdrefIndexer,
    AgentIdrefRecord,
    AgentMefRecord,
    AgentMefSearch,
)
from rero_mef.api import Action
from rero_mef.tasks import process_bulk_queue


def test_entityrecord_api(app, agent_idref_record):
    """Test EntityRecord api."""
    idref = agent_idref_record
    assert AgentIdrefRecord.count() == 1
    assert AgentIdrefRecord.index_all() == 1

    assert AgentIdrefRecord.get_metadata_identifier_names() == (
        "agent_idref_metadata",
        "agent_idref_id",
    )

    count = sum(1 for _ in AgentIdrefRecord.get_all_records())
    assert count == 1

    _, agent_action = AgentIdrefRecord.create_or_update(
        data=dict(idref), dbcommit=True, reindex=True, test_md5=True
    )
    assert agent_action == Action.UPTODATE

    mef_record, _ = idref.create_or_update_mef(dbcommit=True, reindex=True)

    idref["gender"] = "female"
    _, agent_action = AgentIdrefRecord.create_or_update(
        data=dict(idref), dbcommit=True, reindex=True, test_md5=True
    )
    assert agent_action == Action.REPLACE
    AgentMefRecord.flush_indexes()
    mef_es = next(AgentMefSearch().filter("term", pid=mef_record.pid).scan()).to_dict()
    assert mef_es.get("idref").get("gender") == "female"

    assert AgentIdrefRecord.get_pid_by_id(idref.id) == idref.pid

    AgentIdrefIndexer().bulk_index(list(AgentIdrefRecord.get_all_ids()))
    indexed, failed = process_bulk_queue(stats_only=True)
    assert indexed >= 1
    assert failed == 0

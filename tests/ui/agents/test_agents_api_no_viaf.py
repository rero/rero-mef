# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test agents api."""

from rero_mef.agents import Action, AgentGndRecord, AgentIdrefRecord, AgentReroRecord


def test_create_agent_record_no_viaf_links(
    app, agent_gnd_data, agent_rero_data, agent_idref_data
):
    """Test create agent record without VIAF links."""
    gnd_record, action = AgentGndRecord.create_or_update(
        data=agent_gnd_data, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert gnd_record["pid"] == "12391664X"

    m_record, m_actions = gnd_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.CREATE}
    assert "md5" in m_record
    assert {k: v for k, v in m_record.items() if k != "md5"} == {
        "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json",
        "gnd": {"$ref": "https://mef.rero.ch/api/agents/gnd/12391664X"},
        "pid": "1",
        "type": "bf:Person",
    }

    rero_record, action = AgentReroRecord.create_or_update(
        data=agent_rero_data, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert rero_record["pid"] == "A023655346"

    m_record, m_actions = rero_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.CREATE}
    assert "md5" in m_record
    assert {k: v for k, v in m_record.items() if k != "md5"} == {
        "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json",
        "pid": "2",
        "rero": {"$ref": "https://mef.rero.ch/api/agents/rero/A023655346"},
        "type": "bf:Person",
    }

    idref_record, action = AgentIdrefRecord.create_or_update(
        data=agent_idref_data, dbcommit=True, reindex=True
    )
    assert action == Action.CREATE
    assert idref_record["pid"] == "069774331"

    m_record, m_actions = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    assert m_actions == {m_record.pid: Action.CREATE}
    assert "md5" in m_record
    assert {k: v for k, v in m_record.items() if k != "md5"} == {
        "$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json",
        "idref": {"$ref": "https://mef.rero.ch/api/agents/idref/069774331"},
        "pid": "3",
        "type": "bf:Person",
    }

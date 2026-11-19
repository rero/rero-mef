# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test agents MEF api."""

from rero_mef.agents import AgentMefRecord

from ...utils import create_record


def test_get_all_pids_without_entities_and_viaf(app):
    """Test get all pids without agents and VIAF."""
    record = {"$schema": "https://mef.rero.ch/schemas/mef/mef-v0.0.1.json"}
    m_record = create_record(AgentMefRecord, record)
    assert list(AgentMefRecord.get_all_pids_without_entities_and_viaf()) == [m_record.pid]


def test_get_multiple_missing_pids(app, agent_mef_data, agent_viaf_record):
    """Test get pids with multiple MEF."""
    m_record_1 = create_record(AgentMefRecord, agent_mef_data, delete_pid=True)
    assert m_record_1["type"] == "bf:Person"
    m_record_2 = create_record(AgentMefRecord, agent_mef_data, delete_pid=True)
    assert m_record_2["type"] == "bf:Person"
    (
        pids,
        multiple_pids,
        missing_pids,
        none_pids,
    ) = AgentMefRecord.get_multiple_missing_pids(record_types=["aidref", "aggnd", "agrero"])
    mef_pids = sorted([m_record_1.pid, m_record_2.pid])
    assert pids == {"aggnd": {}, "agrero": {}, "aidref": {}}
    assert multiple_pids == {
        "aggnd": {"12391664X": mef_pids},
        "agrero": {"A023655346": mef_pids},
        "aidref": {"069774331": mef_pids},
    }
    assert missing_pids == {"aggnd": [], "agrero": [], "aidref": []}
    assert none_pids == {"aggnd": [], "agrero": [], "aidref": []}

    # one type reads only the MEF records holding it, with the same result
    assert AgentMefRecord.get_multiple_missing_pids(record_types=["aidref"]) == (
        {"aidref": {}},
        {"aidref": {"069774331": mef_pids}},
        {"aidref": []},
        {"aidref": []},
    )
    assert AgentMefRecord.get_multiple_missing_pids() == ({}, {}, {}, {})

# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test that one VIAF cluster ends up in one agent MEF record."""

from rero_mef.agents import Action, AgentGndRecord, AgentMefRecord
from rero_mef.utils import build_ref_string


def make_ref(record):
    """Reference to an agent record."""
    return {"$ref": build_ref_string(entity_type="agents", entity_name=record.name, entity_pid=record.pid)}


def create_mef(record, viaf_pid):
    """Create a MEF record holding only *record*, linked to the VIAF cluster *viaf_pid*."""
    mef = AgentMefRecord.create(data={record.name: make_ref(record), "viaf_pid": viaf_pid}, dbcommit=True, reindex=True)
    AgentMefRecord.flush_indexes()
    return mef.pid


def test_create_or_update_mef_merges_split_cluster(app, agent_viaf_record, agent_idref_record, agent_rero_record):
    """A source update brings a VIAF cluster spread over two MEF records back together.

    Production had such pairs: each record held one source of the cluster and both carried its VIAF pid, because
    an update only moved its own source and left the other sources and the VIAF pid in the second record.
    """
    viaf_pid = agent_viaf_record.pid
    split = [create_mef(agent_idref_record, viaf_pid), create_mef(agent_rero_record, viaf_pid)]
    assert sorted(AgentMefRecord.get_mef(viaf_pid, "viaf", pid_only=True)) == sorted(split)

    mef_record, actions = agent_idref_record.create_or_update_mef(dbcommit=True, reindex=True)

    assert AgentMefRecord.get_mef(viaf_pid, "viaf", pid_only=True) == [mef_record.pid]
    assert mef_record["idref"]["$ref"].endswith(f"/{agent_idref_record.pid}")
    assert mef_record["rero"]["$ref"].endswith(f"/{agent_rero_record.pid}")
    emptied = next(pid for pid in split if pid != mef_record.pid)
    assert actions[emptied] == Action.DELETE
    assert AgentMefRecord.get_record_by_pid(emptied) is None
    assert AgentMefRecord.get_mef(agent_rero_record.pid, agent_rero_record.name, pid_only=True) == [mef_record.pid]


def test_create_or_update_mef_keeps_sources_of_other_clusters(
    app, agent_viaf_record, agent_idref_record, agent_gnd_record
):
    """A source that the cluster does not list stays in its record, which only loses the VIAF pid."""
    viaf_pid = agent_viaf_record.pid
    # A GND agent of another identity, wrongly linked to the cluster.
    stranger = agent_gnd_record.__class__.create(
        data={**agent_gnd_record, "pid": "STRANGER"}, dbcommit=True, reindex=True
    )
    stranger_mef = create_mef(stranger, viaf_pid)
    # The record of the cluster is the most recently updated one, the record kept.
    kept = AgentMefRecord.get_mef(agent_idref_record.pid, agent_idref_record.name)[0]
    kept.update(data=kept, dbcommit=True, reindex=True)
    AgentMefRecord.flush_indexes()

    mef_record, actions = agent_idref_record.create_or_update_mef(dbcommit=True, reindex=True)

    assert mef_record.pid == kept.pid
    assert AgentMefRecord.get_mef(viaf_pid, "viaf", pid_only=True) == [kept.pid]
    other = AgentMefRecord.get_record_by_pid(stranger_mef)
    assert other["gnd"]["$ref"].endswith("/STRANGER")
    assert "viaf_pid" not in other
    assert actions[stranger_mef] == Action.DISCARD


def test_create_or_update_mef_moves_cluster_reference_into_occupied_slot(
    app, agent_viaf_record, agent_idref_record, agent_gnd_record
):
    """A cluster-listed reference takes a source slot the kept record already holds, the agent it displaces gets its own record.

    The duplicate keeps no VIAF pid once emptied, so its cluster-listed reference must not be left behind in it.
    """
    viaf_pid = agent_viaf_record.pid
    displaced = AgentGndRecord.create(data={**agent_gnd_record, "pid": "GND_OTHER"}, dbcommit=True, reindex=True)
    duplicate = create_mef(agent_gnd_record, viaf_pid)
    # the record of the cluster, as the previous test leaves it, takes the other GND agent in its GND slot and is
    # the most recently updated one, the record kept
    kept = AgentMefRecord.get_mef(agent_idref_record.pid, agent_idref_record.name)[0]
    kept[displaced.name] = make_ref(displaced)
    kept.update(data=kept, dbcommit=True, reindex=True)
    AgentMefRecord.flush_indexes()

    mef_record, actions = agent_idref_record.create_or_update_mef(dbcommit=True, reindex=True)

    assert mef_record.pid == kept.pid
    assert mef_record["gnd"]["$ref"].endswith(f"/{agent_gnd_record.pid}")
    assert AgentMefRecord.get_mef(viaf_pid, "viaf", pid_only=True) == [kept.pid]
    assert actions[duplicate] == Action.DELETE
    assert AgentMefRecord.get_record_by_pid(duplicate) is None
    own = AgentMefRecord.get_mef(displaced.pid, displaced.name, pid_only=True)
    assert len(own) == 1
    assert "viaf_pid" not in AgentMefRecord.get_record_by_pid(own[0])

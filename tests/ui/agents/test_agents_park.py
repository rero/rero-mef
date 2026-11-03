# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the MEF record of a deleted, redirected agent."""

from copy import deepcopy
from unittest import mock

from rero_mef.agents import AgentGndRecord, AgentIdrefRecord, AgentMefRecord


def test_deleted_redirected_gnd_agent_gets_its_own_mef_record(app, agent_gnd_data, agent_idref_data):
    """A GND agent deleted with a redirect moves to its own MEF record, without VIAF link; the rest stays live."""
    target, _ = AgentGndRecord.create_or_update(
        data=deepcopy(agent_gnd_data) | {"pid": "8000002"}, dbcommit=True, reindex=True
    )
    old_data = deepcopy(agent_gnd_data) | {"pid": "8000001"}
    old, _ = AgentGndRecord.create_or_update(data=old_data, dbcommit=True, reindex=True)
    idref, _ = AgentIdrefRecord.create_or_update(
        data=deepcopy(agent_idref_data) | {"pid": "8000003"}, dbcommit=True, reindex=True
    )
    target_mef = AgentMefRecord.create(
        data={"gnd": {"$ref": f"https://mef.rero.ch/api/agents/gnd/{target.pid}"}}, dbcommit=True, reindex=True
    )
    shared_mef = AgentMefRecord.create(
        data={
            "gnd": {"$ref": f"https://mef.rero.ch/api/agents/gnd/{old.pid}"},
            "idref": {"$ref": f"https://mef.rero.ch/api/agents/idref/{idref.pid}"},
            "viaf_pid": "8000009",
        },
        dbcommit=True,
        reindex=True,
    )
    AgentMefRecord.flush_indexes()

    # deleted and redirected
    old, _ = AgentGndRecord.create_or_update(
        data=old_data
        | {"deleted": "2026-10-20T00:00:00+00:00", "relation_pid": {"type": "redirect_to", "value": target.pid}},
        dbcommit=True,
        reindex=True,
    )
    own_mef, _ = old.create_or_update_mef(dbcommit=True, reindex=True)

    shared_mef = AgentMefRecord.get_record_by_pid(shared_mef.pid)
    assert shared_mef.ref_pids == {"idref": idref.pid}
    assert shared_mef["viaf_pid"] == "8000009"
    assert not shared_mef.get("deleted")
    assert own_mef.ref_pids == {"gnd": old.pid}
    assert own_mef.get("deleted")
    assert not own_mef.get("viaf_pid")
    assert AgentMefRecord.get_latest(pid_type="gnd", pid=old.pid)["pid"] == target_mef.pid


def test_deleted_agent_redirected_out_of_its_type_keeps_resolving(app, agent_gnd_data):
    """A GND agent redirected to a pid no agent record holds resolves to its own deleted MEF record."""
    old_data = deepcopy(agent_gnd_data) | {"pid": "8000011"}
    AgentGndRecord.create_or_update(data=old_data, dbcommit=True, reindex=True)
    old, _ = AgentGndRecord.create_or_update(
        data=old_data
        | {"deleted": "2026-10-20T00:00:00+00:00", "relation_pid": {"type": "redirect_to", "value": "1416410082"}},
        dbcommit=True,
        reindex=True,
    )
    own_mef, _ = old.create_or_update_mef(dbcommit=True, reindex=True)

    with mock.patch.object(app.logger, "warning") as warning:
        latest = AgentMefRecord.get_latest(pid_type="gnd", pid=old.pid)
    assert latest["pid"] == own_mef.pid
    assert latest.get("deleted")
    warning.assert_called_once_with(
        f"REDIRECT OUT OF TYPE: AgentMefRecord gnd {old.pid} -> 1416410082 | mef: {own_mef.pid}"
    )

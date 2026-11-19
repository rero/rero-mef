# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test monitoring."""

import pytest
from click.testing import CliRunner
from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from rero_mef.agents.idref.api import AgentIdrefRecord
from rero_mef.cli import reindex_missing
from rero_mef.monitoring.api import Monitoring
from rero_mef.monitoring.cli import dangling_pids_cli, dangling_redirects_cli, mef_counts_cli


def test_monitoring(app, agent_idref_data):
    """The shared monitoring compares the database and the index of every MEF record type."""
    idref = AgentIdrefRecord.create(data=agent_idref_data, delete_pid=False, dbcommit=True, reindex=False)
    mon = Monitoring(time_delta=0)
    info = mon.info()
    assert sorted(info) == [
        "aggnd",
        "agrero",
        "aidref",
        "cidref",
        "cognd",
        "comef",
        "corero",
        "mef",
        "pidref",
        "plgnd",
        "plmef",
        "viaf",
    ]
    assert info["aidref"] == {"index": "agents_idref", "db": 1, "search": 0, "db-search": 1}
    assert mon.check() == {"aidref": {"db-search": 1}}
    assert mon.missing("aidref") == {"DB": [], "search": ["069774331"], "search duplicate": []}
    idref.delete(force=True, dbcommit=True)


def test_reindex_missing(app, agent_idref_data, script_info):
    """The records missing in the index are reindexed, verbose or not."""
    pid = AgentIdrefRecord.create(data=agent_idref_data, delete_pid=False, dbcommit=True, reindex=False).pid

    res = CliRunner().invoke(reindex_missing, ["-e", "aidref", "-d", "0"], obj=script_info)
    assert res.exit_code == 0
    AgentIdrefRecord.flush_indexes()
    assert Monitoring(time_delta=0).missing("aidref") == {"DB": [], "search": [], "search duplicate": []}
    # the session of the record is lost after the CliRunner
    AgentIdrefRecord.get_record_by_pid(pid).delete(force=True, dbcommit=True, delindex=True)
    AgentIdrefRecord.flush_indexes()


def test_monitoring_check_mef(app):
    """check_mef returns a dict with entity-level MEF vs DB counts."""
    mon = Monitoring(time_delta=0)
    result = mon.check_mef()
    assert isinstance(result, dict)


def test_monitoring_cli_mef_counts(app, script_info):
    """mef_counts_cli prints the MEF/DB comparison table."""
    runner = CliRunner()
    res = runner.invoke(mef_counts_cli, ["-d", "0"], obj=script_info)
    assert res.exit_code == 0
    assert "MEF" in res.output


def test_monitoring_dangling_pids(app, agent_idref_data, script_info):
    """A pid whose record row is gone is reported, and deleted on request."""
    idref = AgentIdrefRecord.create(data=agent_idref_data, delete_pid=False, dbcommit=True, reindex=False)
    pid = idref.pid
    assert Monitoring.get_dangling_pids("aidref") == []

    # Strand the pid the way a refused record used to: drop the record row, keep the pid.
    db.session.delete(idref.model)
    db.session.commit()
    assert Monitoring.get_dangling_pids("aidref") == [pid]

    runner = CliRunner()
    res = runner.invoke(dangling_pids_cli, [], obj=script_info)
    assert res.exit_code == 0
    assert f"aidref      1 found: {pid}" in res.output
    assert Monitoring.get_dangling_pids("aidref") == [pid]

    res = runner.invoke(dangling_pids_cli, ["--delete"], obj=script_info)
    assert res.exit_code == 0
    assert f"aidref      1 deleted: {pid}" in res.output
    assert Monitoring.get_dangling_pids("aidref") == []
    with pytest.raises(PIDDoesNotExistError):
        PersistentIdentifier.get("aidref", pid)


def test_monitoring_dangling_pids_ignores_a_deleted_record(app, agent_idref_data):
    """A deleted record keeps its row, so its pid is not dangling."""
    idref = AgentIdrefRecord.create(data=agent_idref_data, delete_pid=False, dbcommit=True, reindex=False)
    idref.delete(force=False, dbcommit=True, delindex=False)
    assert Monitoring.get_dangling_pids("aidref") == []


def test_a_deleted_pid_is_not_dangling(app, agent_idref_data):
    """The tombstone of a record that went is not a leftover, whatever holds no row for it."""
    PersistentIdentifier.create("aidref", "099999996", status=PIDStatus.DELETED)
    db.session.commit()

    assert "099999996" not in Monitoring.get_dangling_pids("aidref")
    assert "099999996" not in Monitoring.remove_dangling_pids("aidref")
    assert PersistentIdentifier.get("aidref", "099999996").status == PIDStatus.DELETED


def test_dangling_redirects(app, agent_idref_data, script_info):
    """Only a `redirect_to` whose target is missing is reported."""
    live = dict(agent_idref_data) | {"pid": "099999881"}
    AgentIdrefRecord.create_or_update(data=live, dbcommit=True, reindex=True)

    # points at a pid nothing holds
    broken = dict(agent_idref_data) | {
        "pid": "099999882",
        "relation_pid": {"type": "redirect_to", "value": "099999999"},
    }
    AgentIdrefRecord.create_or_update(data=broken, dbcommit=True, reindex=True)

    # points at the record above, which is held
    good = dict(agent_idref_data) | {
        "pid": "099999883",
        "relation_pid": {"type": "redirect_to", "value": "099999881"},
    }
    AgentIdrefRecord.create_or_update(data=good, dbcommit=True, reindex=True)

    # IdRef's own relation: the value is the superseded pid, never expected to be held
    superseded = dict(agent_idref_data) | {
        "pid": "099999884",
        "relation_pid": {"type": "redirect_from", "value": "099999998"},
    }
    AgentIdrefRecord.create_or_update(data=superseded, dbcommit=True, reindex=True)

    # points at a pid nothing but the pidstore holds: the forward answers with nothing either
    PersistentIdentifier.create("aidref", "099999997", status=PIDStatus.REGISTERED)
    db.session.commit()
    stranded = dict(agent_idref_data) | {
        "pid": "099999885",
        "relation_pid": {"type": "redirect_to", "value": "099999997"},
    }
    AgentIdrefRecord.create_or_update(data=stranded, dbcommit=True, reindex=True)
    AgentIdrefRecord.flush_indexes()

    assert Monitoring.get_dangling_redirects("aidref") == [
        ("099999882", "099999999"),
        ("099999885", "099999997"),
    ]

    res = CliRunner().invoke(dangling_redirects_cli, [], obj=script_info)
    assert res.exit_code == 0
    assert "099999882" in res.output
    assert "099999883" not in res.output
    assert "099999884" not in res.output

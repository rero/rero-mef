# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test finding and repairing stale `type_conflict` flags.

The flag is computed when a MEF record is indexed, from the type of the record its source redirects to. A load that
brings that target after the MEF record leaves the flag unset, and nothing reindexes the MEF record when the target
arrives, changes type or goes away.
"""

from click.testing import CliRunner

from rero_mef.agents import AgentGndRecord, AgentMefRecord
from rero_mef.cli import repair_type_conflicts as cli_repair_type_conflicts
from rero_mef.places import PlaceGndRecord
from rero_mef.stale import audit_type_conflicts
from rero_mef.tasks import repair_type_conflicts
from rero_mef.utils import get_timestamp

from ..utils import create_record


def _place(pid, name):
    """A GND place, the target of a cross-type redirect."""
    return {
        "$schema": "https://mef.rero.ch/schemas/places_gnd/gnd-place-v0.0.1.json",
        "pid": pid,
        "type": "bf:Place",
        "authorized_access_point": name,
    }


def _flagged():
    return sorted(hit.pid for hit in AgentMefRecord.search().filter("term", type_conflict=True).source(["pid"]).scan())


def test_the_flag_follows_the_redirect_target(
    app, agent_gnd_crosstype_redirect_2_data, agent_mef_crosstype_redirect_2_data
):
    """A target loaded after the MEF record raises the flag, its deletion clears it."""
    create_record(AgentGndRecord, agent_gnd_crosstype_redirect_2_data)
    mef_record = create_record(AgentMefRecord, agent_mef_crosstype_redirect_2_data)
    # the target is not loaded yet, which is no conflict
    assert _flagged() == []
    assert audit_type_conflicts("mef") == []

    place = create_record(PlaceGndRecord, _place("040425134", "Norden (Landkreis Aurich)"))
    # nothing reindexed the MEF record: its flag is stale
    assert _flagged() == []
    assert audit_type_conflicts("mef") == [(mef_record.pid, False, True)]

    # a dry run only reports
    assert repair_type_conflicts(dry_run=True) == {"mef": 1, "comef": 0, "plmef": 0}
    assert _flagged() == []

    assert repair_type_conflicts() == {"mef": 1, "comef": 0, "plmef": 0}
    assert _flagged() == [mef_record.pid]
    assert audit_type_conflicts("mef") == []

    # without its target, the redirect is no conflict anymore
    place.delete(dbcommit=True, delindex=True)
    PlaceGndRecord.flush_indexes()
    assert audit_type_conflicts("mef") == [(mef_record.pid, True, False)]
    assert repair_type_conflicts() == {"mef": 1, "comef": 0, "plmef": 0}
    assert _flagged() == []
    assert repair_type_conflicts() == {"mef": 0, "comef": 0, "plmef": 0}


def test_the_cli_repairs_after_a_load(
    app, script_info, agent_gnd_crosstype_redirect_3_data, agent_mef_crosstype_redirect_3_data
):
    """The setup runs the repair once its fixtures are loaded, and the run is stamped for the monitoring."""
    create_record(AgentGndRecord, agent_gnd_crosstype_redirect_3_data)
    mef_record = create_record(AgentMefRecord, agent_mef_crosstype_redirect_3_data)
    create_record(PlaceGndRecord, _place("1334736340", "Theaterbau des Théâtre des Champs-Élysées (Paris)"))

    runner = CliRunner()
    res = runner.invoke(cli_repair_type_conflicts, ["--dry-run"], obj=script_info)
    assert res.output.splitlines() == ["mef: 1 stale (dry run)", "comef: 0 stale (dry run)", "plmef: 0 stale (dry run)"]
    assert mef_record.pid not in _flagged()

    res = runner.invoke(cli_repair_type_conflicts, [], obj=script_info)
    assert res.output.splitlines() == ["mef: 1 stale", "comef: 0 stale", "plmef: 0 stale"]
    assert mef_record.pid in _flagged()

    stamp = get_timestamp("repair_type_conflicts")
    assert stamp["dry_run"] is False
    assert stamp["found"] == {"mef": 1, "comef": 0, "plmef": 0}
    assert stamp["repaired"] == {"mef": 1, "comef": 0, "plmef": 0}
    assert stamp["time"]

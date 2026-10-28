# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test places linking through the GND number."""

from copy import deepcopy
from unittest import mock

from rero_mef.api import Action
from rero_mef.places import PlaceGndRecord, PlaceIdrefRecord, PlaceMefRecord
from rero_mef.utils import build_ref_string


def _idref_place(place_idref_data, pid, gnd_pid):
    """Build an IdRef place stating a GND number."""
    data = deepcopy(place_idref_data)
    data["pid"] = pid
    data["identifiedBy"].append({"source": "GND", "type": "bf:Nbn", "value": f"(DE-101){gnd_pid}"})
    return data


def test_deleted_idref_place_does_not_take_the_gnd_place(app, place_idref_data, place_gnd_data):
    """A deleted IdRef place keeps stating a GND number a live one also states, and must leave it alone.

    This is IdRef 02750381X, deleted, stating GND 040482634 that IdRef 260199737 also states: each time the
    deleted record was processed, it took the GND place out of the MEF record of the live one.
    """
    gnd_data = deepcopy(place_gnd_data)
    gnd_data["pid"] = "040482634"
    gnd_record, _ = PlaceGndRecord.create_or_update(data=gnd_data, dbcommit=True, reindex=True)
    live_record, _ = PlaceIdrefRecord.create_or_update(
        data=_idref_place(place_idref_data, "260199737", gnd_record.pid), dbcommit=True, reindex=True
    )
    # Both IdRef places live: the GND number is ambiguous, so the second one gets a MEF record of its own.
    other_data = _idref_place(place_idref_data, "02750381X", gnd_record.pid)
    other_record, _ = PlaceIdrefRecord.create_or_update(data=other_data, dbcommit=True, reindex=True)
    PlaceGndRecord.flush_indexes()
    PlaceIdrefRecord.flush_indexes()
    other_mef, _ = other_record.create_or_update_mef(dbcommit=True, reindex=True)
    PlaceMefRecord.flush_indexes()
    assert other_mef.ref_pids == {"idref": other_record.pid}

    # A later harvest deletes it, which leaves the live one alone with the number.
    deleted_record, _ = PlaceIdrefRecord.create_or_update(
        data=other_data | {"deleted": "2026-07-27T07:02:39.299680+00:00"}, dbcommit=True, reindex=True
    )
    PlaceIdrefRecord.flush_indexes()
    live_mef, _ = live_record.create_or_update_mef(dbcommit=True, reindex=True)
    PlaceMefRecord.flush_indexes()
    assert live_mef.ref_pids == {"idref": live_record.pid, "gnd": gnd_record.pid}

    assert deleted_record.association_info["record"] is None
    deleted_mef, _ = deleted_record.create_or_update_mef(dbcommit=True, reindex=True)
    PlaceMefRecord.flush_indexes()

    assert deleted_mef.pid == other_mef.pid
    assert deleted_mef.ref_pids == {"idref": deleted_record.pid}
    assert [mef.pid for mef in PlaceMefRecord.get_mef(gnd_record.pid, "gnd")] == [live_mef.pid]


def test_latest_keeps_a_redirect_to_a_pid_no_place_holds(app, place_gnd_redirect_data):
    """A redirect to a pid no place record holds resolves to the record's own MEF record."""
    # live first, then deleted and redirected
    live_data = {k: v for k, v in deepcopy(place_gnd_redirect_data).items() if k not in ("deleted", "relation_pid")}
    PlaceGndRecord.create_or_update(data=live_data, dbcommit=True, reindex=True)
    gnd_record, _ = PlaceGndRecord.create_or_update(data=deepcopy(place_gnd_redirect_data), dbcommit=True, reindex=True)
    ref = build_ref_string(entity_type="places", entity_name="gnd", entity_pid=gnd_record.pid)
    mef = PlaceMefRecord.create(data={"gnd": {"$ref": ref}, "type": "bf:Place"}, dbcommit=True, reindex=True)
    PlaceMefRecord.flush_indexes()

    # the redirect target is held by no place record
    assert not PlaceMefRecord.get_mef(gnd_record["relation_pid"]["value"], "gnd")
    with mock.patch.object(app.logger, "warning") as warning:
        assert PlaceMefRecord.get_latest(pid_type="gnd", pid=gnd_record.pid)["pid"] == mef.pid
    warning.assert_called_once_with(
        f"REDIRECT OUT OF TYPE: PlaceMefRecord gnd {gnd_record.pid} -> 1332364101 | mef: {mef.pid}"
    )


def test_a_partner_held_elsewhere_gets_no_new_mef_record(app, place_idref_data, place_gnd_data):
    """A partner another MEF record already holds gets no new MEF record."""
    gnd_data = deepcopy(place_gnd_data)
    gnd_data["pid"] = "040657418"
    gnd_record, _ = PlaceGndRecord.create_or_update(data=gnd_data, dbcommit=True, reindex=True)
    live_data = _idref_place(place_idref_data, "191035726", gnd_record.pid)
    live_record, _ = PlaceIdrefRecord.create_or_update(data=live_data, dbcommit=True, reindex=True)
    other_data = _idref_place(place_idref_data, "027482928", gnd_record.pid)
    PlaceIdrefRecord.create_or_update(data=other_data, dbcommit=True, reindex=True)
    deleted_record, _ = PlaceIdrefRecord.create_or_update(
        data=other_data | {"deleted": "2026-07-27T07:02:52.843524+00:00"}, dbcommit=True, reindex=True
    )
    PlaceGndRecord.flush_indexes()
    PlaceIdrefRecord.flush_indexes()

    # the GND place in the MEF record of the deleted IdRef place and in that of the live one
    def ref(name, pid):
        return {"$ref": build_ref_string(entity_type="places", entity_name=name, entity_pid=pid)}

    stale_mef = PlaceMefRecord.create(
        data={"idref": ref("idref", deleted_record.pid), "gnd": ref("gnd", gnd_record.pid), "type": "bf:Place"},
        dbcommit=True,
        reindex=True,
    )
    live_mef = PlaceMefRecord.create(
        data={"idref": ref("idref", live_record.pid), "gnd": ref("gnd", gnd_record.pid), "type": "bf:Place"},
        dbcommit=True,
        reindex=True,
    )
    PlaceMefRecord.flush_indexes()
    mef_count = PlaceMefRecord.count()

    deleted_record.create_or_update_mef(dbcommit=True, reindex=True)
    PlaceMefRecord.flush_indexes()

    assert PlaceMefRecord.count() == mef_count
    assert [mef.pid for mef in PlaceMefRecord.get_mef(gnd_record.pid, "gnd")] == [live_mef.pid]
    assert PlaceMefRecord.get_record_by_pid(stale_mef.pid).ref_pids == {"idref": deleted_record.pid}


def test_deleted_redirected_gnd_place_gets_its_own_mef_record(app, place_idref_data, place_gnd_data):
    """A GND place deleted with a redirect moves to its own MEF record; its partner's record stays live."""
    target, _ = PlaceGndRecord.create_or_update(
        data=deepcopy(place_gnd_data) | {"pid": "7000002"}, dbcommit=True, reindex=True
    )
    old_data = deepcopy(place_gnd_data) | {"pid": "7000001"}
    old, _ = PlaceGndRecord.create_or_update(data=old_data, dbcommit=True, reindex=True)
    idref, _ = PlaceIdrefRecord.create_or_update(
        data=_idref_place(place_idref_data, "7000003", old.pid), dbcommit=True, reindex=True
    )
    PlaceGndRecord.flush_indexes()
    PlaceIdrefRecord.flush_indexes()
    target_mef, _ = target.create_or_update_mef(dbcommit=True, reindex=True)
    shared_mef, _ = idref.create_or_update_mef(dbcommit=True, reindex=True)
    assert shared_mef.ref_pids == {"idref": idref.pid, "gnd": old.pid}

    # deleted and redirected
    old, _ = PlaceGndRecord.create_or_update(
        data=old_data
        | {"deleted": "2026-10-20T00:00:00+00:00", "relation_pid": {"type": "redirect_to", "value": target.pid}},
        dbcommit=True,
        reindex=True,
    )
    own_mef, actions = old.create_or_update_mef(dbcommit=True, reindex=True)
    PlaceMefRecord.flush_indexes()

    shared_mef = PlaceMefRecord.get_record_by_pid(shared_mef.pid)
    assert shared_mef.ref_pids == {"idref": idref.pid}
    assert not shared_mef.get("deleted")
    assert own_mef.pid != shared_mef.pid
    assert own_mef.ref_pids == {"gnd": old.pid}
    assert own_mef.get("deleted")
    assert [mef.pid for mef in PlaceMefRecord.get_mef(old.pid, "gnd")] == [own_mef.pid]
    assert PlaceMefRecord.get_latest(pid_type="gnd", pid=old.pid)["pid"] == target_mef.pid

    again, actions = old.create_or_update_mef(dbcommit=True, reindex=True)
    assert again.pid == own_mef.pid
    assert actions == {own_mef.pid: Action.REPLACE}

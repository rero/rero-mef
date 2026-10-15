# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test places linking through the GND number."""

from copy import deepcopy

from rero_mef.places import PlaceGndRecord, PlaceIdrefRecord, PlaceMefRecord


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

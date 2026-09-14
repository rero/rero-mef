# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test finding and repairing links the rules no longer support.

A harvest reprocesses the record that changed, never the records that depended
on it. When a second GND record starts claiming a BNF number the two concepts
already linked on, the newcomer is told there is no winner while the stored
pair is never looked at again, and the link survives a rule that refuses it.
"""

import json
from copy import deepcopy

from rero_mef.concepts import ConceptGndRecord, ConceptIdrefRecord, ConceptMefRecord
from rero_mef.stale import _expected_partner, audit, repair
from rero_mef.tasks import repair_stale_associations
from rero_mef.utils import build_ref_string, get_timestamp


def test_expected_partner_follows_the_rules():
    """The audit decides with the rules themselves, not a copy of them."""
    own = {"FRBNF1": [("i1", None)]}
    other = {"FRBNF1": [("g1", "closeMatch")]}
    assert _expected_partner(ConceptIdrefRecord, "i1", ["FRBNF1"], own, other) == "g1"

    # a second claimant on the other side and no exact match leaves no winner
    contested = {"FRBNF1": [("g1", "closeMatch"), ("g2", "closeMatch")]}
    assert _expected_partner(ConceptIdrefRecord, "i1", ["FRBNF1"], own, contested) is None

    # ...unless exactly one of them asserts the equivalence
    settled = {"FRBNF1": [("g1", "closeMatch"), ("g2", "exactMatch")]}
    assert _expected_partner(ConceptIdrefRecord, "i1", ["FRBNF1"], own, settled) == "g2"

    # a record sharing its identifier with another on its own side gets nothing
    shared = {"FRBNF1": [("i1", None), ("i2", None)]}
    assert _expected_partner(ConceptIdrefRecord, "i1", ["FRBNF1"], shared, other) is None

    assert _expected_partner(ConceptIdrefRecord, "i1", [], own, other) is None


def test_a_second_claimant_makes_a_stored_link_stale(app, concept_idref_link_data, concept_gnd_link_data):
    """A GND record claiming an already used number leaves the stored link unsupported."""
    idref_record, _ = ConceptIdrefRecord.create_or_update(data=concept_idref_link_data, dbcommit=True, reindex=True)
    gnd_record, _ = ConceptGndRecord.create_or_update(data=concept_gnd_link_data, dbcommit=True, reindex=True)
    ConceptIdrefRecord.flush_indexes()
    ConceptGndRecord.flush_indexes()
    mef_record, _ = idref_record.create_or_update_mef(dbcommit=True, reindex=True)
    ConceptMefRecord.flush_indexes()
    assert mef_record.ref_pids.get("gnd") == gnd_record.pid
    assert audit("cidref", "cognd", "comef") == []

    # A second GND concept starts claiming the same number, as `Holzwerkstoff` did to `Holz`.
    rival_data = deepcopy(concept_gnd_link_data)
    rival_data["pid"] = f"{gnd_record.pid}999"
    rival_data["authorized_access_point"] = "Rival claiming the same BNF number"
    ConceptGndRecord.create_or_update(data=rival_data, dbcommit=True, reindex=True)
    ConceptGndRecord.flush_indexes()

    # Nothing reprocessed the stored pair, so the MEF record still holds the link.
    assert ConceptMefRecord.get_record_by_pid(mef_record.pid).ref_pids.get("gnd") == gnd_record.pid

    # The audit reports it, naming the partner the rules would give now.
    divergent = audit("cidref", "cognd", "comef")
    assert [(pid, stored, expected) for pid, _, stored, expected in divergent] == [
        (idref_record.pid, gnd_record.pid, None)
    ]

    # Repairing splits the pair: the IdRef concept keeps its MEF record without a GND reference.
    assert repair("cidref", divergent) == 1
    ConceptMefRecord.flush_indexes()
    assert ConceptMefRecord.get_record_by_pid(mef_record.pid).ref_pids.get("gnd") is None
    assert audit("cidref", "cognd", "comef") == []


def _renumbered(data, pid_suffix, number="99999999"):
    """Copy a fixture onto a BNF number and a pid of its own.

    The records of one test then form a cluster no other test claims a number in.
    """
    renumbered = json.loads(json.dumps(data).replace("12468269", number))
    renumbered["pid"] = f"{data['pid']}{pid_suffix}"
    return renumbered


def test_a_duplicate_mef_record_is_repaired_once(app, concept_idref_link_data, concept_gnd_link_data):
    """A concept in two MEF records is repaired to one, and the next run has nothing left to do."""
    idref_record, _ = ConceptIdrefRecord.create_or_update(
        data=_renumbered(concept_idref_link_data, "111"), dbcommit=True, reindex=True
    )
    gnd_record, _ = ConceptGndRecord.create_or_update(
        data=_renumbered(concept_gnd_link_data, "111"), dbcommit=True, reindex=True
    )
    rival_record, _ = ConceptGndRecord.create_or_update(
        data=_renumbered(concept_gnd_link_data, "222"), dbcommit=True, reindex=True
    )
    ConceptIdrefRecord.flush_indexes()
    ConceptGndRecord.flush_indexes()

    # Both GND concepts claim the number of the IdRef one, each in a MEF record of its own.
    for gnd_pid in (gnd_record.pid, rival_record.pid):
        ConceptMefRecord.create(
            data={
                "type": "bf:Topic",
                "idref": {
                    "$ref": build_ref_string(entity_type="concepts", entity_name="idref", entity_pid=idref_record.pid)
                },
                "gnd": {"$ref": build_ref_string(entity_type="concepts", entity_name="gnd", entity_pid=gnd_pid)},
            },
            dbcommit=True,
            reindex=True,
        )
    ConceptMefRecord.flush_indexes()
    stored = ConceptMefRecord.count()

    # Both pairs are reported, not just the one an index keyed by the IdRef pid would have kept.
    divergent = audit("cidref", "cognd", "comef")
    assert [(pid, expected) for pid, _, _, expected in divergent] == [(idref_record.pid, None)]

    # The repair leaves the IdRef concept one MEF record and splits off the GND concept it was paired with.
    assert repair_stale_associations() == {"cidref": 1, "pidref": 0}
    ConceptMefRecord.flush_indexes()
    assert len(ConceptMefRecord.get_mef(entity_pid=idref_record.pid, entity_name="idref")) == 1
    assert len(ConceptMefRecord.get_mef(entity_pid=gnd_record.pid, entity_name="gnd")) == 1
    assert len(ConceptMefRecord.get_mef(entity_pid=rival_record.pid, entity_name="gnd")) == 1
    assert ConceptMefRecord.count() == stored + 1

    # It used to add one more MEF record on every run, because it never found a single one to update.
    assert audit("cidref", "cognd", "comef") == []
    assert repair_stale_associations() == {"cidref": 0, "pidref": 0}
    ConceptMefRecord.flush_indexes()
    assert ConceptMefRecord.count() == stored + 1


def test_a_link_the_rules_now_give_is_repaired(app, concept_idref_link_data, concept_gnd_link_data):
    """A MEF record holding no partner is repaired once the rules give it one."""
    idref_record, _ = ConceptIdrefRecord.create_or_update(
        data=_renumbered(concept_idref_link_data, "333", "99999998"), dbcommit=True, reindex=True
    )
    gnd_record, _ = ConceptGndRecord.create_or_update(
        data=_renumbered(concept_gnd_link_data, "333", "99999998"), dbcommit=True, reindex=True
    )
    ConceptIdrefRecord.flush_indexes()
    ConceptGndRecord.flush_indexes()

    # the MEF record as it stood before the GND concept stated that number
    ConceptMefRecord.create(
        data={
            "type": "bf:Topic",
            "idref": {
                "$ref": build_ref_string(entity_type="concepts", entity_name="idref", entity_pid=idref_record.pid)
            },
        },
        dbcommit=True,
        reindex=True,
    )
    ConceptMefRecord.flush_indexes()

    divergent = audit("cidref", "cognd", "comef")
    assert [(pid, stored, expected) for pid, _, stored, expected in divergent] == [
        (idref_record.pid, None, gnd_record.pid)
    ]

    assert repair_stale_associations() == {"cidref": 1, "pidref": 0}
    ConceptMefRecord.flush_indexes()
    mef_records = ConceptMefRecord.get_mef(entity_pid=idref_record.pid, entity_name="idref")
    assert len(mef_records) == 1
    assert mef_records[0].ref_pids.get("gnd") == gnd_record.pid
    assert audit("cidref", "cognd", "comef") == []


def test_the_task_stamps_what_it_did(app, concept_idref_link_data, concept_gnd_link_data):
    """The scheduled task records its counts so monitoring can read them."""
    ConceptIdrefRecord.create_or_update(data=concept_idref_link_data, dbcommit=True, reindex=True)
    ConceptGndRecord.create_or_update(data=concept_gnd_link_data, dbcommit=True, reindex=True)
    ConceptIdrefRecord.flush_indexes()
    ConceptGndRecord.flush_indexes()

    found = repair_stale_associations(dry_run=True)
    assert set(found) == {"cidref", "pidref"}

    stamp = get_timestamp("repair_stale_associations")
    assert stamp["dry_run"] is True
    assert stamp["found"] == found
    assert stamp["repaired"] == {"cidref": 0, "pidref": 0}
    assert stamp["time"]

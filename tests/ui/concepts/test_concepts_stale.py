# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test finding and repairing links the rules no longer support.

A harvest reprocesses the record that changed, never the records that depended
on it. When a second GND record starts claiming a BNF number the two concepts
already linked on, the newcomer is told there is no winner while the stored
pair is never looked at again, and the link survives a rule that refuses it.
"""

from copy import deepcopy

from rero_mef.concepts import ConceptGndRecord, ConceptIdrefRecord, ConceptMefRecord
from rero_mef.stale import _expected_partner, audit, repair
from rero_mef.tasks import repair_stale_associations
from rero_mef.utils import get_timestamp


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
